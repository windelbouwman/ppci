import logging
from ... import ir, irutils
from ...common import CompilerError
from ...binutils import debuginfo
from . import types, declarations, statements, expressions
from .types import BareType


class CCodeGenerator:
    """ Converts parsed C code to ir-code """
    logger = logging.getLogger('ccodegen')

    def __init__(self, context, debug_db):
        self.context = context
        self.debug_db = debug_db
        self.builder = None
        self.ir_var_map = {}
        self.constant_values = {}
        self.evaluating_constants = set()
        self.break_block_stack = []  # A stack of while or switch loops
        self.continue_block_stack = []  # A stack of for loops
        self.labeled_blocks = {}
        self.switch_options = None
        int_types = {2: ir.i16, 4: ir.i32, 8: ir.i64}
        uint_types = {2: ir.i16, 4: ir.u32, 8: ir.u64}
        int_size = self.context.arch_info.get_size('int')
        self.ir_type_map = {
            BareType.CHAR: (ir.i8, 1),
            BareType.SCHAR: (ir.i8, 1),
            BareType.UCHAR: (ir.u8, 1),
            BareType.SHORT: (ir.i16, 2),
            BareType.USHORT: (ir.u16, 2),
            BareType.INT: (int_types[int_size], int_size),
            BareType.UINT: (uint_types[int_size], int_size),
            BareType.LONG: (ir.i64, 8),
            BareType.ULONG: (ir.u64, 8),
            BareType.LONGLONG: (ir.i64, 8),
            BareType.ULONGLONG: (ir.u64, 8),
            BareType.FLOAT: (ir.f32, 4),
            BareType.DOUBLE: (ir.f64, 8),
        }

    def get_label_block(self, name):
        """ Get the ir block for a given label, and create it if necessary """
        if name in self.labeled_blocks:
            block = self.labeled_blocks[name]
        else:
            block = self.builder.new_block()
            self.labeled_blocks[name] = block  # TODO: use name
        return block

    def gen_code(self, compile_unit):
        """ Initial entry point for the code generator """
        self.builder = irutils.Builder()
        self.ir_var_map = {}
        self.logger.debug('Generating IR-code')
        ir_mod = ir.Module('main')
        self.builder.module = ir_mod
        for declaration in compile_unit.declarations:
            self.gen_object(declaration)
        self.logger.info('Finished IR-code generation')
        return ir_mod

    def gen_object(self, declaration):
        """ Generate code for a single object """
        assert isinstance(declaration, declarations.Declaration)

        # Generate code:
        if isinstance(declaration, declarations.Typedef):
            pass
            # self.type_scope.insert(declaration)
        elif isinstance(declaration, declarations.FunctionDeclaration):
            self.gen_function(declaration)
        elif isinstance(declaration, declarations.VariableDeclaration):
            self.gen_global_variable(declaration)
        elif isinstance(declaration, declarations.ValueDeclaration):
            pass
        else:  # pragma: no cover
            raise NotImplementedError()

    def emit(self, instruction):
        """ Helper function to emit a single instruction """
        # print(instruction)
        return self.builder.emit(instruction)

    def info(self, message, node):
        """ Generate information message at the given node """
        node.loc.print_message(message)

    def error(self, message, location):
        """ Trigger an error at the given node """
        raise CompilerError(message, loc=location)

    def gen_global_variable(self, var_decl):
        # if typ is array, use initializer to determine size
        if var_decl.initial_value:
            # TODO: determine initializer value
            pass
        size = self.context.sizeof(var_decl.typ)
        ir_var = ir.Variable(var_decl.name, size)
        self.builder.module.add_variable(ir_var)
        self.ir_var_map[var_decl] = ir_var

    def gen_function(self, function):
        """ Generate code for a function """
        if not function.body:
            return
        self.logger.debug('Generating IR-code for %s', function.name)
        assert not self.break_block_stack
        assert len(self.continue_block_stack) == 0
        self.labeled_blocks = {}
        assert not self.labeled_blocks
        self.unreachable = False

        # Save current function for later on..
        self.current_function = function

        if function.typ.return_type.is_void:
            ir_function = self.builder.new_procedure(function.name)
        else:
            return_type = self.get_ir_type(function.typ.return_type)
            ir_function = self.builder.new_function(function.name, return_type)

        # Create entry code:
        self.builder.set_function(ir_function)
        first_block = self.builder.new_block()
        self.builder.set_block(first_block)
        ir_function.entry = first_block

        # Add arguments (create memory space for them!):
        for argument in function.typ.arguments:
            ir_typ = self.get_ir_type(argument.typ)
            if argument.name is None:
                ir_argument = ir.Parameter('anonymous', ir_typ)
                ir_function.add_parameter(ir_argument)
            else:
                ir_argument = ir.Parameter(argument.name, ir_typ)
                ir_function.add_parameter(ir_argument)
                size = self.context.sizeof(argument.typ)
                ir_var = self.emit(ir.Alloc(argument.name + '_alloc', size))
                self.emit(ir.Store(ir_argument, ir_var))
                self.ir_var_map[argument] = ir_var

        # Generate debug info for function:
        dbg_args = [
            debuginfo.DebugParameter(a.name, self.get_debug_type(a.typ))
            for a in function.typ.arguments]
        dfi = debuginfo.DebugFunction(
            function.name, function.location,
            self.get_debug_type(function.typ.return_type),
            dbg_args)
        self.debug_db.enter(ir_function, dfi)

        # Generate code for body:
        assert isinstance(function.body, statements.Compound)
        self.gen_compound(function.body)

        if not self.builder.block.is_closed:
            # In case of void function, introduce exit instruction:
            if function.typ.return_type.is_void:
                self.emit(ir.Exit())
            else:
                if self.builder.block.is_empty:
                    last_block = self.builder.block
                    self.builder.set_block(None)
                    ir_function.delete_unreachable()
                    assert not last_block.is_used
                    assert last_block not in ir_function
                else:
                    self.error(
                        'Function does not return an {}'.format(
                            function.typ.return_type),
                        function)

        # TODO: maybe generate only code which is reachable?
        ir_function.delete_unreachable()
        self.builder.set_function(None)
        self.current_function = None
        assert len(self.break_block_stack) == 0
        assert len(self.continue_block_stack) == 0

    def gen_stmt(self, statement):
        fn_map = {
            statements.If: self.gen_if,
            statements.While: self.gen_while,
            statements.DoWhile: self.gen_do_while,
            statements.For: self.gen_for,
            statements.Switch: self.gen_switch,
            statements.Goto: self.gen_goto,
            statements.Break: self.gen_break,
            statements.Continue: self.gen_continue,
            statements.Return: self.gen_return,
            statements.Label: self.gen_label,
            statements.Case: self.gen_case,
            statements.Default: self.gen_default,
            statements.Empty: self.gen_empty_statement,
            statements.Compound: self.gen_compound,
            statements.ExpressionStatement: self.gen_expression_statement,
            statements.DeclarationStatement: self.gen_declaration_statement,
        }
        if type(statement) in fn_map:
            fn_map[type(statement)](statement)
        else:  # pragma: no cover
            raise NotImplementedError(str(statement))

    def gen_empty_statement(self, statement):
        """ Generate code for empty statement """
        pass

    def gen_compound(self, statement):
        """ Generate code for a compound statement """
        for inner_statement in statement.statements:
            self.gen_stmt(inner_statement)

    def gen_declaration_statement(self, statement):
        """ Generate code for a declaration statement """
        declaration = statement.declaration
        if isinstance(declaration, declarations.VariableDeclaration):
            self.gen_local_variable(declaration)
        else:
            raise NotImplementedError(str(declaration))

    def gen_expression_statement(self, statement):
        """ Generate code for an expression statement """
        self.gen_expr(statement.expression)
        # TODO: issue a warning when expression result is non void?

    def gen_if(self, stmt: statements.If):
        """ Generate if-statement code """
        final_block = self.builder.new_block()
        yes_block = self.builder.new_block()
        if stmt.no:
            no_block = self.builder.new_block()
        else:
            no_block = final_block
        self.gen_condition(stmt.condition, yes_block, no_block)
        self.builder.set_block(yes_block)
        self.gen_stmt(stmt.yes)
        self.emit(ir.Jump(final_block))
        if stmt.no:
            self.builder.set_block(no_block)
            self.gen_stmt(stmt.no)
            self.emit(ir.Jump(final_block))
        self.builder.set_block(final_block)

    def gen_switch(self, stmt: statements.Switch):
        """ Generate switch-case-statement code.
        See also:
            https://www.codeproject.com/Articles/100473/
            Something-You-May-Not-Know-About-the-Switch-Statem

        For now, implemented as a gigantic if-then forest.
        """
        backup = self.switch_options
        self.switch_options = {}
        test_block = self.builder.new_block()
        body_block = self.builder.new_block()
        final_block = self.builder.new_block()

        # First execute the test code:
        self.emit(ir.Jump(test_block))

        # Implement the switch body:
        self.break_block_stack.append(final_block)
        self.builder.set_block(body_block)
        self.gen_stmt(stmt.statement)
        self.emit(ir.Jump(final_block))
        self.break_block_stack.pop(-1)

        # Implement switching logic, now that we have the branches:
        # TODO: implement jump tables and other performance related stuff.
        self.builder.set_block(test_block)
        test_value = self.gen_expr(stmt.expression, rvalue=True)
        switch_ir_typ = self.get_ir_type(stmt.expression.typ)
        for option, target_block in self.switch_options.items():
            if option == 'default':
                pass
            else:
                option = self.emit(ir.Const(option, 'case', switch_ir_typ))
                next_test_block = self.builder.new_block()
                self.emit(ir.CJump(
                    test_value, '==', option, target_block, next_test_block))
                self.builder.set_block(next_test_block)

        # If all else fails, jump to the default case if we have it.
        if 'default' in self.switch_options:
            self.emit(ir.Jump(self.switch_options['default']))
        else:
            self.emit(ir.Jump(final_block))

        # Set continuation point:
        self.builder.set_block(final_block)

        # Restore state:
        self.switch_options = backup

    def gen_while(self, stmt: statements.While):
        """ Generate while statement code """
        condition_block = self.builder.new_block()
        body_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.break_block_stack.append(final_block)
        self.continue_block_stack.append(condition_block)
        self.emit(ir.Jump(condition_block))
        self.builder.set_block(condition_block)
        self.gen_condition(stmt.condition, body_block, final_block)
        self.builder.set_block(body_block)
        self.gen_stmt(stmt.body)
        self.emit(ir.Jump(condition_block))
        self.builder.set_block(final_block)
        self.break_block_stack.pop(-1)
        self.continue_block_stack.pop(-1)

    def gen_do_while(self, stmt: statements.DoWhile):
        """ Generate do-while-statement code """
        body_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.break_block_stack.append(final_block)
        self.continue_block_stack.append(body_block)
        self.emit(ir.Jump(body_block))
        self.builder.set_block(body_block)
        self.gen_stmt(stmt.body)
        self.gen_condition(stmt.condition, body_block, final_block)
        self.builder.set_block(final_block)
        self.break_block_stack.pop(-1)
        self.continue_block_stack.pop(-1)

    def gen_for(self, stmt: statements.For):
        """ Generate code for for-statement """
        condition_block = self.builder.new_block()
        body_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.break_block_stack.append(final_block)
        self.continue_block_stack.append(condition_block)
        if stmt.init:
            self.gen_expr(stmt.init)
        self.emit(ir.Jump(condition_block))
        self.builder.set_block(condition_block)
        if stmt.condition:
            self.gen_condition(stmt.condition, body_block, final_block)
        else:
            self.emit(ir.Jump(body_block))
        self.builder.set_block(body_block)
        self.gen_stmt(stmt.body)
        if stmt.post:
            self.gen_expr(stmt.post)
        self.emit(ir.Jump(condition_block))
        self.builder.set_block(final_block)
        self.break_block_stack.pop(-1)
        self.continue_block_stack.pop(-1)

    def gen_label(self, stmt: statements.Label):
        """ Generate code for a label """
        block = self.get_label_block(stmt.name)
        self.emit(ir.Jump(block))  # fall through
        self.builder.set_block(block)
        self.gen_stmt(stmt.statement)

    def gen_case(self, stmt: statements.Case):
        """ Generate code for case label inside a switch statement """
        block = self.builder.new_block()
        assert self.switch_options is not None
        if stmt.value in self.switch_options:
            self.error('Case defined multiple times', stmt.location)
        self.switch_options[stmt.value] = block
        self.emit(ir.Jump(block))  # fall through
        self.builder.set_block(block)
        self.gen_stmt(stmt.statement)

    def gen_default(self, stmt: statements.Default):
        """ Generate code for case label inside a switch statement """
        block = self.builder.new_block()
        assert self.switch_options is not None
        self.switch_options['default'] = block
        self.emit(ir.Jump(block))  # fall through
        self.builder.set_block(block)
        self.gen_stmt(stmt.statement)

    def gen_goto(self, stmt: statements.Goto):
        """ Generate code for a goto statement """
        block = self.get_label_block(stmt.label)
        self.emit(ir.Jump(block))
        new_block = self.builder.new_block()
        self.builder.set_block(new_block)
        self.unreachable = True

    def gen_continue(self, stmt: statements.Continue):
        """ Generate code for the continue statement """
        # block = self.get_label_block(stmt.label)
        if self.continue_block_stack:
            block = self.continue_block_stack[-1]
            self.emit(ir.Jump(block))
        else:
            self.error('Cannot continue here!', stmt)
        new_block = self.builder.new_block()
        self.builder.set_block(new_block)
        # TODO: unreachable code after here!
        self.unreachable = True

    def gen_break(self, stmt: statements.Break):
        """ Generate code to break out of something. """
        # block = self.get_label_block(stmt.label)
        if self.break_block_stack:
            block = self.break_block_stack[-1]
            self.emit(ir.Jump(block))
        else:
            self.error('Cannot break here!', stmt)
        new_block = self.builder.new_block()
        self.builder.set_block(new_block)
        self.unreachable = True

    def gen_return(self, stmt: statements.Return):
        """ Generate return statement code """
        if stmt.value:
            value = self.gen_expr(stmt.value, rvalue=True)
            self.emit(ir.Return(value))
        else:
            self.emit(ir.Exit())
        new_block = self.builder.new_block()
        self.builder.set_block(new_block)

    def gen_condition(self, condition, yes_block, no_block):
        """ Generate switch based on condition. """
        if isinstance(condition, expressions.Binop):
            if condition.op == '||':
                middle_block = self.builder.new_block()
                self.gen_condition(condition.a, yes_block, middle_block)
                self.builder.set_block(middle_block)
                self.gen_condition(condition.b, yes_block, no_block)
            elif condition.op == '&&':
                middle_block = self.builder.new_block()
                self.gen_condition(condition.a, middle_block, no_block)
                self.builder.set_block(middle_block)
                self.gen_condition(condition.b, yes_block, no_block)
            elif condition.op in ['<', '>', '==', '!=', '<=', '>=']:
                lhs = self.gen_expr(condition.a, rvalue=True)
                rhs = self.gen_expr(condition.b, rvalue=True)
                op_map = {
                    '>': '>', '<': '<',
                    '==': '==', '!=': '!=',
                    '<=': '<=', '>=': '>='
                }
                op = op_map[condition.op]
                self.emit(ir.CJump(lhs, op, rhs, yes_block, no_block))
            else:
                self.check_non_zero(condition, yes_block, no_block)
        elif isinstance(condition, expressions.Unop):
            if condition.op == '!':
                # Simply swap yes and no here!
                self.gen_condition(condition.a, no_block, yes_block)
            else:
                self.check_non_zero(condition, yes_block, no_block)
        else:
            self.check_non_zero(condition, yes_block, no_block)

    def check_non_zero(self, expr, yes_block, no_block):
        """ Check an expression for being non-zero """
        value = self.gen_expr(expr, rvalue=True)
        ir_typ = self.get_ir_type(expr.typ)
        zero = self.emit(ir.Const(0, 'zero', ir_typ))
        self.emit(ir.CJump(value, '==', zero, no_block, yes_block))

    def gen_local_variable(self, variable: declarations.VariableDeclaration):
        """ Generate a local variable """
        name = variable.name
        size = self.context.sizeof(variable.typ)
        ir_addr = self.emit(ir.Alloc(name + '_alloc', size))
        self.ir_var_map[variable] = ir_addr

    def get_const_value(self, constant):
        """ Retrieve the calculated value for the given constant """
        if constant in self.constant_values:
            value = self.constant_values[constant]
        else:
            # Evaluate the constant now!
            if constant in self.evaluating_constants:
                self.error('Circular constant evaluation')
            self.evaluating_constants.add(constant)
            value = self.gen_expr(constant.value, purpose=self.CONST_EVAL)
            self.constant_values[constant] = value
            self.evaluating_constants.remove(constant)
        return value

    def gen_condition_to_integer(self, expr):
        """ Generate code that takes a boolean and convert it to integer """
        yes_block = self.builder.new_block()
        no_block = self.builder.new_block()
        end_block = self.builder.new_block()

        self.gen_condition(expr, yes_block, no_block)

        self.builder.set_block(yes_block)
        ir_typ = self.get_ir_type(expr.typ)
        yes_value = self.emit(ir.Const(1, 'one', ir_typ))
        self.emit(ir.Jump(end_block))

        self.builder.set_block(no_block)
        no_value = self.emit(ir.Const(0, 'zero', ir_typ))
        self.emit(ir.Jump(end_block))

        self.builder.set_block(end_block)
        value = self.emit(ir.Phi('phi', ir_typ))
        value.set_incoming(yes_block, yes_value)
        value.set_incoming(no_block, no_value)
        return value

    def gen_expr(self, expr, rvalue=False):
        """ Generate code for an expression.

        rvalue: if True, then the result of the expression will be an rvalue.
        """
        assert isinstance(expr, expressions.Expression)

        if isinstance(expr, expressions.Unop):
            if expr.op in ['x++', 'x--', '--x', '++x']:
                # Increment and decrement in pre and post form
                ir_a = self.gen_expr(expr.a, rvalue=False)
                assert expr.a.lvalue

                ir_typ = self.get_ir_type(expr.typ)
                loaded = self.emit(ir.Load(ir_a, 'loaded', ir_typ))
                # for pointers, this is not one, but sizeof
                if isinstance(expr.typ, types.PointerType):
                    size = self.context.sizeof(expr.typ.element_type)
                    one = self.emit(ir.Const(size, 'one_element', ir_typ))
                else:
                    one = self.emit(ir.Const(1, 'one', ir_typ))

                # Determine increment or decrement:
                op = expr.op[1]
                changed = self.emit(ir.Binop(
                    loaded, op, one, 'inc', ir_typ))
                self.emit(ir.Store(changed, ir_a))

                # Determine pre or post form:
                pre = expr.op[0] == 'x'
                if pre:
                    value = loaded
                else:
                    value = changed
            elif expr.op == '*':
                value = self.gen_expr(expr.a, rvalue=True)
            elif expr.op == '&':
                assert expr.a.lvalue
                value = self.gen_expr(expr.a, rvalue=False)
            elif expr.op == '-':
                a = self.gen_expr(expr.a, rvalue=True)
                ir_typ = self.get_ir_type(expr.typ)
                zero = self.emit(ir.Const(0, 'zero', ir_typ))
                value = self.emit(ir.Binop(zero, '-', a, 'neg', ir_typ))
            elif expr.op == '~':
                a = self.gen_expr(expr.a, rvalue=True)
                ir_typ = self.get_ir_type(expr.typ)
                # TODO: use 0xff for all bits!
                mx = self.emit(ir.Const(0xff, 'ffff', ir_typ))
                value = self.emit(ir.Binop(a, '^', mx, 'xor', ir_typ))
            elif expr.op in ['!']:
                value = self.gen_condition_to_integer(expr)
            else:  # pragma: no cover
                raise NotImplementedError(str(expr.op))
        elif isinstance(expr, expressions.Binop):
            if expr.op in ['-', '*', '/', '%', '^', '|', '&', '>>', '<<']:
                lhs = self.gen_expr(expr.a, rvalue=True)
                rhs = self.gen_expr(expr.b, rvalue=True)
                op = expr.op

                ir_typ = self.get_ir_type(expr.typ)
                value = self.emit(ir.Binop(lhs, op, rhs, 'op', ir_typ))
            elif expr.op == ',':
                # Handle the comma operator by returning the second result
                lhs = self.gen_expr(expr.a, rvalue=True)
                rhs = self.gen_expr(expr.b, rvalue=True)
                value = rhs
            elif expr.op in ['+']:
                lhs = self.gen_expr(expr.a, rvalue=True)
                rhs = self.gen_expr(expr.b, rvalue=True)
                # Handle pointer arithmatic!
                # Pointer arithmatic is an old artifact from the days
                # when an integer refered always to a array cell!
                if isinstance(expr.a.typ, types.IndexableType):
                    # TODO: assert is_integer(expr.b.typ)
                    esize = self.emit(
                        ir.Const(
                            self.context.sizeof(expr.a.typ.element_type),
                            'esize', rhs.ty))
                    rhs = self.emit(ir.mul(rhs, esize, 'rhs', rhs.ty))
                    rhs = self.emit(ir.Cast(rhs, 'ptr_arith', ir.ptr))
                elif isinstance(expr.b.typ, types.IndexableType):
                    # TODO: assert is_integer(expr.a.typ)
                    esize = self.emit(
                        ir.Const(
                            self.context.sizeof(expr.b.typ.element_type),
                            'esize', lhs.ty))
                    lhs = self.emit(ir.mul(lhs, esize, 'lhs', lhs.ty))
                    lhs = self.emit(ir.Cast(lhs, 'ptr_arith', ir.ptr))
                else:
                    pass

                op = expr.op

                ir_typ = self.get_ir_type(expr.typ)
                value = self.emit(ir.Binop(lhs, op, rhs, 'op', ir_typ))
            elif expr.op in ['<', '>', '==', '!=', '<=', '>=', '||', '&&']:
                value = self.gen_condition_to_integer(expr)
            elif expr.op in [
                    '=', '+=', '-=', '*=', '%=', '/=',
                    '>>=', '<<=',
                    '&=', '|=', '~=', '^=']:
                lhs = self.gen_expr(expr.a, rvalue=False)
                rhs = self.gen_expr(expr.b, rvalue=True)

                # Handle '+=' and friends:
                if expr.op != '=':
                    op = expr.op[:-1]
                    ir_typ = self.get_ir_type(expr.typ)
                    loaded = self.emit(ir.Load(lhs, 'lhs', ir_typ))
                    value = self.emit(ir.Binop(
                        loaded, op, rhs, 'assign', ir_typ))
                else:
                    value = rhs
                self.emit(ir.Store(value, lhs))
            else:  # pragma: no cover
                raise NotImplementedError(str(expr.op))
        elif isinstance(expr, expressions.Ternop):
            if expr.op in ['?']:
                # TODO: merge maybe with conditional logic?
                yes_block = self.builder.new_block()
                no_block = self.builder.new_block()
                end_block = self.builder.new_block()

                self.gen_condition(expr.a, yes_block, no_block)

                # The true path:
                self.builder.set_block(yes_block)
                yes_value = self.gen_expr(expr.b, rvalue=True)
                # Fetch current block, because it might have changed!
                final_yes_block = self.builder.block
                self.emit(ir.Jump(end_block))

                # The false path:
                self.builder.set_block(no_block)
                no_value = self.gen_expr(expr.c, rvalue=True)
                final_no_block = self.builder.block
                self.emit(ir.Jump(end_block))

                self.builder.set_block(end_block)
                ir_typ = self.get_ir_type(expr.typ)
                value = self.emit(ir.Phi('phi', ir_typ))
                value.set_incoming(final_yes_block, yes_value)
                value.set_incoming(final_no_block, no_value)
            else:  # pragma: no cover
                raise NotImplementedError(str(expr.op))
        elif isinstance(expr, expressions.VariableAccess):
            variable = expr.variable
            if isinstance(
                    variable,
                    (declarations.VariableDeclaration,
                     declarations.ParameterDeclaration,
                     declarations.ConstantDeclaration)):
                value = self.ir_var_map[variable]
            elif isinstance(variable, declarations.ValueDeclaration):
                # Enum value declaration!
                constant_value = variable.value
                ir_typ = self.get_ir_type(expr.typ)
                value = self.emit(ir.Const(
                    constant_value, variable.name, ir_typ))
            else:  # pragma: no cover
                raise NotImplementedError()
        elif isinstance(expr, expressions.FunctionCall):
            # Evaluate arguments:
            ir_arguments = []
            for argument in expr.args:
                value = self.gen_expr(argument, rvalue=True)
                ir_arguments.append(value)
            function = expr.function
            if function.typ.return_type.is_void:
                self.emit(ir.ProcedureCall(function.name, ir_arguments))
                value = None
            else:
                ir_typ = self.get_ir_type(expr.typ)
                value = self.emit(ir.FunctionCall(
                    function.name, ir_arguments, 'result', ir_typ))
        elif isinstance(expr, expressions.StringLiteral):
            # Construct nifty 0-terminated string into memory!
            encoding = 'latin1'
            data = expr.value[1:-1].encode(encoding) + bytes([0])
            value = self.emit(ir.LiteralData(data, 'cstr'))
        elif isinstance(expr, expressions.CharLiteral):
            ir_typ = self.get_ir_type(expr.typ)
            value = self.emit(ir.Const(expr.value, 'constant', ir_typ))
        elif isinstance(expr, expressions.NumericLiteral):
            ir_typ = self.get_ir_type(expr.typ)
            value = self.emit(ir.Const(expr.value, 'constant', ir_typ))
        elif isinstance(expr, expressions.InitializerList):
            expr.lvalue = True
            self.error('Illegal initializer list', expr.location)
        elif isinstance(expr, expressions.Cast):
            a = self.gen_expr(expr.expr, rvalue=True)
            ir_typ = self.get_ir_type(expr.to_typ)
            value = self.emit(ir.Cast(a, 'typecast', ir_typ))
        elif isinstance(expr, expressions.Sizeof):
            if isinstance(expr.sizeof_typ, types.CType):
                # Get size of the given type:
                type_size = self.context.sizeof(expr.sizeof_typ)
            else:
                # And get its size:
                type_size = self.context.sizeof(expr.sizeof_typ.typ)

            ir_typ = self.get_ir_type(expr.typ)
            value = self.emit(ir.Const(type_size, 'type_size', ir_typ))
        elif isinstance(expr, expressions.FieldSelect):
            base = self.gen_expr(expr.base, rvalue=False)
            offset = expr.field.offset
            offset = self.emit(ir.Const(offset, 'offset', ir.ptr))
            value = self.emit(
                ir.Binop(base, '+', offset, 'offset', ir.ptr))
        elif isinstance(expr, expressions.ArrayIndex):
            base = self.gen_expr(expr.base, rvalue=False)
            index = self.gen_expr(expr.index, rvalue=True)

            # Generate constant for element size:
            element_type_size = self.context.sizeof(
                expr.base.typ.element_type)
            element_size = self.emit(
                ir.Const(element_type_size, 'element_size', ir.ptr))

            # Calculate offset:
            index = self.emit(ir.Cast(index, 'index', ir.ptr))
            offset = self.emit(
                ir.mul(index, element_size, "element_offset", ir.ptr))

            # Calculate address:
            value = self.emit(
                ir.add(base, offset, "element_address", ir.ptr))
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))

        # Check for given attributes:
        assert isinstance(expr.typ, types.CType)
        assert isinstance(expr.lvalue, bool)

        # If we need an rvalue, load it!
        if rvalue and expr.lvalue:
            ir_typ = self.get_ir_type(expr.typ)
            value = self.emit(ir.Load(value, 'load', ir_typ))
        return value

    def get_ir_type(self, typ: types.CType):
        """ Given a C type, get the fitting ir type """
        assert isinstance(typ, types.CType)

        if isinstance(typ, types.BareType):
            return self.ir_type_map[typ.type_id][0]
        elif isinstance(typ, types.IndexableType):
            # Pointers and arrays are seen as pointers:
            return ir.ptr
        elif isinstance(typ, types.EnumType):
            return self.get_ir_type(self.context.get_type(['int']))
        elif isinstance(typ, types.UnionType):
            size = self.context.sizeof(typ)
            return ir.BlobDataTyp.get(size)
        elif isinstance(typ, types.StructType):
            size = self.context.sizeof(typ)
            return ir.BlobDataTyp.get(size)
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))

    def get_debug_type(self, typ: types.CType):
        """ Get or create debug type info in the debug information """
        # Find cached values:
        if self.debug_db.contains(typ):
            return self.debug_db.get(typ)

        if isinstance(typ, types.BareType):
            if typ.is_void:
                dbg_typ = debuginfo.DebugBaseType(
                    typ.type_id, 0, 1)
            else:
                dbg_typ = debuginfo.DebugBaseType(
                    typ.type_id, self.context.sizeof(typ), 1)
            self.debug_db.enter(typ, dbg_typ)
        elif isinstance(typ, types.PointerType):
            ptype = self.get_debug_type(typ.element_type)
            dbg_typ = debuginfo.DebugPointerType(ptype)
            self.debug_db.enter(typ, dbg_typ)
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))
        return dbg_typ
