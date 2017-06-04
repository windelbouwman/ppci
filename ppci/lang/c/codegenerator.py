import logging
from ... import ir, irutils
from ...common import CompilerError
from . import nodes
from .scope import Scope


class CCodeGenerator:
    """ Converts parsed C code to ir-code """
    logger = logging.getLogger('ccodegen')

    def __init__(self, context):
        self.context = context
        self.builder = None
        self.scope = None
        self.ir_var_map = {}
        self.constant_values = {}
        self.evaluating_constants = set()
        self.break_block_stack = []  # A stack of while or switch loops
        self.continue_block_stack = []  # A stack of for loops
        self.labeled_blocks = {}
        self.switch_options = None
        int_types = {2: ir.i16, 4: ir.i32, 8: ir.i64}
        uint_types = {2: ir.i16, 4: ir.u32, 8: ir.u64}
        int_size = self.context.march.byte_sizes['int']
        self.ir_type_map = {
            nodes.BareType.CHAR: (ir.i8, 1),
            nodes.BareType.SCHAR: (ir.i8, 1),
            nodes.BareType.UCHAR: (ir.u8, 1),
            nodes.BareType.SHORT: (ir.i16, 2),
            nodes.BareType.USHORT: (ir.u16, 2),
            nodes.BareType.INT: (int_types[int_size], int_size),
            nodes.BareType.UINT: (uint_types[int_size], int_size),
            nodes.BareType.LONG: (ir.i64, 8),
            nodes.BareType.ULONG: (ir.u64, 8),
            nodes.BareType.FLOAT: (ir.f32, 4),
            nodes.BareType.DOUBLE: (ir.f64, 8),
        }
        # Define the type for a string:
        self.cstr_type = nodes.PointerType(self.get_type(['char']))

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
        self.type_scope = Scope()
        self.scope = compile_unit.scope
        self.ir_var_map = {}
        self.logger.debug('Generating IR-code')
        ir_mod = ir.Module('c_compilation_unit')
        self.builder.module = ir_mod
        for declaration in compile_unit.declarations:
            assert isinstance(declaration, nodes.Declaration)
            # Insert into the current scope:
            if self.scope.is_defined(declaration.name):
                sym = self.scope.get(declaration.name)
                # The symbol might be a forward declaration:
                if self.equal_types(sym.typ, declaration.typ) and \
                        declaration.is_function:
                    self.logger.debug('okay, forward declaration implemented')
                else:
                    self.info('First defined here', sym)
                    self.error("Invalid redefinition", declaration)
            else:
                self.scope.insert(declaration)

            if isinstance(declaration.typ, nodes.StructOrUnionType):
                struct_typ = declaration.typ
                if struct_typ.tag:
                    self.logger.debug(
                        'Registering struct tag %s', struct_typ.tag)
                    self.scope.struct_tags[struct_typ.tag] = struct_typ

            # Generate code:
            if isinstance(declaration, nodes.Typedef):
                self.type_scope.insert(declaration)
            elif isinstance(declaration, nodes.FunctionDeclaration):
                self.gen_function(declaration)
            elif isinstance(declaration, nodes.VariableDeclaration):
                self.gen_global_variable(declaration)
            else:  # pragma: no cover
                raise NotImplementedError()
        self.logger.info('Finished IR-code generation')
        return ir_mod

    def emit(self, instruction):
        """ Helper function to emit a single instruction """
        # print(instruction)
        return self.builder.emit(instruction)

    def info(self, message, node):
        """ Generate information message at the given node """
        node.loc.print_message(message)

    def error(self, message, node):
        """ Trigger an error at the given node """
        raise CompilerError(message, loc=node.loc)

    def gen_global_variable(self, var_decl):
        # if typ is array, use initializer to determine size
        size = self.sizeof(var_decl.typ)
        ir_var = ir.Variable(var_decl.name, size)
        self.builder.module.add_variable(ir_var)
        self.ir_var_map[var_decl] = ir_var

    def gen_function(self, function):
        """ Generate code for a function """
        assert len(self.break_block_stack) == 0
        assert len(self.continue_block_stack) == 0
        assert not self.labeled_blocks
        self.unreachable = False
        if not function.body:
            return

        # Save current function for later on..
        self.current_function = function

        if function.typ.return_type.is_void:
            ir_function = self.builder.new_procedure(function.name)
        else:
            return_type = self.get_ir_type(function.typ.return_type)
            ir_function = self.builder.new_function(function.name, return_type)

        # Nice clean slate:
        self.scope = Scope(self.scope)

        # Create entry code:
        self.builder.set_function(ir_function)
        first_block = self.builder.new_block()
        self.builder.set_block(first_block)
        ir_function.entry = first_block

        # Add arguments (create memory space for them!):
        for argument in function.typ.arguments:
            arg_name = argument.name
            if arg_name is None:
                arg_name = 'no_name'
            else:
                if self.scope.is_defined(arg_name, all_scopes=False):
                    self.error('Illegal redefine', argument)
            self.scope.insert(argument)

            ir_typ = self.get_ir_type(argument.typ)
            ir_argument = ir.Parameter(arg_name, ir_typ)
            ir_function.add_parameter(ir_argument)
            size = self.sizeof(argument.typ)
            ir_var = self.emit(ir.Alloc(arg_name + '_alloc', size))
            self.emit(ir.Store(ir_argument, ir_var))
            self.ir_var_map[argument] = ir_var

        # Generate code for body:
        self.gen_stmt(function.body)

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
        self.scope = self.scope.parent
        assert len(self.break_block_stack) == 0
        assert len(self.continue_block_stack) == 0

    def gen_stmt(self, statement):
        fn_map = {
            nodes.If: self.gen_if,
            nodes.While: self.gen_while,
            nodes.DoWhile: self.gen_do_while,
            nodes.For: self.gen_for,
            nodes.Switch: self.gen_switch,
            nodes.Goto: self.gen_goto,
            nodes.Break: self.gen_break,
            nodes.Continue: self.gen_continue,
            nodes.Return: self.gen_return,
            nodes.Label: self.gen_label,
            nodes.Case: self.gen_case,
            nodes.Default: self.gen_default,
        }
        if type(statement) in fn_map:
            fn_map[type(statement)](statement)
        elif isinstance(statement, nodes.Compound):
            for inner_statement in statement.statements:
                self.gen_stmt(inner_statement)
        elif isinstance(statement, nodes.Empty):
            pass
        elif isinstance(statement, nodes.Expression):
            self.gen_expr(statement)
        elif isinstance(statement, nodes.VariableDeclaration):
            self.gen_local_var(statement)
        else:  # pragma: no cover
            raise NotImplementedError(str(statement))

    def gen_if(self, stmt: nodes.If):
        """ Generate if-statement code """
        final_block = self.builder.new_block()
        yes_block = self.builder.new_block()
        if stmt.no:
            no_block = self.builder.new_block()
        else:
            no_block = final_block
        self.gen_condition(stmt.condition, yes_block, no_block, self.CODEGEN)
        self.builder.set_block(yes_block)
        self.gen_stmt(stmt.yes)
        self.emit(ir.Jump(final_block))
        if stmt.no:
            self.builder.set_block(no_block)
            self.gen_stmt(stmt.no)
            self.emit(ir.Jump(final_block))
        self.builder.set_block(final_block)

    def gen_switch(self, stmt: nodes.Switch):
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
        test_value = self.gen_expr(stmt.expression)
        for option, target_block in self.switch_options.items():
            print(option)
            if option == 'default':
                pass
            else:
                option = self.emit(ir.Const(option, 'case', ir.i32))
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

    def gen_while(self, stmt: nodes.While):
        """ Generate while statement code """
        condition_block = self.builder.new_block()
        body_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.break_block_stack.append(final_block)
        self.continue_block_stack.append(condition_block)
        self.emit(ir.Jump(condition_block))
        self.builder.set_block(condition_block)
        self.gen_condition(
            stmt.condition, body_block, final_block, self.CODEGEN)
        self.builder.set_block(body_block)
        self.gen_stmt(stmt.body)
        self.emit(ir.Jump(condition_block))
        self.builder.set_block(final_block)
        self.break_block_stack.pop(-1)
        self.continue_block_stack.pop(-1)

    def gen_do_while(self, stmt: nodes.DoWhile):
        """ Generate do-while-statement code """
        body_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.break_block_stack.append(final_block)
        self.continue_block_stack.append(body_block)
        self.emit(ir.Jump(body_block))
        self.builder.set_block(body_block)
        self.gen_stmt(stmt.body)
        self.gen_condition(
            stmt.condition, body_block, final_block, self.CODEGEN)
        self.builder.set_block(final_block)
        self.break_block_stack.pop(-1)
        self.continue_block_stack.pop(-1)

    def gen_for(self, stmt: nodes.For):
        """ Generate code for for-statement """
        condition_block = self.builder.new_block()
        body_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.break_block_stack.append(final_block)
        self.continue_block_stack.append(condition_block)
        if stmt.init:
            self.gen_stmt(stmt.init)
        self.emit(ir.Jump(condition_block))
        self.builder.set_block(condition_block)
        if stmt.condition:
            self.gen_condition(
                stmt.condition, body_block, final_block, self.CODEGEN)
        else:
            self.emit(ir.Jump(body_block))
        self.builder.set_block(body_block)
        self.gen_stmt(stmt.body)
        if stmt.post:
            self.gen_stmt(stmt.post)
        self.emit(ir.Jump(condition_block))
        self.builder.set_block(final_block)
        self.break_block_stack.pop(-1)
        self.continue_block_stack.pop(-1)

    def gen_label(self, stmt: nodes.Label):
        """ Generate code for a label """
        block = self.get_label_block(stmt.name)
        self.emit(ir.Jump(block))  # fall through
        self.builder.set_block(block)
        self.gen_stmt(stmt.statement)

    def gen_case(self, stmt: nodes.Case):
        """ Generate code for case label inside a switch statement """
        case_value = self.gen_expr(stmt.value, purpose=self.CONST_EVAL)
        block = self.builder.new_block()
        if self.switch_options is None:
            self.error('Case statement outside of a switch!', stmt)
        if case_value in self.switch_options:
            self.error('Case defined multiple times', stmt)
        self.switch_options[case_value] = block
        self.emit(ir.Jump(block))  # fall through
        self.builder.set_block(block)
        self.gen_stmt(stmt.statement)

    def gen_default(self, stmt: nodes.Default):
        """ Generate code for case label inside a switch statement """
        block = self.builder.new_block()
        if self.switch_options is None:
            self.error('Default statement outside of a switch!', stmt)
        self.switch_options['default'] = block
        self.emit(ir.Jump(block))  # fall through
        self.builder.set_block(block)
        self.gen_stmt(stmt.statement)

    def gen_goto(self, stmt: nodes.Goto):
        """ Generate code for a goto statement """
        block = self.get_label_block(stmt.label)
        self.emit(ir.Jump(block))
        new_block = self.builder.new_block()
        self.builder.set_block(new_block)
        self.unreachable = True

    def gen_continue(self, stmt: nodes.Continue):
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

    def gen_break(self, stmt: nodes.Break):
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

    def gen_return(self, stmt: nodes.Return):
        """ Generate return statement code """
        return_type = self.current_function.typ.return_type
        if stmt.value:
            if return_type.is_void:
                self.error('Cannot return a value from this function', stmt)
            value = self.gen_expr(stmt.value, rvalue=True)
            value = self.coerce(stmt.value, value, return_type, self.CODEGEN)
            self.emit(ir.Return(value))
        else:
            if not return_type.is_void:
                self.error('Must return a value from this function', stmt)
            self.emit(ir.Exit())
        new_block = self.builder.new_block()
        self.builder.set_block(new_block)

    def gen_condition(
            self, condition: nodes.Expression, yes_block, no_block,
            purpose):
        """ Generate switch based on condition.

        If the purpose is to generate code, then jump to one of the given
        blocks.

        If the purpose is to evaluate an expression, the value of the
        expression is returned.
        """
        if isinstance(condition, nodes.Binop):
            if condition.op == '||':
                condition.typ = self.get_type(['int'])
                if purpose is self.CODEGEN:
                    middle_block = self.builder.new_block()
                    self.gen_condition(
                        condition.a, yes_block, middle_block, purpose)
                    self.builder.set_block(middle_block)
                    self.gen_condition(
                        condition.b, yes_block, no_block, purpose)
                    value = None
                else:  # pragma: no cover
                    raise NotImplementedError()
            elif condition.op == '&&':
                condition.typ = self.get_type(['int'])
                if purpose is self.CODEGEN:
                    middle_block = self.builder.new_block()
                    self.gen_condition(
                        condition.a, middle_block, no_block, purpose)
                    self.builder.set_block(middle_block)
                    self.gen_condition(
                        condition.b, yes_block, no_block, purpose)
                    value = None
                else:  # pragma: no cover
                    raise NotImplementedError()
            elif condition.op in ['<', '>', '==', '!=', '<=', '>=']:
                lhs = self.gen_expr(
                    condition.a, rvalue=True, purpose=purpose)
                rhs = self.gen_expr(
                    condition.b, rvalue=True, purpose=purpose)
                common_typ = self.get_common_type(
                    condition.a.typ, condition.b.typ)
                lhs = self.coerce(condition.a, lhs, common_typ, purpose)
                rhs = self.coerce(condition.b, rhs, common_typ, purpose)
                condition.typ = self.get_type(['int'])
                if purpose is self.CONST_EVAL:
                    raise NotImplementedError()
                elif purpose is self.CODEGEN:
                    op_map = {
                        '>': '>', '<': '<',
                        '==': '==', '!=': '!=',
                        '<=': '<=', '>=': '>='
                    }
                    op = op_map[condition.op]
                    self.emit(ir.CJump(lhs, op, rhs, yes_block, no_block))
                    value = None
                else:
                    value = None
            else:
                value = self.check_non_zero(
                    condition, yes_block, no_block, purpose)
        elif isinstance(condition, nodes.Unop):
            if condition.op == '!':
                # Simply swap yes and no here!
                value = self.gen_condition(
                    condition.a, no_block, yes_block, purpose)
            else:
                value = self.check_non_zero(
                    condition, yes_block, no_block, purpose)
        else:
            value = self.check_non_zero(
                condition, yes_block, no_block, purpose)

        # Cannot assert here because coercion may occur
        # assert self.equal_types(condition.typ, self.get_type(['int']))
        return value

    def check_non_zero(self, expr, yes_block, no_block, purpose):
        """ Check an expression for being non-zero """
        value = self.gen_expr(expr, rvalue=True, purpose=purpose)
        typ = self.get_type(['int'])
        value = self.coerce(expr, value, typ, purpose)
        if purpose is self.CONST_EVAL:
            return value != 0
        elif purpose is self.CODEGEN:
            ir_typ = self.get_ir_type(typ)
            zero = self.emit(ir.Const(0, 'zero', ir_typ))
            self.emit(ir.CJump(value, '==', zero, no_block, yes_block))
        else:
            pass

    def gen_local_var(self, variable: nodes.VariableDeclaration):
        """ Generate a local variable """
        if self.scope.is_defined(variable.name, all_scopes=False):
            self.error('Illegal redefine', variable)
        self.scope.insert(variable)

        name = variable.name
        size = self.sizeof(variable.typ)
        ir_addr = self.emit(ir.Alloc(name + '_alloc', size))
        self.ir_var_map[variable] = ir_addr

    # Gen expression can serve various purposes:
    CODEGEN = 'cgen'
    CONST_EVAL = 'eval'
    TYPECHECK = 'typecheck'

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

    def gen_expr(self, expr, rvalue=False, purpose=CODEGEN):
        """ Generate code for an expression, evaluate it or typecheck.

        rvalue: if True, then the result of the expression will be an rvalue.
        purpose: Indicating the purpose for calling this function.
        """
        assert isinstance(expr, nodes.Expression)

        if isinstance(expr, nodes.Unop):
            if expr.op in ['x++', 'x--', '--x', '++x']:
                # Increment and decrement in pre and post form
                if purpose is self.CONST_EVAL:
                    self.error('Not a constant expression', expr)
                ir_a = self.gen_expr(expr.a, rvalue=False, purpose=purpose)
                if not expr.a.lvalue:
                    self.error('Expected lvalue', expr.a)
                expr.typ = expr.a.typ
                expr.lvalue = False

                if purpose is self.CODEGEN:
                    ir_typ = self.get_ir_type(expr.typ)
                    loaded = self.emit(ir.Load(ir_a, 'loaded', ir_typ))
                    # for pointers, this is not one, but sizeof
                    if isinstance(expr.typ, nodes.PointerType):
                        size = self.sizeof(expr.typ.pointed_type)
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
                else:
                    value = None
            elif expr.op == '*':
                if purpose is self.CONST_EVAL:
                    self.error('Not a constant expression', expr)
                a = self.gen_expr(expr.a, rvalue=True, purpose=purpose)
                if not isinstance(expr.a.typ, nodes.PointerType):
                    self.error('Cannot derefence non-pointer type', expr)
                value = a
                expr.typ = expr.a.typ.pointed_type
                expr.lvalue = True
            elif expr.op == '&':
                if purpose is self.CONST_EVAL:
                    self.error('Not a constant expression', expr)
                a = self.gen_expr(expr.a, rvalue=False, purpose=purpose)
                if not expr.a.lvalue:
                    self.error('Expected lvalue', expr.a)
                value = a
                expr.typ = nodes.PointerType(expr.a.typ)
                expr.lvalue = False
            elif expr.op == '-':
                a = self.gen_expr(expr.a, rvalue=True, purpose=purpose)
                expr.typ = expr.a.typ
                expr.lvalue = False
                if purpose is self.CONST_EVAL:
                    value = -a
                elif purpose is self.CODEGEN:
                    ir_typ = self.get_ir_type(expr.typ)
                    zero = self.emit(ir.Const(0, 'zero', ir_typ))
                    value = self.emit(ir.Binop(zero, '-', a, 'neg', ir_typ))
                else:
                    value = None
            elif expr.op == '~':
                a = self.gen_expr(expr.a, rvalue=True, purpose=purpose)
                expr.typ = expr.a.typ
                expr.lvalue = False
                # TODO: implement operator
                raise NotImplementedError()
                value = a
            else:
                raise NotImplementedError(str(expr.op))
        elif isinstance(expr, nodes.Binop):
            if expr.op in ['+', '-', '*', '/', '%', '|', '&', '>>', '<<']:
                lhs = self.gen_expr(expr.a, rvalue=True, purpose=purpose)
                rhs = self.gen_expr(expr.b, rvalue=True, purpose=purpose)
                op = expr.op

                common_typ = self.get_common_type(expr.a.typ, expr.b.typ)
                lhs = self.coerce(expr.a, lhs, common_typ, purpose)
                rhs = self.coerce(expr.b, rhs, common_typ, purpose)

                expr.typ = common_typ
                expr.lvalue = False
                if purpose is self.CONST_EVAL:
                    op_map = {
                        '+': lambda x, y: x + y,
                        '-': lambda x, y: x - y,
                        '*': lambda x, y: x * y,
                        '/': lambda x, y: x / y,
                        '>>': lambda x, y: x >> y,
                        '<<': lambda x, y: x << y,
                    }
                    value = op_map[op](lhs, rhs)
                elif purpose is self.CODEGEN:
                    ir_typ = self.get_ir_type(expr.typ)
                    value = self.emit(ir.Binop(lhs, op, rhs, 'op', ir_typ))
                else:
                    value = None
            elif expr.op == ',':
                # Handle the comma operator by returning the second result
                if purpose is self.CONST_EVAL:
                    self.error('Not a constant expression', expr)
                lhs = self.gen_expr(expr.a, rvalue=True, purpose=purpose)
                rhs = self.gen_expr(expr.b, rvalue=True, purpose=purpose)
                expr.typ = expr.b.typ
                expr.lvalue = False
                value = rhs
            elif expr.op in ['<', '>', '==', '!=', '<=', '>=', '||', '&&']:
                if purpose is self.CONST_EVAL:
                    # TODO: implement constant
                    self.error('Not a constant expression', expr)

                expr.lvalue = False
                if purpose is self.CODEGEN:
                    yes_block = self.builder.new_block()
                    no_block = self.builder.new_block()
                    end_block = self.builder.new_block()
                    self.gen_condition(expr, yes_block, no_block, purpose)
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
                else:
                    value = None
            elif expr.op in [
                    '=', '+=', '-=', '*=', '%=', '/=',
                    '>>=', '<<=',
                    '&=', '|=', '~=', '^=']:
                if purpose is self.CONST_EVAL:
                    self.error('Not a constant expression', expr)
                lhs = self.gen_expr(expr.a, rvalue=False, purpose=purpose)
                rhs = self.gen_expr(expr.b, rvalue=True, purpose=purpose)
                rhs = self.coerce(expr.b, rhs, expr.a.typ, purpose)
                expr.lvalue = False
                expr.typ = expr.a.typ

                if not expr.a.lvalue:
                    self.error('Expected lvalue', expr.a)
                # Handle '+=' and friends:
                if purpose is self.CODEGEN:
                    if expr.op != '=':
                        op = expr.op[:-1]
                        ir_typ = self.get_ir_type(expr.typ)
                        loaded = self.emit(ir.Load(lhs, 'lhs', ir_typ))
                        value = self.emit(ir.Binop(
                            loaded, op, rhs, 'assign', ir_typ))
                    else:
                        value = rhs
                    self.emit(ir.Store(value, lhs))
                else:
                    value = None
            else:  # pragma: no cover
                raise NotImplementedError(str(expr.op))
        elif isinstance(expr, nodes.VariableAccess):
            if not self.scope.is_defined(expr.name):
                self.error('Who is this?', expr)
            variable = self.scope.get(expr.name)
            expr.typ = variable.typ
            if isinstance(variable, nodes.VariableDeclaration):
                if purpose is self.CONST_EVAL:
                    # TODO: handle const int values?
                    self.error('Not a constant expression', expr)
                expr.lvalue = True
                if purpose is self.CODEGEN:
                    value = self.ir_var_map[variable]
                else:
                    value = None
            elif isinstance(variable, nodes.ConstantDeclaration):
                expr.lvalue = False
                constant_value = self.get_const_value(variable)
                if purpose is self.CONST_EVAL:
                    value = constant_value
                elif purpose is self.CODEGEN:
                    ir_typ = self.get_ir_type(expr.typ)
                    value = self.emit(ir.Const(
                        constant_value, variable.name, ir_typ))
                else:
                    raise NotImplementedError()
            else:
                raise NotImplementedError()
        elif isinstance(expr, nodes.FunctionCall):
            if purpose is self.CONST_EVAL:
                self.error('Not a constant expression', expr)
            # Lookup the function:
            if not self.scope.is_defined(expr.name):
                self.error('Who is this?', expr)
            function = self.scope.get(expr.name)
            if not isinstance(function, nodes.FunctionDeclaration):
                self.error('Calling a non-function', expr)

            # Determine expression properties:
            expr.typ = function.typ.return_type
            expr.lvalue = False

            # Check argument count:
            num_expected = len(function.typ.arg_types)
            num_given = len(expr.args)
            if num_given != num_expected:
                self.error('Expected {} arguments, but got {}'.format(
                    num_expected, num_given), expr)

            # Evaluate arguments:
            ir_arguments = []
            for argument, arg_type in zip(expr.args, function.typ.arg_types):
                value = self.gen_expr(argument, rvalue=True, purpose=purpose)
                value = self.coerce(argument, value, arg_type, purpose)
                ir_arguments.append(value)

            if purpose is self.CODEGEN:
                if function.typ.return_type.is_void:
                    self.emit(ir.ProcedureCall(function.name, ir_arguments))
                    value = None
                else:
                    ir_typ = self.get_ir_type(expr.typ)
                    value = self.emit(ir.FunctionCall(
                        function.name, ir_arguments, 'result', ir_typ))
            else:
                value = None
        elif isinstance(expr, nodes.Literal):
            # TODO: handle more types
            if isinstance(expr.value, str) and len(expr.value) > 3:
                # String literal:
                expr.typ = self.cstr_type
                expr.lvalue = False
                if purpose is self.CONST_EVAL:
                    self.error('A string is no constant expression')
                elif purpose is self.CODEGEN:
                    # Construct nifty 0-terminated string into memory!
                    data = expr.value.encode('ascii') + bytes([0])
                    value = self.emit(ir.LiteralData(data, 'cstr'))
                else:
                    value = None
            else:
                # TODO: get value from string
                v = int(expr.value)
                expr.typ = self.get_type(['int'])
                expr.lvalue = False
                if purpose is self.CONST_EVAL:
                    value = v
                elif purpose is self.CODEGEN:
                    ir_typ = self.get_ir_type(expr.typ)
                    value = self.emit(ir.Const(v, 'constant', ir_typ))
                else:
                    value = None
        elif isinstance(expr, nodes.Cast):
            # TODO: is the cast valid?
            a = self.gen_expr(expr.expr, rvalue=True, purpose=purpose)
            expr.typ = expr.to_typ
            expr.lvalue = False  # or expr.expr.lvalue?
            if purpose is self.CONST_EVAL:
                # TODO: handle some form of casting?
                value = a
            elif purpose is self.CODEGEN:
                ir_typ = self.get_ir_type(expr.typ)
                value = self.emit(ir.Cast(a, 'typecast', ir_typ))
            else:
                value = None
        elif isinstance(expr, nodes.Sizeof):
            expr.typ = self.get_type(['int'])
            expr.lvalue = False
            if isinstance(expr.sizeof_typ, nodes.CType):
                # Get size of the given type:
                type_size = self.sizeof(expr.sizeof_typ)
            else:
                # Check the type of expression:
                self.gen_expr(expr.sizeof_typ, purpose=self.TYPECHECK)
                # And get its size:
                type_size = self.sizeof(expr.sizeof_typ.typ)
            if purpose is self.CONST_EVAL:
                value = type_size
            elif purpose is self.CODEGEN:
                ir_typ = self.get_ir_type(expr.typ)
                value = self.emit(ir.Const(type_size, 'type_size', ir_typ))
            else:
                value = None
        elif isinstance(expr, nodes.FieldSelect):
            if purpose is self.CONST_EVAL:
                self.error('Not a constant expression', expr)
            base = self.gen_expr(expr.base, rvalue=False, purpose=purpose)
            if not expr.base.lvalue:
                self.error('Expected lvalue', expr.base)
            base_type = self.resolve_type(expr.base.typ)
            if not isinstance(base_type, nodes.StructType):
                self.error(
                    'Cannot index field of non struct type {}'.format(
                        base_type), expr)
            if not base_type.has_field(expr.field):
                self.error(
                    'Field {} not part of struct'.format(expr.field), expr)
            field = base_type.get_field(expr.field)
            expr.typ = field.typ
            expr.lvalue = True
            self.logger.warning('implement offset from field select')
            if purpose is self.CODEGEN:
                offset = 0
                # TODO: calculate offset into struct
                offset = self.emit(ir.Const(offset, 'offset', ir.ptr))
                value = self.emit(
                    ir.Binop(base, '+', offset, 'offset', ir.ptr))
            else:
                value = None
        elif isinstance(expr, nodes.ArrayIndex):
            if purpose is self.CONST_EVAL:
                self.error('Not a constant expression', expr)
            base = self.gen_expr(expr.base, rvalue=False, purpose=purpose)
            index = self.gen_expr(expr.index, rvalue=True, purpose=purpose)
            index = self.coerce(
                expr.index, index, self.get_type(['int']), purpose)
            if not expr.base.lvalue:
                # TODO: must array base be an lvalue?
                self.error('Expected lvalue', expr.base)
            base_type = self.resolve_type(expr.base.typ)
            if not isinstance(base_type, nodes.ArrayType):
                self.error(
                    'Cannot index non array type {}'.format(
                        base_type), expr)

            expr.typ = self.resolve_type(base_type.element_type)
            expr.lvalue = True

            if purpose is self.CODEGEN:
                # Generate constant for element size:
                element_type_size = self.sizeof(expr.typ)
                element_size = self.emit(
                    ir.Const(element_type_size, 'element_size', ir.ptr))

                # Calculate offset:
                index = self.emit(ir.Cast(index, 'index', ir.ptr))
                offset = self.emit(
                    ir.mul(index, element_size, "element_offset", ir.ptr))

                # Calculate address:
                value = self.emit(
                    ir.add(base, offset, "element_address", ir.ptr))
            else:
                value = None
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))

        # Check for given attributes:
        assert isinstance(expr.typ, nodes.CType)
        assert isinstance(expr.lvalue, bool)

        if purpose is self.CODEGEN:
            # assert isinstance(value, ir.Value)
            pass
        elif purpose is self.TYPECHECK:
            assert value is None

        # If we need an rvalue, load it!
        if rvalue and expr.lvalue and (purpose is self.CODEGEN):
            ir_typ = self.get_ir_type(expr.typ)
            value = self.emit(ir.Load(value, 'load', ir_typ))
        return value

    def get_type(self, type_specifiers):
        """ Retrieve a type by type specifiers """
        assert isinstance(type_specifiers, list)
        return self.context.get_type(type_specifiers)

    def get_ir_type(self, typ: nodes.CType):
        """ Given a C type, get the fitting ir type """
        assert isinstance(typ, nodes.CType)

        if isinstance(typ, nodes.BareType):
            return self.ir_type_map[typ.type_id][0]
        elif isinstance(typ, nodes.IdentifierType):
            return self.get_ir_type(self.resolve_type(typ))
        elif isinstance(typ, nodes.PointerType):
            return ir.ptr
        elif isinstance(typ, nodes.EnumType):
            return self.ir_type_map[nodes.BareType.INT][0]
        else:
            raise NotImplementedError(str(typ))

    def equal_types(self, typ1, typ2):
        """ Check for type equality """
        # TODO: enhance!
        if typ1 is typ2:
            # A short circuit:
            return True
        # elif isinstance(typ1, nodes.QualifiedType):
        #    # Handle qualified types:
        #    if isinstance(typ2, nodes.QualifiedType):
        #        return typ1.qualifiers == typ2.qualifiers and \
        #            self.equal_types(typ1.typ, typ2.typ)
        #    else:
        #        return (not typ1.qualifiers) and \
        #            self.equal_types(typ1.typ, typ2)
        # elif isinstance(typ2, nodes.QualifiedType):
        #    # Handle qualified types (we know that typ1 unqualified)
        #    return (not typ2.qualifiers) and self.equal_types(typ1, typ2.typ)
        elif isinstance(typ1, nodes.BareType):
            if isinstance(typ2, nodes.BareType):
                return typ1.type_id == typ2.type_id
        elif isinstance(typ1, nodes.IdentifierType):
            if isinstance(typ2, nodes.IdentifierType):
                return typ1.name == typ2.name
        elif isinstance(typ1, nodes.FunctionType):
            if isinstance(typ2, nodes.FunctionType):
                return len(typ1.arg_types) == len(typ2.arg_types) and \
                    self.equal_types(typ1.return_type, typ2.return_type) and \
                    all(self.equal_types(a1, a2) for a1, a2 in zip(
                        typ1.arg_types, typ2.arg_types))
        elif isinstance(typ1, nodes.PointerType):
            if isinstance(typ2, nodes.PointerType):
                return self.equal_types(typ1.pointed_type, typ2.pointed_type)
        else:
            raise NotImplementedError(str(typ1))
        return False

    def get_common_type(self, typ1, typ2):
        """ Given two types, determine the common type.

        The common type is a type they can both be cast to. """
        # TODO!
        return typ1

    def resolve_type(self, typ: nodes.IdentifierType):
        """ Given a type, look behind the identifiertype """
        if isinstance(typ, nodes.IdentifierType):
            if self.type_scope.is_defined(typ.name):
                # Typedef type!
                typedef = self.type_scope.get(typ.name)
                assert isinstance(typedef, nodes.Typedef)
                return self.resolve_type(typedef.typ)
            else:  # pragma: no cover
                raise KeyError(typ.name)
        else:
            return typ

    def coerce(
            self, expr: nodes.Expression, value, typ: nodes.CType,
            purpose):
        """ Try to fit the given expression into the given type """
        do_cast = False
        from_type = self.resolve_type(expr.typ)
        to_type = self.resolve_type(typ)

        if self.equal_types(from_type, to_type):
            pass
        elif isinstance(from_type, nodes.PointerType) and \
                isinstance(to_type, nodes.BareType):
            do_cast = True
        elif isinstance(from_type, nodes.PointerType) and \
                isinstance(to_type, nodes.PointerType):
            do_cast = True
        elif isinstance(from_type, nodes.BareType) and \
                isinstance(to_type, nodes.PointerType):
            do_cast = True
        elif isinstance(from_type, nodes.BareType) and \
                isinstance(to_type, (nodes.BareType, nodes.EnumType)):
            # TODO: implement stricter checks
            do_cast = True
        else:
            self.error('Cannot convert {} to {}'.format(expr.typ, typ), expr)

        if do_cast:
            if purpose is self.CONST_EVAL:
                raise NotImplementedError()
            elif purpose is self.CODEGEN:
                ir_typ = self.get_ir_type(to_type)
                value = self.emit(ir.Cast(value, 'casting', ir_typ))
            else:
                pass
        return value

    def sizeof(self, typ: nodes.CType):
        """ Given a type, determine its size in whole bytes """
        assert isinstance(typ, nodes.CType)
        if isinstance(typ, nodes.ArrayType):
            element_size = self.sizeof(typ.element_type)
            array_size = self.gen_expr(typ.size, purpose=self.CONST_EVAL)
            return element_size * array_size
        elif isinstance(typ, nodes.BareType):
            return self.ir_type_map[typ.type_id][1]
        elif isinstance(typ, nodes.IdentifierType):
            return self.sizeof(self.resolve_type(typ))
        elif isinstance(typ, nodes.StructType):
            if not typ.complete:
                self.error('Storage size unknown', typ)
            return sum(self.sizeof(part.typ) for part in typ.fields)
        elif isinstance(typ, nodes.UnionType):
            if not typ.complete:
                self.error('Storage size unknown', typ)
            return max(self.sizeof(part.typ) for part in typ.fields)
        elif isinstance(typ, nodes.EnumType):
            if not typ.complete:
                self.error('Storage size unknown', typ)
            # For enums take int as the type
            return self.context.march.byte_sizes['int']
        elif isinstance(typ, nodes.PointerType):
            return self.context.march.byte_sizes['ptr']
        elif isinstance(typ, nodes.FunctionType):
            # TODO: can we determine size of a function type? Should it not
            # be pointer to a function?
            return self.context.march.byte_sizes['ptr']
        elif isinstance(typ, nodes.QualifiedType):
            return self.sizeof(typ.typ)
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))
