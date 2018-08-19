""" IR-code generation.

Walks over the AST of the C sourcecode and generates IR-code.

Most errors and warnings are already detected during the parsing / semantics
phase.

"""
import logging
from ... import ir, irutils
from ...common import CompilerError
from ...binutils import debuginfo
from .nodes import types, declarations, statements, expressions
from .utils import required_padding
from .nodes.types import BasicType
from .scope import RootScope


class CCodeGenerator:
    """ Converts parsed C code to ir-code """
    logger = logging.getLogger('ccodegen')

    def __init__(self, context):
        self.context = context
        self._root_scope = RootScope()
        self.builder = None
        self.debug_db = None
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
        self.ptr_size = self.context.arch_info.get_size('ptr')
        self.ir_type_map = {
            BasicType.CHAR: (ir.i8, 1),
            BasicType.UCHAR: (ir.u8, 1),
            BasicType.SHORT: (ir.i16, 2),
            BasicType.USHORT: (ir.u16, 2),
            BasicType.INT: (int_types[int_size], int_size),
            BasicType.UINT: (uint_types[int_size], int_size),
            BasicType.LONG: (ir.i32, 4),
            BasicType.ULONG: (ir.u32, 4),
            BasicType.LONGLONG: (ir.i64, 8),
            BasicType.ULONGLONG: (ir.u64, 8),
            BasicType.FLOAT: (ir.f32, 4),
            BasicType.DOUBLE: (ir.f64, 8),
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
        self.debug_db = debuginfo.DebugDb()
        ir_mod = ir.Module('main', debug_db=self.debug_db)
        self.builder.module = ir_mod
        for declaration in compile_unit.declarations:
            self.gen_object(declaration)
        self.logger.info('Finished IR-code generation')
        return ir_mod

    def gen_object(self, declaration):
        """ Generate code for a single object """
        assert isinstance(declaration, declarations.CDeclaration)

        # Generate code:
        if isinstance(declaration, declarations.Typedef):
            pass
            # self.type_scope.insert(declaration)
        elif isinstance(declaration, declarations.FunctionDeclaration):
            self.gen_function(declaration)
        elif isinstance(declaration, declarations.VariableDeclaration):
            self.gen_global_variable(declaration)
        elif isinstance(declaration, declarations.EnumConstantDeclaration):
            pass
        else:  # pragma: no cover
            raise NotImplementedError(str(declaration))

    def emit(self, instruction, location=None):
        """ Helper function to emit a single instruction """
        # print(instruction)
        if location:
            self.debug_db.enter(instruction, debuginfo.DebugLocation(location))
        return self.builder.emit(instruction)

    def info(self, message, node):
        """ Generate information message at the given node """
        node.loc.print_message(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message, location):
        """ Trigger an error at the given node """
        raise CompilerError(message, loc=location)

    def gen_global_variable(self, var_decl):
        """ Generate code for a global variable """
        if var_decl.storage_class == 'extern':
            # create an external variable:
            ir_var = ir.ExternalVariable(var_decl.name)
            self.builder.module.add_external(ir_var)
            self.ir_var_map[var_decl] = ir_var
        else:
            # if typ is array, use initializer to determine size
            if var_decl.initial_value:
                ivalue = self.context.gen_global_ival(
                    var_decl.typ, var_decl.initial_value)
            else:
                ivalue = None
            size = self.context.sizeof(var_decl.typ)
            alignment = self.context.alignment(var_decl.typ)
            if var_decl.storage_class == 'static':
                name = '__static' + var_decl.name
            else:
                name = var_decl.name
            ir_var = ir.Variable(name, size, alignment, value=ivalue)
            self.builder.module.add_variable(ir_var)
            self.ir_var_map[var_decl] = ir_var

    def gen_function(self, function):
        """ Generate code for a function """
        if function.body:
            self.gen_function_def(function)
        else:
            # TODO: when to put a function declaration as extern?
            # For now just ignore extern keyword?
            if True:  # function.storage_class == 'extern':
                ftyp = function.typ
                argument_types = [
                    self.get_ir_type(a.typ) for a in ftyp.arguments]

                if ftyp.is_vararg:
                    argument_types.append(ir.ptr)

                if ftyp.return_type.is_void:
                    external_function = ir.ExternalProcedure(
                        function.name, argument_types)
                else:
                    return_type = self.get_ir_type(ftyp.return_type)
                    external_function = ir.ExternalFunction(
                        function.name, argument_types, return_type)

                self.builder.module.add_external(external_function)
                self.ir_var_map[function] = external_function
            else:
                # Okay, a declaration, no body, what now?
                pass

    def gen_function_def(self, function):
        """ Generate code for a function definition """
        self.logger.debug('Generating IR-code for %s', function.name)
        assert not self.break_block_stack
        assert not self.continue_block_stack
        self.labeled_blocks = {}
        assert not self.labeled_blocks
        self.unreachable = False

        # Save current function for later on..
        self.current_function = function

        # Create ir function:
        if function.typ.return_type.is_void:
            ir_function = self.builder.new_procedure(function.name)
        elif function.typ.return_type.is_struct:
            # Pass implicit first argument to function when complex type
            # is returned.
            ir_function = self.builder.new_procedure(function.name)
            self.return_value_address = ir.Parameter(
                'return_value_address', ir.ptr)
            ir_function.add_parameter(self.return_value_address)
        else:
            return_type = self.get_ir_type(function.typ.return_type)
            ir_function = self.builder.new_function(function.name, return_type)
        self.ir_var_map[function] = ir_function

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
                if isinstance(ir_typ, ir.BlobDataTyp):
                    ir_var = self.emit(
                        ir.AddressOf(ir_argument, argument.name + '_addr'))
                else:
                    name = argument.name + '_alloc'
                    size = self.context.sizeof(argument.typ)
                    alignment = self.context.alignment(argument.typ)
                    ir_var = self.emit(ir.Alloc(name, size, alignment))
                    ir_var = self.emit(
                        ir.AddressOf(ir_var, argument.name + '_addr'))
                    self.emit(ir.Store(ir_argument, ir_var))
                self.ir_var_map[argument] = ir_var

        # In case of a variadic function, add an extra pointer:
        if function.typ.is_vararg:
            self.logger.debug('Adding vararg pointer')
            ir_argument = ir.Parameter('varargz', ir.ptr)
            ir_function.add_parameter(ir_argument)
            self._varargz_ptr = ir_argument

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
                warn_when_no_return = True
                if warn_when_no_return:
                    self.warning('Function does not return a value')
                    ir_typ = self.get_ir_type(function.typ.return_type)
                    zero = self.emit(ir.Const(0, 'zero', ir_typ))
                    self.emit(ir.Return(zero))
                else:
                    self.error(
                        'Function does not return an {}'.format(
                            function.typ.return_type),
                        function)

        # TODO: maybe generate only code which is reachable?
        ir_function.delete_unreachable()
        self.builder.set_function(None)
        self.current_function = None
        self._varargz_ptr = None
        assert not self.break_block_stack
        assert not self.continue_block_stack

    def gen_stmt(self, statement):
        """ Generate code for the given statement """
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

    def gen_empty_statement(self, statement) -> None:
        """ Generate code for empty statement """
        pass

    def gen_compound(self, statement) -> None:
        """ Generate code for a compound statement """
        for inner_statement in statement.statements:
            self.gen_stmt(inner_statement)

    def gen_declaration_statement(self, statement):
        """ Generate code for a declaration statement """
        declaration = statement.declaration
        if isinstance(declaration, declarations.VariableDeclaration):
            if declaration.storage_class == 'static':
                self.gen_global_variable(declaration)
            else:
                self.gen_local_variable(declaration)
        else:
            raise NotImplementedError(str(declaration))

    def gen_expression_statement(self, statement):
        """ Generate code for an expression statement """
        self.gen_expr(statement.expression, rvalue=True)
        # TODO: issue a warning when expression result is non void?

    def gen_if(self, stmt: statements.If) -> None:
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

    def gen_switch(self, stmt: statements.Switch) -> None:
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

    def gen_while(self, stmt: statements.While) -> None:
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

    def gen_do_while(self, stmt: statements.DoWhile) -> None:
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

    def gen_for(self, stmt: statements.For) -> None:
        """ Generate code for for-statement """
        condition_block = self.builder.new_block()
        body_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.break_block_stack.append(final_block)
        self.continue_block_stack.append(condition_block)
        if stmt.init:
            self.gen_expr(stmt.init, rvalue=True)
        self.emit(ir.Jump(condition_block))
        self.builder.set_block(condition_block)
        if stmt.condition:
            self.gen_condition(stmt.condition, body_block, final_block)
        else:
            self.emit(ir.Jump(body_block))
        self.builder.set_block(body_block)
        self.gen_stmt(stmt.body)
        if stmt.post:
            self.gen_expr(stmt.post, rvalue=True)
        self.emit(ir.Jump(condition_block))
        self.builder.set_block(final_block)
        self.break_block_stack.pop(-1)
        self.continue_block_stack.pop(-1)

    def gen_label(self, stmt: statements.Label) -> None:
        """ Generate code for a label """
        block = self.get_label_block(stmt.name)
        self.emit(ir.Jump(block))  # fall through
        self.builder.set_block(block)
        self.gen_stmt(stmt.statement)

    def gen_case(self, stmt: statements.Case) -> None:
        """ Generate code for case label inside a switch statement """
        block = self.builder.new_block()
        assert self.switch_options is not None
        value = self.context.eval_expr(stmt.value)
        if value in self.switch_options:
            self.error('Case defined multiple times', stmt.location)
        self.switch_options[value] = block
        self.emit(ir.Jump(block))  # fall through
        self.builder.set_block(block)
        self.gen_stmt(stmt.statement)

    def gen_default(self, stmt: statements.Default) -> None:
        """ Generate code for case label inside a switch statement """
        block = self.builder.new_block()
        assert self.switch_options is not None
        self.switch_options['default'] = block
        self.emit(ir.Jump(block))  # fall through
        self.builder.set_block(block)
        self.gen_stmt(stmt.statement)

    def gen_goto(self, stmt: statements.Goto) -> None:
        """ Generate code for a goto statement """
        block = self.get_label_block(stmt.label)
        self.emit(ir.Jump(block))
        new_block = self.builder.new_block()
        self.builder.set_block(new_block)
        self.unreachable = True

    def gen_continue(self, stmt: statements.Continue) -> None:
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

    def gen_break(self, stmt: statements.Break) -> None:
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

    def gen_return(self, stmt: statements.Return) -> None:
        """ Generate return statement code """
        if stmt.value:
            if stmt.value.typ.is_struct:
                # Complex types are copied to pointer passed as
                # first argument.
                value = self.gen_expr(stmt.value, rvalue=True)
                self.emit(ir.Store(value, self.return_value_address))
                # self.emit(ir.CopyBlob(self.return_value_address))
                self.emit(ir.Exit())
            else:
                # Simple types are returned via ir-value.
                value = self.gen_expr(stmt.value, rvalue=True)
                self.emit(ir.Return(value))
        else:
            self.emit(ir.Exit())
        new_block = self.builder.new_block()
        self.builder.set_block(new_block)

    def gen_condition(self, condition, yes_block, no_block):
        """ Generate switch based on condition. """
        if isinstance(condition, expressions.BinaryOperator):
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
        elif isinstance(condition, expressions.UnaryOperator):
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
        alignment = self.context.alignment(variable.typ)
        ir_alloc = self.emit(ir.Alloc(name + '_alloc', size, alignment))
        ir_addr = self.emit(ir.AddressOf(ir_alloc, name + '_addr'))
        self.ir_var_map[variable] = ir_addr
        if variable.initial_value:
            # Initialize local variable by a sequence of assignments.
            self.gen_local_init(ir_addr, variable.typ, variable.initial_value)

    def gen_local_init(self, ptr, typ, expr):
        """ Initialize a local slab of memory with an initial value """
        if isinstance(
                typ, (BasicType, types.PointerType, types.EnumType)):
            value = self.gen_expr(expr, rvalue=True)
            self._store_value(value, ptr)
            inc = self.context.sizeof(typ)
            size = self.emit(ir.Const(inc, 'size', ir.ptr))
            ptr = self.emit(ir.add(ptr, size, 'iptr', ir.ptr))
        elif isinstance(typ, types.ArrayType):
            inc = 0
            for iv in expr.elements:
                # TODO: do array elements need to be aligned?
                ptr, inc2 = self.gen_local_init(ptr, typ.element_type, iv)
                inc += inc2
        elif isinstance(typ, types.StructType):
            ptr, inc = self._init_struct(ptr, typ, expr)
        elif isinstance(typ, types.UnionType):
            # Initialize the first field!
            field = typ.fields[0]
            iv = expr.elements[0]
            ptr, inc = self.gen_local_init(ptr, field.typ, expr.elements[0])
            # Update pointer with size of union:
            # inc = self.context.sizeof(typ)
            # size = self.emit(ir.Const(inc, 'size', ir.ptr))
            # ptr = self.emit(ir.add(ptr, size, 'iptr', ir.ptr))
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))
        return ptr, inc

    def _init_struct(self, ptr, typ, expr):
        """ Fill structure with initializer (at runtime) """
        if isinstance(expr, expressions.InitializerList):
            # Initializing with list
            size, field_offsets = self.context._get_field_offsets(typ)
            offset = 0
            for field, iv in zip(typ.fields, expr.elements):
                # Move further in struct by whole bytes:
                field_offset = field_offsets[field] // 8
                if offset < field_offset:
                    pad_inc = field_offset - offset
                    padding = self.emit(ir.Const(pad_inc, 'padding', ir.ptr))
                    ptr = self.emit(ir.add(ptr, padding, 'iptr', ir.ptr))
                    offset += pad_inc

                # Fill position:
                if field.is_bitfield:  # Bit field special case!
                    value = self.gen_expr(iv, rvalue=True)
                    bitsize = self.context.eval_expr(field.bitsize)
                    bitshift = field_offsets[field] % 8
                    signed = field.typ.is_signed
                    access = BitFieldAccess(ptr, bitshift, bitsize, signed)
                    self._store_bitfield(value, access)
                    # TODO: how much to increase now?
                    inc2 = 0
                else:
                    ptr, inc2 = self.gen_local_init(ptr, field.typ, iv)
                offset += inc2

            # Fill last padding space:
            if offset < size:
                pad_inc = size - offset
                padding = self.emit(ir.Const(pad_inc, 'padding', ir.ptr))
                ptr = self.emit(ir.add(ptr, padding, 'iptr', ir.ptr))
                offset += pad_inc
            inc = offset
            assert inc == size
        else:
            # Store result of function!
            value = self.gen_expr(expr, rvalue=True)
            self.emit(ir.Store(value, ptr))
            inc = value.ty.size
        return ptr, inc

    def get_const_value(self, constant):
        """ Retrieve the calculated value for the given constant """
        if constant in self.constant_values:
            value = self.constant_values[constant]
        else:
            # Evaluate the constant now!
            if constant in self.evaluating_constants:
                self.error('Circular constant evaluation', constant.location)
            self.evaluating_constants.add(constant)
            # TODO: refactor const handling
            raise NotImplementedError()
            value = self.evaluate_expression(constant.value)
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
        assert isinstance(expr, expressions.CExpression)

        if isinstance(expr, expressions.UnaryOperator):
            value = self.gen_unop(expr)
        elif isinstance(expr, expressions.BinaryOperator):
            value = self.gen_binop(expr)
        elif isinstance(expr, expressions.TernaryOperator):
            value = self.gen_ternop(expr)
        elif isinstance(expr, expressions.VariableAccess):
            variable = expr.variable
            if isinstance(
                    variable,
                    (declarations.VariableDeclaration,
                     declarations.ParameterDeclaration,
                     declarations.ConstantDeclaration)):
                value = self.ir_var_map[variable]
            elif isinstance(variable, declarations.EnumConstantDeclaration):
                # Enum value declaration!
                constant_value = self.context.get_enum_value(
                    variable.typ, variable)
                ir_typ = self.get_ir_type(expr.typ)
                value = self.emit(ir.Const(
                    constant_value, variable.name, ir_typ))
            elif isinstance(variable, declarations.FunctionDeclaration):
                value = self.ir_var_map[variable]
            else:  # pragma: no cover
                raise NotImplementedError(str(variable))
        elif isinstance(expr, expressions.FunctionCall):
            value = self.gen_call(expr)
        elif isinstance(expr, expressions.StringLiteral):
            # Construct nifty 0-terminated string into memory!
            encoding = 'latin1'
            data = expr.value[1:-1].encode(encoding) + bytes([0])
            value = self.emit(ir.LiteralData(data, 'cstr'))
            value = self.emit(ir.AddressOf(value, 'dptr'))
        elif isinstance(expr, expressions.CharLiteral):
            ir_typ = self.get_ir_type(expr.typ)
            value = self.emit(
                ir.Const(expr.value, 'constant', ir_typ),
                location=expr.location)
        elif isinstance(expr, expressions.NumericLiteral):
            ir_typ = self.get_ir_type(expr.typ)
            value = self.emit(
                ir.Const(expr.value, 'constant', ir_typ),
                location=expr.location)
        elif isinstance(expr, expressions.InitializerList):
            expr.lvalue = True
            self.error('Illegal initializer list', expr.location)
        elif isinstance(expr, expressions.Cast):
            a = self.gen_expr(expr.expr, rvalue=True)
            if expr.to_typ.is_void:
                value = None
            else:
                ir_typ = self.get_ir_type(expr.to_typ)
                value = self.emit(
                    ir.Cast(a, 'typecast', ir_typ), location=expr.location)
        elif isinstance(expr, expressions.Sizeof):
            value = self.gen_sizeof(expr)
        elif isinstance(expr, expressions.FieldSelect):
            base = self.gen_expr(expr.base, rvalue=False)
            _, field_offsets = self.context._get_field_offsets(expr.base.typ)
            offset = field_offsets[expr.field]
            if expr.field.is_bitfield:
                offset, bitshift = offset // 8, offset % 8
                offset = self.emit(ir.Const(offset, 'offset', ir.ptr))
                value = self.emit(
                    ir.Binop(base, '+', offset, 'offset', ir.ptr))
                bitsize = self.context.eval_expr(expr.field.bitsize)
                signed = expr.field.typ.is_signed
                value = BitFieldAccess(value, bitshift, bitsize, signed)
            else:
                assert offset % 8 == 0
                offset //= 8
                offset = self.emit(ir.Const(offset, 'offset', ir.ptr))
                value = self.emit(
                    ir.Binop(base, '+', offset, 'offset', ir.ptr))
        elif isinstance(expr, expressions.ArrayIndex):
            value = self.gen_array_index(expr)
        elif isinstance(expr, expressions.BuiltIn):
            value = self.gen_builtin(expr)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))

        # Check for given attributes:
        assert isinstance(expr.typ, types.CType)
        assert isinstance(expr.lvalue, bool)  # C semantics lvalue

        # If we need an rvalue, load it!
        if rvalue and expr.lvalue:
            # Array handling is a special case!
            # when accessed, arrays turn into pointers to its first element.
            value = self._load_value(value, expr.typ)

        elif not rvalue:
            assert expr.lvalue
        return value

    def _load_value(self, lvalue, ctyp):
        """ Load a value from given l-value """
        if isinstance(ctyp, types.ArrayType):
            self.logger.debug('Array type accessed %s', ctyp)
            value = lvalue
        else:
            # TODO: inject evil bitfield manipulation code here:
            # self.logger.debug('Non-Array type is indexed %s', expr)
            ir_typ = self.get_ir_type(ctyp)
            if isinstance(ir_typ, ir.BlobDataTyp):
                # If we have a blob pointer and want its content
                # We must get the source of the address of:
                assert isinstance(lvalue, ir.AddressOf)
                value = lvalue.src
            elif isinstance(lvalue, BitFieldAccess):
                value = self._load_bitfield(lvalue, ir_typ)
            else:
                value = self.emit(ir.Load(lvalue, 'load', ir_typ))
        return value

    def _store_value(self, value, address):
        """ Store a value at given lvalue location """
        if isinstance(address, BitFieldAccess):
            self._store_bitfield(value, address)
        else:
            self.emit(ir.Store(value, address))

    def _load_bitfield(self, access, target_ir_typ):
        """ Dark voo-doo code generated here """
        assert target_ir_typ.is_integer

        ir_typ = self._get_bitfield_ir_typ(access, True)
        full_bitsize = ir_typ.bits
        # TODO: if this is the case, we need more work to be done:
        assert access.bitshift + access.bitsize <= full_bitsize

        # Load some data from memory:
        loaded = self.emit(ir.Load(access.address, 'loaded', ir_typ))

        if access.signed:
            # Shift left, then right, this to ensure sign extension
            assert loaded.ty.is_signed
            left_shift = full_bitsize - access.bitshift - access.bitsize
            right_shift = access.bitshift + left_shift
            shift_amount = self.emit(
                ir.Const(left_shift, 'left_shift', ir_typ))
            value = self.emit(
                ir.Binop(loaded, '<<', shift_amount, 'value', ir_typ))
            shift_amount = self.emit(
                ir.Const(right_shift, 'right_shift', ir_typ))
            value = self.emit(
                ir.Binop(value, '>>', shift_amount, 'value', ir_typ))
        else:
            assert not loaded.ty.is_signed
            mask = ((1 << access.bitsize) - 1) << access.bitshift
            mask = self.emit(ir.Const(mask, 'mask', ir_typ))
            value = self.emit(ir.Binop(loaded, '&', mask, 'value', ir_typ))

            # Shift value:
            if access.bitshift:
                shift_amount = self.emit(
                    ir.Const(access.bitshift, 'shift', ir_typ))
                value = self.emit(
                    ir.Binop(value, '>>', shift_amount, 'value', ir_typ))

        # Finally convert to target type:
        if value.ty is not target_ir_typ:
            value = self.emit(ir.Cast(value, 'cast', target_ir_typ))

        return value

    def _store_bitfield(self, value, access):
        """ inject evil bitfield manipulation code """
        ir_typ = self._get_bitfield_ir_typ(access, False)
        full_bitsize = ir_typ.bits
        assert access.bitshift + access.bitsize <= full_bitsize
        mask = ((1 << access.bitsize) - 1) << access.bitshift
        full_mask = (1 << full_bitsize) - 1
        inv_mask = full_mask ^ mask

        assert value.ty.is_integer

        # Optionally cast value:
        if value.ty is not ir_typ:
            value = self.emit(ir.Cast(value, 'cast', ir_typ))

        # Load memory value:
        # TODO: volatile used to enforce struct in memory.
        # Should not be required?
        loaded = self.emit(ir.Load(
            access.address, 'loaded', ir_typ, volatile=True))

        # Shift value:
        if access.bitshift:
            shift_amount = self.emit(
                ir.Const(access.bitshift, 'shift', ir_typ))
            value = self.emit(
                ir.Binop(value, '<<', shift_amount, 'value', ir_typ))

        # Clip value:
        mask = self.emit(ir.Const(mask, 'mask', ir_typ))
        value = self.emit(ir.Binop(value, '&', mask, 'value', ir_typ))

        # Clear bits for bitfield:
        inv_mask = self.emit(ir.Const(inv_mask, 'inv_mask', ir_typ))
        loaded = self.emit(ir.Binop(
            loaded, '&', inv_mask, 'loaded_masked', ir_typ))

        # Or with value
        value = self.emit(ir.Binop(loaded, '|', value, 'value', ir_typ))

        # Store modified value back:
        self.emit(ir.Store(value, access.address))

    def _get_bitfield_ir_typ(self, access, signed):
        required_bits = access.bitshift + access.bitsize
        if signed and access.signed:
            mp = {
                8: ir.i8,
                16: ir.i16,
                32: ir.i32,
                64: ir.i64,
            }
        else:
            mp = {
                8: ir.u8,
                16: ir.u16,
                32: ir.u32,
                64: ir.u64,
            }
        for b, v in mp.items():
            if required_bits <= b:
                return v
        raise NotImplementedError('Bitfields larger than 64 bits')

    def gen_unop(self, expr: expressions.UnaryOperator):
        """ Generate code for unary operator """
        if expr.op in ['x++', 'x--', '--x', '++x']:
            # Increment and decrement in pre and post form
            ir_a = self.gen_expr(expr.a, rvalue=False)
            assert expr.a.lvalue

            ir_typ = self.get_ir_type(expr.typ)
            loaded = self._load_value(ir_a, expr.typ)
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
            self._store_value(changed, ir_a)

            # Determine pre or post form:
            pre = expr.op[0] == 'x'
            if pre:
                value = loaded
            else:
                value = changed
        elif expr.op == '*':
            value = self.gen_expr(expr.a, rvalue=True)
            assert expr.lvalue
        elif expr.op == '&':
            assert expr.a.lvalue
            value = self.gen_expr(expr.a, rvalue=False)
        elif expr.op in ['-', '~']:
            a = self.gen_expr(expr.a, rvalue=True)
            ir_typ = self.get_ir_type(expr.typ)
            value = self.emit(ir.Unop(expr.op, a, 'unop', ir_typ))
        elif expr.op in ['!']:
            value = self.gen_condition_to_integer(expr)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr.op))
        return value

    def gen_binop(self, expr: expressions.BinaryOperator):
        """ Generate code for binary operation expression """
        if expr.op in ['-', '*', '/', '%', '^', '|', '&', '>>', '<<']:
            lhs = self.gen_expr(expr.a, rvalue=True)
            rhs = self.gen_expr(expr.b, rvalue=True)
            op = expr.op

            ir_typ = self.get_ir_type(expr.typ)
            value = self.emit(
                ir.Binop(lhs, op, rhs, 'op', ir_typ),
                location=expr.location)
        elif expr.op == ',':
            # Handle the comma operator by returning the second result
            self.gen_expr(expr.a, rvalue=True)
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

            if expr.op == '=':
                value = rhs
            else:
                # Handle '+=' and friends:
                op = expr.op[:-1]
                ir_typ = self.get_ir_type(expr.typ)
                loaded = self._load_value(lhs, expr.typ)
                value = self.emit(ir.Binop(
                    loaded, op, rhs, 'assign', ir_typ))
            self._store_value(value, lhs)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr.op))
        return value

    def gen_ternop(self, expr: expressions.TernaryOperator):
        """ Generate code for ternary operator a ? b : c """
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
        return value

    def gen_call(self, expr: expressions.FunctionCall):
        """ Generate code for a function call """
        if isinstance(expr.callee.typ, types.FunctionType):
            ftyp = expr.callee.typ
        else:
            ftyp = expr.callee.typ.element_type

        # Determine fixed and variable arguments:
        if ftyp.is_vararg:
            x = len(ftyp.arguments)
            fixed_args = expr.args[:x]
            var_args = expr.args[x:]
        else:
            fixed_args = expr.args
            var_args = []

        # Evaluate arguments:
        ir_arguments = []

        # If return value is complex, reserve room for it an pass pointer
        if ftyp.return_type.is_struct:
            size = self.context.sizeof(ftyp.return_type)
            alignment = self.context.alignment(ftyp.return_type)
            rval_alloc = self.emit(ir.Alloc('rval_alloc', size, alignment))
            rval_ptr = self.emit(ir.AddressOf(rval_alloc, 'rval_ptr'))
            ir_arguments.append(rval_ptr)

        # Place other arguments:
        for argument in fixed_args:
            value = self.gen_expr(argument, rvalue=True)
            ir_arguments.append(value)

        # Handle variable arguments:
        if ftyp.is_vararg:
            if not var_args:
                # Emit a null pointer when no arguments given:
                vararg_ptr = self.emit(ir.Const(0, 'varargs', ir.ptr))
                ir_arguments.append(vararg_ptr)
            else:
                # Allocate a memory slab:
                size = 0
                alignment = 1
                for va in var_args:
                    va_size = self.context.sizeof(va.typ)
                    va_alignment = self.context.alignment(va.typ)
                    # If not aligned, make it happen:
                    size += required_padding(size, va_alignment)
                    size += va_size
                    alignment = max(alignment, va_alignment)
                vararg_ptr = self.emit(ir.Alloc('varargs', size, alignment))
                vararg_ptr = self.emit(ir.AddressOf(vararg_ptr, 'vaptr'))
                # Append var arg slot:
                ir_arguments.append(vararg_ptr)

                offset = 0
                for argument in var_args:
                    value = self.gen_expr(argument, rvalue=True)
                    va_size = self.context.sizeof(argument.typ)
                    va_alignment = self.context.alignment(va.typ)

                    # handle alignment:
                    padding = required_padding(offset, va_alignment)
                    if padding > 0:
                        cnst = self.emit(ir.Const(padding, 'padding', ir.ptr))
                        vararg_ptr = self.emit(
                            ir.add(vararg_ptr, cnst, 'va2', ir.ptr))
                    offset += padding

                    # Store value:
                    self.emit(ir.Store(value, vararg_ptr))

                    # Increase pointer:
                    s2 = self.emit(ir.Const(va_size, 'size', ir.ptr))
                    offset += va_size
                    vararg_ptr = self.emit(
                        ir.add(vararg_ptr, s2, 'va2', ir.ptr))

        # Get function pointer or label:
        if isinstance(expr.callee.typ, types.FunctionType):
            # Normal call, get global value:
            ir_function = self.ir_var_map[expr.callee.variable]
        elif isinstance(expr.callee.typ, types.PointerType) and \
                isinstance(expr.callee.typ.element_type, types.FunctionType):
            ir_function = self.gen_expr(expr.callee, rvalue=True)
        else:  # pragma: no cover
            raise NotImplementedError()

        # Use function or procedure call depending on return type:
        if ftyp.return_type.is_void:
            self.emit(ir.ProcedureCall(ir_function, ir_arguments))
            value = None
        elif ftyp.return_type.is_struct:
            self.emit(ir.ProcedureCall(ir_function, ir_arguments))
            value = rval_alloc
        else:
            ir_typ = self.get_ir_type(expr.typ)
            value = self.emit(ir.FunctionCall(
                ir_function, ir_arguments, 'result', ir_typ))

        return value

    def gen_array_index(self, expr: expressions.ArrayIndex):
        """ Generate code for array indexing """
        # Load base as an rvalue, to make sure we load pointers values.
        base = self.gen_expr(expr.base, rvalue=True)
        index = self.gen_expr(expr.index, rvalue=True)

        # Generate constant for element size:
        element_type_size = self.context.sizeof(
            expr.base.typ.element_type)
        element_size = self.emit(
            ir.Const(element_type_size, 'element_size', ir.ptr),
            location=expr.location)

        # Calculate offset:
        index = self.emit(
            ir.Cast(index, 'index', ir.ptr), location=expr.location)
        offset = self.emit(
            ir.mul(index, element_size, "element_offset", ir.ptr),
            location=expr.location)

        # Calculate address:
        value = self.emit(
            ir.add(base, offset, "element_address", ir.ptr),
            location=expr.location)
        return value

    def gen_builtin(self, expr):
        """ Generate appropriate built-in functionality """
        if isinstance(expr, expressions.BuiltInVaArg):
            value = self.gen_va_arg(expr)
        elif isinstance(expr, expressions.BuiltInVaStart):
            value = self.gen_va_start(expr)
        elif isinstance(expr, expressions.BuiltInOffsetOf):
            value = self.gen_offsetof(expr)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))
        return value

    def gen_va_start(self, expr: expressions.BuiltInVaStart):
        """ Generate code for the va_start builtin """
        assert self._varargz_ptr
        # Save the arg pointer into the ap_list variable:
        va_ptr = self._varargz_ptr
        valist_ptrptr = self.gen_expr(expr.arg_pointer, rvalue=False)
        self.emit(ir.Store(va_ptr, valist_ptrptr))
        return va_ptr

    def gen_va_arg(self, expr: expressions.BuiltInVaArg):
        """ Generate code for a va_arg operation """
        valist_ptrptr = self.gen_expr(expr.arg_pointer, rvalue=False)
        va_ptr = self.emit(ir.Load(valist_ptrptr, 'va_ptr', ir.ptr))
        ir_typ = self.get_ir_type(expr.typ)
        # Load the variable argument:
        value = self.emit(ir.Load(va_ptr, 'va_arg', ir_typ))
        size = self.emit(ir.Const(
            self.context.sizeof(expr.typ), 'size', ir.ptr))
        va_ptr = self.emit(ir.add(va_ptr, size, 'incptr', ir.ptr))
        self.emit(ir.Store(va_ptr, valist_ptrptr))
        return value

    def gen_offsetof(self, expr: expressions.BuiltInOffsetOf):
        """ Generate code for offsetof """
        assert isinstance(expr.query_typ, types.StructOrUnionType)
        field = expr.query_typ.get_field(expr.member)
        offset = self.context.offsetof(expr.query_typ, field)
        ir_typ = self.get_ir_type(expr.typ)
        value = self.emit(ir.Const(offset, 'offset', ir_typ))
        return value

    def gen_sizeof(self, expr: expressions.Sizeof):
        """ Generate code for sizeof construction """
        if isinstance(expr.sizeof_typ, types.CType):
            # Get size of the given type:
            type_size = self.context.sizeof(expr.sizeof_typ)
        else:
            # And get its size:
            type_size = self.context.sizeof(expr.sizeof_typ.typ)

        ir_typ = self.get_ir_type(expr.typ)
        value = self.emit(ir.Const(type_size, 'type_size', ir_typ))
        return value

    def get_ir_type(self, typ: types.CType):
        """ Given a C type, get the fitting ir type """
        assert isinstance(typ, types.CType)

        if isinstance(typ, types.BasicType):
            return self.ir_type_map[typ.type_id][0]
        elif isinstance(typ, (types.IndexableType, types.FunctionType)):
            # Pointers and arrays are seen as pointers:
            return ir.ptr
        elif isinstance(typ, types.EnumType):
            return self.get_ir_type(self._root_scope.get_type(['int']))
        elif isinstance(typ, (types.UnionType, types.StructType)):
            size = self.context.sizeof(typ)
            alignment = self.context.alignment(typ)
            return ir.BlobDataTyp(size, alignment=alignment)
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))

    def get_debug_type(self, typ: types.CType):
        """ Get or create debug type info in the debug information """
        # Find cached values:
        if self.debug_db.contains(typ):
            return self.debug_db.get(typ)

        if isinstance(typ, types.BasicType):
            if typ.is_void:
                dbg_typ = debuginfo.DebugBaseType(
                    typ.type_id, 0, 1)
            else:
                dbg_typ = debuginfo.DebugBaseType(
                    typ.type_id, self.context.sizeof(typ), 1)
            self.debug_db.enter(typ, dbg_typ)
        elif isinstance(typ, types.EnumType):
            return self.get_debug_type(self._root_scope.get_type(['int']))
        elif isinstance(typ, types.FunctionType):
            # This is in most cases a pointer to a function type.
            # Register for now as basetype with 0 size:
            dbg_typ = debuginfo.DebugBaseType('func', 0, 1)
            self.debug_db.enter(typ, dbg_typ)
        elif isinstance(typ, types.PointerType):
            ptype = self.get_debug_type(typ.element_type)
            dbg_typ = debuginfo.DebugPointerType(ptype)
            self.debug_db.enter(typ, dbg_typ)
        elif isinstance(typ, types.StructType):
            dbg_typ = debuginfo.DebugStructType()

            # Ensure to register the type first:
            self.debug_db.enter(typ, dbg_typ)

            for field in typ.fields:
                field_typ = self.get_debug_type(field.typ)
                field_offset = self.context.offsetof(typ, field)
                dbg_typ.add_field(field.name, field_typ, field_offset)
        elif isinstance(typ, types.ArrayType):
            element_typ = self.get_debug_type(typ.element_type)
            size = self.context.eval_expr(typ.size)
            dbg_typ = debuginfo.DebugArrayType(element_typ, size)
            self.debug_db.enter(typ, dbg_typ)
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))
        return dbg_typ


class BitFieldAccess:
    """ Container object which carries bitfield access details """
    def __init__(self, address, bitshift, bitsize, signed):
        self.address = address
        self.bitshift = bitshift
        self.bitsize = bitsize
        self.signed = signed
