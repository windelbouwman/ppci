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
from ...utils.bitfun import value_to_bits, bits_to_bytes
from .eval import ConstantExpressionEvaluator


class CCodeGenerator:
    """ Converts parsed C code to ir-code """

    logger = logging.getLogger("ccodegen")

    def __init__(self, context):
        self.context = context
        self._root_scope = RootScope()
        self.builder = None
        self.debug_db = None
        self.ir_var_map = {}
        self.break_block_stack = []  # A stack of while or switch loops
        self.continue_block_stack = []  # A stack of for loops
        self.labeled_blocks = {}
        self.switch_options = None
        self.static_counter = 0  # Unique number to make static vars unique
        int_types = {2: ir.i16, 4: ir.i32, 8: ir.i64}
        uint_types = {2: ir.i16, 4: ir.u32, 8: ir.u64}
        int_size = self.context.arch_info.get_size("int")
        long_size = self.context.arch_info.get_size("long")
        self.ptr_size = self.context.arch_info.get_size("ptr")
        self.ir_type_map = {
            BasicType.CHAR: (ir.i8, 1),
            BasicType.UCHAR: (ir.u8, 1),
            BasicType.SHORT: (ir.i16, 2),
            BasicType.USHORT: (ir.u16, 2),
            BasicType.INT: (int_types[int_size], int_size),
            BasicType.UINT: (uint_types[int_size], int_size),
            BasicType.LONG: (int_types[long_size], long_size),
            BasicType.ULONG: (uint_types[long_size], long_size),
            BasicType.LONGLONG: (ir.i64, 8),
            BasicType.ULONGLONG: (ir.u64, 8),
            BasicType.FLOAT: (ir.f32, 4),
            BasicType.DOUBLE: (ir.f64, 8),
            BasicType.LONGDOUBLE: (ir.f64, 8),  # TODO: is this correct?
        }
        self._constant_evaluator = LinkTimeExpressionEvaluator(self)

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
        self.logger.debug("Generating IR-code")
        self.debug_db = debuginfo.DebugDb()
        ir_mod = ir.Module("main", debug_db=self.debug_db)
        self.builder.module = ir_mod

        # Split declaration into functions and variables:
        functions = []
        variables = []
        for declaration in compile_unit.declarations:
            assert isinstance(declaration, declarations.CDeclaration)

            if isinstance(
                declaration,
                (declarations.Typedef, declarations.EnumConstantDeclaration),
            ):
                pass
            elif isinstance(declaration, declarations.FunctionDeclaration):
                functions.append(declaration)
            elif isinstance(declaration, declarations.VariableDeclaration):
                variables.append(declaration)
            else:  # pragma: no cover
                raise NotImplementedError(str(declaration))

        # Generate code:
        for variable in variables:
            self.gen_global_variable(variable)

        for function in functions:
            self.create_function(function)

        for function in functions:
            self.gen_function(function)

        self.logger.info("Finished IR-code generation")
        return ir_mod

    def emit(self, instruction):
        """ Helper function to emit a single instruction """
        return self.builder.emit(instruction)

    def emit_alloca(self, typ):
        """ Helper function to reserve some room on the stack. """
        size, alignment = self.data_layout(typ)
        name = "alloca"
        ir_var = self.emit(ir.Alloc(name, size, alignment))
        ir_var = self.emit(ir.AddressOf(ir_var, name + "_addr"))
        return ir_var

    def emit_global_variable(self, name, binding, typ, ivalue):
        """ Helper to emit a global variable. """
        size, alignment = self.data_layout(typ)
        ir_var = ir.Variable(name, binding, size, alignment, value=ivalue)
        self.builder.module.add_variable(ir_var)
        return ir_var

    def emit_const(self, value, ctyp):
        """ Small helper to emit a constant. """
        ir_typ = self.get_ir_type(ctyp)
        return self.builder.emit_const(value, ir_typ)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message, location):
        """ Trigger an error at the given node """
        raise CompilerError(message, loc=location)

    def gen_global_variable(self, var_decl):
        """ Generate code for a global variable """
        assert isinstance(var_decl, declarations.VariableDeclaration)
        if var_decl.storage_class == "extern" and not var_decl.is_definition():
            # create an external variable:
            ir_var = ir.ExternalVariable(var_decl.name)
            self.builder.module.add_external(ir_var)
            self.ir_var_map[var_decl] = ir_var
        else:
            if var_decl.initial_value:
                ivalue = self.gen_global_ival(
                    var_decl.typ, var_decl.initial_value
                )
            else:
                ivalue = None
            name = var_decl.name
            if var_decl.storage_class == "static":
                binding = ir.Binding.LOCAL
            else:
                binding = ir.Binding.GLOBAL
            ir_var = self.emit_global_variable(
                name, binding, var_decl.typ, ivalue
            )
            self.ir_var_map[var_decl] = ir_var

    def gen_global_ival(self, typ, ival):
        """ Create memory image for initial value of global variable """
        # Check initial value type:
        if not isinstance(ival, expressions.CExpression):
            raise TypeError("ival must be an Expression")

        if isinstance(typ, types.ArrayType):
            mem = self.gen_global_initialize_array(typ, ival)
        elif isinstance(typ, types.StructType):
            mem = self.gen_global_initialize_struct(typ, ival)
        elif isinstance(typ, types.UnionType):
            mem = self.gen_global_initialize_union(typ, ival)
        elif isinstance(typ, (types.BasicType, types.PointerType)):
            mem = self.gen_global_initialize_expression(typ, ival)
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))
        assert isinstance(mem, tuple)
        return mem

    def gen_global_initialize_expression(self, typ, expr):
        """ Generate memory slab for global expression. """
        cval = self._constant_evaluator.eval_expr(expr)

        if isinstance(cval, tuple):
            assert cval[0] is ir.ptr and len(cval) == 2
            mem = (cval,)
        else:
            mem = (self.context.pack(typ, cval),)
        return mem

    def gen_global_string_constant(self, expr):
        """ Create a new global variable holding string literal data. """
        value_data = expr.to_bytes()
        amount = len(value_data)
        alignment = 1
        name = "__txt_const_{}".format(self.static_counter)
        self.static_counter += 1
        text_var = ir.Variable(
            name, ir.Binding.LOCAL, amount, alignment, value=value_data
        )
        self.builder.module.add_variable(text_var)
        return text_var

    def gen_global_compound_literal(self, expr: expressions.CompoundLiteral):
        """ Generate a global variable for a compound literal.

        See also:
        - https://en.cppreference.com/w/c/language/compound_literal
        """

        value_data = self.gen_global_ival(expr.typ, expr.init)

        # Create name:
        name = "__compound_{}".format(self.static_counter)
        self.static_counter += 1

        compound_literal_variable = self.emit_global_variable(
            name, ir.Binding.LOCAL, expr.typ, value_data
        )
        return compound_literal_variable

    def gen_global_initialize_array(self, typ, ival):
        """ Properly fill an array with initial values """
        assert isinstance(ival, expressions.ArrayInitializer)
        assert ival.typ is typ

        element_size = self.sizeof(typ.element_type)
        implicit_value = tuple([bytes([0] * element_size)])

        mem = tuple()
        for value in ival.values:
            # TODO: handle alignment
            if value is None:
                element_mem = implicit_value
            else:
                element_mem = self.gen_global_ival(typ.element_type, value)
            mem = mem + element_mem

        array_size = self.context.eval_expr(typ.size)

        if len(ival.values) < array_size:
            extra_implicit = array_size - len(ival.values)
            mem = mem + implicit_value * extra_implicit
        elif len(ival.values) > array_size:
            mem = mem[:array_size]

        return mem

    def gen_global_initialize_union(self, typ, ival):
        """ Initialize a union type """
        assert isinstance(ival, expressions.UnionInitializer)
        assert ival.typ is typ
        mem = tuple()
        # Initialize the first field!
        field = ival.field
        mem = mem + self.gen_global_ival(field.typ, ival.value)
        size = self.sizeof(typ)
        filling = size - len(mem)
        assert filling >= 0
        mem = mem + (bytes([0] * filling),)
        return mem

    def gen_global_initialize_struct(self, typ, ival):
        """ Properly fill global struct variable with content """
        assert isinstance(ival, expressions.StructInitializer)
        assert ival.typ is typ
        mem = tuple()
        bits = []  # A working list of bytes

        field_offsets = self.context.get_field_offsets(typ)[1]
        for field in typ.fields:
            if field.is_bitfield:
                # Special case for bitfields
                if field in ival.values:
                    value = ival.values[field]
                    cval = self.context.eval_expr(value)
                else:
                    cval = 0
                bitsize = self.context.eval_expr(field.bitsize)
                new_bits = value_to_bits(cval, bitsize)
                bits.extend(new_bits)
            else:
                # Flush bits:
                if bits:
                    mem = mem + (bits_to_bytes(bits),)
                    bits.clear()
                # Apply some padding:
                field_offset = field_offsets[field] // 8
                # TODO: how to handle bit fields?
                mem_len = self.mem_len(mem)
                if mem_len < field_offset:
                    padding_count = field_offset - mem_len
                    mem = mem + (bytes([0] * padding_count),)

                # Add field data, if any:
                if field in ival.values:
                    value = ival.values[field]
                    mem = mem + self.gen_global_ival(field.typ, value)
                else:
                    field_size = self.sizeof(field.typ)
                    mem = mem + (bytes([0] * field_size),)

        # Purge last remaining bits:
        if bits:
            mem = mem + (bits_to_bytes(bits),)
            bits.clear()
        return mem

    def mem_len(self, mem):
        """ Determine the bytesize of a memory slab """
        size = 0
        for part in mem:
            if isinstance(part, bytes):
                size += len(part)
            elif isinstance(part, tuple) and part[0] is ir.ptr:
                size += self.context.arch_info.get_size(part[0])
            else:  # pragma: no cover
                raise NotImplementedError(repr(part))
        return size

    def gen_function(self, function):
        """ Generate code for a function """
        if function.body:
            self.gen_function_def(function)

    def create_function(self, function):
        """ Create code for a function """
        if function.body:
            self.create_function_internal(function)
        else:
            self.create_function_external(function)

    def create_function_internal(self, function):
        """ Create the function and put it into the var_map """
        if function.storage_class == "static":
            binding = ir.Binding.LOCAL
        else:
            binding = ir.Binding.GLOBAL

        # Create ir function:
        if function.typ.return_type.is_void:
            ir_function = self.builder.new_procedure(function.name, binding)
        elif function.typ.return_type.is_struct:
            # Pass implicit first argument to function when complex type
            # is returned.
            ir_function = self.builder.new_procedure(function.name, binding)
            return_value_address = ir.Parameter("return_value_address", ir.ptr)
            ir_function.add_parameter(return_value_address)
        else:
            return_type = self.get_ir_type(function.typ.return_type)
            ir_function = self.builder.new_function(
                function.name, binding, return_type
            )
        self.ir_var_map[function] = ir_function

    def create_function_external(self, function):
        """ Create external function reference. """
        ftyp = function.typ
        argument_types = [self.get_ir_type(a.typ) for a in ftyp.arguments]

        if ftyp.is_vararg:
            argument_types.append(ir.ptr)

        if ftyp.return_type.is_void:
            external_function = ir.ExternalProcedure(
                function.name, argument_types
            )
        else:
            return_type = self.get_ir_type(ftyp.return_type)
            external_function = ir.ExternalFunction(
                function.name, argument_types, return_type
            )

        self.builder.module.add_external(external_function)
        self.ir_var_map[function] = external_function

    def gen_function_def(self, function):
        """ Generate code for a function definition """
        self.logger.debug("Generating IR-code for %s", function.name)
        assert not self.break_block_stack
        assert not self.continue_block_stack
        self.labeled_blocks = {}
        assert not self.labeled_blocks

        # Save current function for later on..
        self.current_function = function

        ir_function = self.ir_var_map[function]

        # Create entry code:
        self.builder.set_function(ir_function)
        first_block = self.builder.new_block()
        self.builder.set_block(first_block)
        ir_function.entry = first_block

        # Add arguments (create memory space for them!):
        for argument in function.typ.arguments:
            ir_typ = self.get_ir_type(argument.typ)
            if argument.name is None:
                ir_argument = ir.Parameter("anonymous", ir_typ)
                ir_function.add_parameter(ir_argument)
            else:
                ir_argument = ir.Parameter(argument.name, ir_typ)
                ir_function.add_parameter(ir_argument)
                if isinstance(ir_typ, ir.BlobDataTyp):
                    ir_var = self.emit(
                        ir.AddressOf(ir_argument, argument.name + "_addr")
                    )
                else:
                    ir_var = self.emit_alloca(argument.typ)
                    self.emit(ir.Store(ir_argument, ir_var))
                self.ir_var_map[argument] = ir_var

        # In case of a variadic function, add an extra pointer:
        if function.typ.is_vararg:
            self.logger.debug("Adding vararg pointer")
            ir_argument = ir.Parameter("varargz", ir.ptr)
            ir_function.add_parameter(ir_argument)
            self._varargz_ptr = ir_argument

        # Generate debug info for function:
        dbg_args = [
            debuginfo.DebugParameter(a.name, self.get_debug_type(a.typ))
            for a in function.typ.arguments
        ]
        dfi = debuginfo.DebugFunction(
            function.name,
            function.location,
            self.get_debug_type(function.typ.return_type),
            dbg_args,
        )

        self.debug_db.enter(ir_function, dfi)

        # Generate code for body:
        assert isinstance(function.body, statements.Compound)
        self.gen_compound_statement(function.body)

        if not self.builder.block.is_closed:
            # In case of void function, introduce exit instruction:
            if function.typ.return_type.is_void:
                self.emit(ir.Exit())
            else:
                warn_when_no_return = True
                if warn_when_no_return:
                    self.warning("Function does not return a value")
                    zero = self.emit_const(0, function.typ.return_type)
                    self.emit(ir.Return(zero))
                else:
                    self.error(
                        "Function does not return an {}".format(
                            function.typ.return_type
                        ),
                        function,
                    )

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
            statements.RangeCase: self.gen_range_case,
            statements.Default: self.gen_default,
            statements.Empty: self.gen_empty_statement,
            statements.Compound: self.gen_compound_statement,
            statements.InlineAssemblyCode: self.gen_inline_assembly,
            statements.ExpressionStatement: self.gen_expression_statement,
            statements.DeclarationStatement: self.gen_declaration_statement,
        }
        if type(statement) in fn_map:
            with self.builder.use_location(statement.location):
                fn_map[type(statement)](statement)
        else:  # pragma: no cover
            raise NotImplementedError(str(statement))

    def gen_empty_statement(self, statement) -> None:
        """ Generate code for empty statement """
        pass

    def gen_compound_statement(self, statement) -> None:
        """ Generate code for a compound statement """
        for inner_statement in statement.statements:
            self.gen_stmt(inner_statement)

    def gen_declaration_statement(self, statement):
        """ Generate code for a declaration statement """
        declaration = statement.declaration
        if isinstance(declaration, declarations.VariableDeclaration):
            if declaration.storage_class == "static":
                self.gen_local_static_variable(declaration)
            else:
                self.gen_local_variable(declaration)
        else:
            raise NotImplementedError(str(declaration))

    def gen_local_static_variable(self, var_decl):
        """ Generate code for a local static variable. """
        if var_decl.initial_value:
            ivalue = self.gen_global_ival(var_decl.typ, var_decl.initial_value)
        else:
            ivalue = None
        name = "{}_{}".format(var_decl.name, self.static_counter)
        self.static_counter += 1

        binding = ir.Binding.LOCAL
        ir_var = self.emit_global_variable(name, binding, var_decl.typ, ivalue)
        self.ir_var_map[var_decl] = ir_var

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
        self.builder.emit_jump(final_block)
        if stmt.no:
            self.builder.set_block(no_block)
            self.gen_stmt(stmt.no)
            self.builder.emit_jump(final_block)
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
        self.builder.emit_jump(test_block)

        # Implement the switch body:
        self.break_block_stack.append(final_block)
        self.builder.set_block(body_block)
        self.gen_stmt(stmt.statement)
        self.builder.emit_jump(final_block)
        self.break_block_stack.pop(-1)

        # Implement switching logic, now that we have the branches:
        # TODO: implement jump tables and other performance related stuff.
        self.builder.set_block(test_block)
        test_value = self.gen_expr(stmt.expression, rvalue=True)
        switch_ir_typ = self.get_ir_type(stmt.expression.typ)
        for option, target_block in self.switch_options.items():
            if option != "default":
                option = self.builder.emit_const(option, switch_ir_typ)
                next_test_block = self.builder.new_block()
                self.emit(
                    ir.CJump(
                        test_value, "==", option, target_block, next_test_block
                    )
                )
                self.builder.set_block(next_test_block)

        # If all else fails, jump to the default case if we have it.
        target_block = self.switch_options.get("default", final_block)
        self.builder.emit_jump(target_block)

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
        self.builder.emit_jump(condition_block)
        self.builder.set_block(condition_block)
        self.gen_condition(stmt.condition, body_block, final_block)
        self.builder.set_block(body_block)
        self.gen_stmt(stmt.body)
        self.builder.emit_jump(condition_block)
        self.builder.set_block(final_block)
        self.break_block_stack.pop(-1)
        self.continue_block_stack.pop(-1)

    def gen_do_while(self, stmt: statements.DoWhile) -> None:
        """ Generate do-while-statement code """
        body_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.break_block_stack.append(final_block)
        self.continue_block_stack.append(body_block)
        self.builder.emit_jump(body_block)
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
            if isinstance(stmt.init, declarations.VariableDeclaration):
                self.gen_local_variable(stmt.init)
            else:
                self.gen_expr(stmt.init, rvalue=True)
        self.builder.emit_jump(condition_block)
        self.builder.set_block(condition_block)
        if stmt.condition:
            self.gen_condition(stmt.condition, body_block, final_block)
        else:
            self.builder.emit_jump(body_block)
        self.builder.set_block(body_block)
        self.gen_stmt(stmt.body)
        if stmt.post:
            self.gen_expr(stmt.post, rvalue=True)
        self.builder.emit_jump(condition_block)
        self.builder.set_block(final_block)
        self.break_block_stack.pop(-1)
        self.continue_block_stack.pop(-1)

    def gen_label(self, stmt: statements.Label) -> None:
        """ Generate code for a label """
        block = self.get_label_block(stmt.name)
        self.builder.emit_jump(block)  # fall through
        self.builder.set_block(block)
        self.gen_stmt(stmt.statement)

    def gen_case(self, stmt: statements.Case) -> None:
        """ Generate code for case label inside a switch statement """
        block = self.builder.new_block()
        assert self.switch_options is not None
        value = self.context.eval_expr(stmt.value)
        if value in self.switch_options:
            self.error("Case defined multiple times", stmt.location)
        self.switch_options[value] = block
        self.builder.emit_jump(block)  # fall through
        self.builder.set_block(block)
        self.gen_stmt(stmt.statement)

    def gen_range_case(self, stmt: statements.Case) -> None:
        """ Generate code for range case label inside a switch statement """
        block = self.builder.new_block()
        assert self.switch_options is not None
        # TODO: This could lead to a very big if-then-else chain?
        value1 = self.context.eval_expr(stmt.value1)
        value2 = self.context.eval_expr(stmt.value2)
        for value in range(value1, value2 + 1):
            if value in self.switch_options:
                self.error("Case defined multiple times", stmt.location)
            self.switch_options[value] = block

        self.builder.emit_jump(block)  # fall through
        self.builder.set_block(block)
        self.gen_stmt(stmt.statement)

    def gen_default(self, stmt: statements.Default) -> None:
        """ Generate code for case label inside a switch statement """
        block = self.builder.new_block()
        assert self.switch_options is not None
        self.switch_options["default"] = block
        self.builder.emit_jump(block)  # fall through
        self.builder.set_block(block)
        self.gen_stmt(stmt.statement)

    def gen_goto(self, stmt: statements.Goto) -> None:
        """ Generate code for a goto statement """
        block = self.get_label_block(stmt.label)
        self.builder.emit_jump(block)
        new_block = self.builder.new_block()
        self.builder.set_block(new_block)

    def gen_continue(self, stmt: statements.Continue) -> None:
        """ Generate code for the continue statement """
        # block = self.get_label_block(stmt.label)
        if self.continue_block_stack:
            block = self.continue_block_stack[-1]
            self.builder.emit_jump(block)
        else:
            self.error("Cannot continue here!", stmt)
        new_block = self.builder.new_block()
        self.builder.set_block(new_block)

    def gen_break(self, stmt: statements.Break) -> None:
        """ Generate code to break out of something. """
        # block = self.get_label_block(stmt.label)
        if self.break_block_stack:
            block = self.break_block_stack[-1]
            self.builder.emit_jump(block)
        else:
            self.error("Cannot break here!", stmt)
        new_block = self.builder.new_block()
        self.builder.set_block(new_block)

    def gen_return(self, stmt: statements.Return) -> None:
        """ Generate return statement code """
        if stmt.value:
            if stmt.value.typ.is_struct:
                # Complex types are copied to pointer passed as
                # first argument.
                value = self.gen_expr(stmt.value, rvalue=True)
                return_value_address = self.builder.function.arguments[0]
                assert return_value_address.name == "return_value_address"
                self.emit(ir.Store(value, return_value_address))
                # self.emit(ir.CopyBlob(self.return_value_address))
                self.builder.emit_exit()
            else:
                # Simple types are returned via ir-value.
                value = self.gen_expr(stmt.value, rvalue=True)
                self.builder.emit_return(value)
        else:
            self.builder.emit_exit()
        new_block = self.builder.new_block()
        self.builder.set_block(new_block)

    def gen_inline_assembly(self, stmt):
        """ Generate code for inline assembly. """
        inline_asm = ir.InlineAsm(stmt.template, stmt.clobbers)

        # First load, all asm operands:
        for _, asm_input_expr in stmt.input_operands:
            asm_input_ir = self.gen_expr(asm_input_expr, rvalue=True)
            inline_asm.add_input_variable(asm_input_ir)

        # Emit inline assembly:
        self.emit(inline_asm)

        # Store asm outputs:
        for asm_output_expr in stmt.output_operands:
            # asm_input_ir = self.gen_expr(asm_input_expr, rvalue=True)
            # Ouch, we cannot have an ir-node with more than a single
            # output value ...
            # inline_asm.add_def(asm_input_ir)
            raise NotImplementedError()

    def gen_condition(self, condition, yes_block, no_block):
        """ Generate switch based on condition. """
        if isinstance(condition, expressions.BinaryOperator):
            if condition.op == "||":
                middle_block = self.builder.new_block()
                self.gen_condition(condition.a, yes_block, middle_block)
                self.builder.set_block(middle_block)
                self.gen_condition(condition.b, yes_block, no_block)
            elif condition.op == "&&":
                middle_block = self.builder.new_block()
                self.gen_condition(condition.a, middle_block, no_block)
                self.builder.set_block(middle_block)
                self.gen_condition(condition.b, yes_block, no_block)
            elif condition.op in ["<", ">", "==", "!=", "<=", ">="]:
                lhs = self.gen_expr(condition.a, rvalue=True)
                rhs = self.gen_expr(condition.b, rvalue=True)
                op_map = {
                    ">": ">",
                    "<": "<",
                    "==": "==",
                    "!=": "!=",
                    "<=": "<=",
                    ">=": ">=",
                }
                op = op_map[condition.op]
                self.emit(ir.CJump(lhs, op, rhs, yes_block, no_block))
            else:
                self.check_non_zero(condition, yes_block, no_block)
        elif isinstance(condition, expressions.UnaryOperator):
            if condition.op == "!":
                # Simply swap yes and no here!
                self.gen_condition(condition.a, no_block, yes_block)
            else:
                self.check_non_zero(condition, yes_block, no_block)
        else:
            self.check_non_zero(condition, yes_block, no_block)

    def check_non_zero(self, expr, yes_block, no_block):
        """ Check an expression for being non-zero """
        value = self.gen_expr(expr, rvalue=True)
        zero = self.emit_const(0, expr.typ)
        self.emit(ir.CJump(value, "==", zero, no_block, yes_block))

    def gen_local_variable(self, variable: declarations.VariableDeclaration):
        """ Generate a local variable """
        ir_addr = self.emit_alloca(variable.typ)
        self.ir_var_map[variable] = ir_addr
        if variable.initial_value:
            # Initialize local variable by a sequence of assignments.
            self.gen_local_init(ir_addr, variable.typ, variable.initial_value)

    def gen_local_init(self, ptr, typ, expr):
        """ Initialize a local slab of memory with an initial value """
        if isinstance(typ, (BasicType, types.PointerType, types.EnumType)):
            value = self.gen_expr(expr, rvalue=True)
            self._store_value(value, ptr)
            inc = self.sizeof(typ)
            ptr = self.builder.emit_add(ptr, inc, ir.ptr)
        elif isinstance(typ, types.ArrayType):
            ptr, inc = self.gen_local_init_array(ptr, typ, expr)
        elif isinstance(typ, types.StructType):
            ptr, inc = self.gen_local_init_struct(ptr, typ, expr)
        elif isinstance(typ, types.UnionType):
            ptr, inc = self.gen_local_init_union(ptr, typ, expr)
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))
        return ptr, inc

    def gen_local_init_union(self, ptr, typ, expr):
        """ Initialize a union type local variable """
        assert isinstance(expr, expressions.UnionInitializer)
        assert expr.typ is typ

        # Initialize the first field!
        field = expr.field
        ivalue = expr.value
        ptr, inc = self.gen_local_init(ptr, field.typ, ivalue)
        # Update pointer with size of union:
        # inc = self.context.sizeof(typ)
        # size = self.emit(ir.Const(inc, 'size', ir.ptr))
        # ptr = self.emit(ir.add(ptr, size, 'iptr', ir.ptr))
        return ptr, inc

    def gen_local_init_array(
        self, ptr, typ, expr: expressions.ArrayInitializer
    ):
        assert isinstance(expr, expressions.ArrayInitializer)
        inc = 0
        for value in expr.values:
            # TODO: do array elements need to be aligned?
            if value is None:
                # Implicit value (a hole between other valid values.)
                pad_inc = self.sizeof(typ.element_type)
                ptr = self.builder.emit_add(ptr, pad_inc, ir.ptr)
                inc2 = pad_inc
            else:
                ptr, inc2 = self.gen_local_init(ptr, typ.element_type, value)
            inc += inc2
        return ptr, inc

    def gen_local_init_struct(self, ptr, typ, expr):
        """ Fill structure with initializer (at runtime) """
        if isinstance(expr, expressions.StructInitializer):
            # Initializing with initialization values
            assert expr.typ is typ
            size, field_offsets = self.context.get_field_offsets(typ)
            offset = 0
            for field in typ.fields:
                # Move further in struct by whole bytes:
                field_offset = field_offsets[field] // 8
                if offset < field_offset:
                    pad_inc = field_offset - offset
                    ptr = self.builder.emit_add(ptr, pad_inc, ir.ptr)
                    offset += pad_inc

                # Fill position:
                if field.is_bitfield:  # Bit field special case!
                    if field in expr.values:
                        value = expr.values[field]
                        value = self.gen_expr(value, rvalue=True)
                        bitsize = self.context.eval_expr(field.bitsize)
                        bitshift = field_offsets[field] % 8
                        signed = field.typ.is_signed
                        access = BitFieldAccess(ptr, bitshift, bitsize, signed)
                        self._store_bitfield(value, access)
                    # TODO: how much to increase now?
                    inc2 = 0
                else:
                    if field in expr.values:
                        value = expr.values[field]
                        ptr, inc2 = self.gen_local_init(ptr, field.typ, value)
                    else:
                        pad_inc = self.sizeof(field.typ)
                        ptr = self.builder.emit_add(ptr, pad_inc, ir.ptr)
                        inc2 = pad_inc
                offset += inc2

            # Fill last padding space:
            if offset < size:
                pad_inc = size - offset
                ptr = self.builder.emit_add(ptr, pad_inc, ir.ptr)
                offset += pad_inc
            inc = offset
            assert inc == size
        else:
            # Store result of function!
            value = self.gen_expr(expr, rvalue=True)
            self.emit(ir.Store(value, ptr))
            inc = value.ty.size
        return ptr, inc

    def gen_condition_to_integer(self, expr):
        """ Generate code that takes a boolean and convert it to integer """
        yes_block = self.builder.new_block()
        no_block = self.builder.new_block()
        end_block = self.builder.new_block()

        self.gen_condition(expr, yes_block, no_block)

        self.builder.set_block(yes_block)
        yes_value = self.emit_const(1, expr.typ)
        self.builder.emit_jump(end_block)

        self.builder.set_block(no_block)
        no_value = self.emit_const(0, expr.typ)
        self.builder.emit_jump(end_block)

        self.builder.set_block(end_block)
        ir_typ = self.get_ir_type(expr.typ)
        value = self.emit(ir.Phi("phi", ir_typ))
        value.set_incoming(yes_block, yes_value)
        value.set_incoming(no_block, no_value)
        return value

    def gen_expr(self, expr, rvalue=False):
        """ Generate code for an expression.

        rvalue: if True, then the result of the expression will be an rvalue.
        """
        assert isinstance(expr, expressions.CExpression), str(expr)

        with self.builder.use_location(expr.location):
            if isinstance(expr, expressions.UnaryOperator):
                value = self.gen_unop(expr)
            elif isinstance(expr, expressions.BinaryOperator):
                value = self.gen_binop(expr)
            elif isinstance(expr, expressions.TernaryOperator):
                value = self.gen_ternop(expr)
            elif isinstance(expr, expressions.VariableAccess):
                value = self.gen_variable_access(expr)
            elif isinstance(expr, expressions.FunctionCall):
                value = self.gen_call(expr)
            elif isinstance(expr, expressions.StringLiteral):
                value = self.gen_string_literal(expr)
            elif isinstance(expr, expressions.CharLiteral):
                value = self.gen_char_literal(expr)
            elif isinstance(expr, expressions.NumericLiteral):
                value = self.gen_numeric_literal(expr)
            elif isinstance(expr, expressions.CompoundLiteral):
                value = self.gen_compound_literal(expr)
            elif isinstance(expr, expressions.InitializerList):
                self.error("Illegal initializer list", expr.location)
            elif isinstance(expr, expressions.Cast):
                value = self.gen_cast(expr)
            elif isinstance(expr, expressions.Sizeof):
                value = self.gen_sizeof(expr)
            elif isinstance(expr, expressions.FieldSelect):
                value = self.gen_field_select(expr)
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
            value = self._load_value(value, expr.typ)

        elif not rvalue:
            assert expr.lvalue
        return value

    def _load_value(self, lvalue, ctyp):
        """ Load a value from given l-value """

        if ctyp.is_array:
            value = lvalue
        else:
            # TODO: inject evil bitfield manipulation code here:
            # self.logger.debug('Non-Array type is indexed %s', expr)
            ir_typ = self.get_ir_type(ctyp)
            if isinstance(ir_typ, ir.BlobDataTyp):
                # If we have a blob pointer and want its content
                # We must get the source of the address of:
                if isinstance(lvalue, ir.AddressOf):
                    value = lvalue.src
                else:
                    # This code is debatable, allocate new storage and copy
                    # the data over there?
                    value = self.emit(
                        ir.Alloc("load_blob", ir_typ.size, ir_typ.alignment)
                    )
                    value_ptr = self.emit(ir.AddressOf(value, "value_ptr"))
                    self.gen_copy_struct(value_ptr, lvalue, ir_typ.size)
            elif isinstance(lvalue, BitFieldAccess):
                value = self._load_bitfield(lvalue, ir_typ)
            else:
                value = self.builder.emit_load(lvalue, ir_typ)
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
        loaded = self.builder.emit_load(access.address, ir_typ)

        if access.signed:
            # Shift left, then right, this to ensure sign extension
            assert loaded.ty.is_signed
            left_shift = full_bitsize - access.bitshift - access.bitsize
            right_shift = access.bitshift + left_shift
            value = self.builder.emit_binop(loaded, "<<", left_shift, ir_typ)
            value = self.builder.emit_binop(value, ">>", right_shift, ir_typ)
        else:
            assert not loaded.ty.is_signed
            mask = ((1 << access.bitsize) - 1) << access.bitshift
            value = self.builder.emit_binop(loaded, "&", mask, ir_typ)

            # Shift value:
            if access.bitshift:
                value = self.builder.emit_binop(
                    value, ">>", access.bitshift, ir_typ
                )

        # Finally convert to target type:
        if value.ty is not target_ir_typ:
            value = self.builder.emit_cast(value, target_ir_typ)

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
            value = self.builder.emit_cast(value, ir_typ)

        # Load memory value:
        # TODO: volatile used to enforce struct in memory.
        # Should not be required?
        loaded = self.builder.emit_load(access.address, ir_typ, volatile=True)

        # Shift value:
        if access.bitshift:
            value = self.builder.emit_binop(
                value, "<<", access.bitshift, ir_typ
            )

        # Clip value:
        value = self.builder.emit_binop(value, "&", mask, ir_typ)

        # Clear bits for bitfield:
        loaded = self.builder.emit_binop(loaded, "&", inv_mask, ir_typ)

        # Or with value
        value = self.builder.emit_binop(loaded, "|", value, ir_typ)

        # Store modified value back:
        self.emit(ir.Store(value, access.address))

    def _get_bitfield_ir_typ(self, access, signed):
        required_bits = access.bitshift + access.bitsize
        if signed and access.signed:
            mp = {8: ir.i8, 16: ir.i16, 32: ir.i32, 64: ir.i64}
        else:
            mp = {8: ir.u8, 16: ir.u16, 32: ir.u32, 64: ir.u64}
        for b, v in mp.items():
            if required_bits <= b:
                return v
        raise NotImplementedError("Bitfields larger than 64 bits")

    def gen_char_literal(self, expr):
        """ Generate code for a char literal. """
        return self.emit_const(expr.value, expr.typ)

    def gen_string_literal(self, expr):
        """ Generate code for a string literal. """
        data = expr.to_bytes()
        value = self.emit(ir.LiteralData(data, "cstr"))
        value = self.emit(ir.AddressOf(value, "dptr"))
        return value

    def gen_numeric_literal(self, expr):
        """ Compile a numeric literal. """
        return self.emit_const(expr.value, expr.typ)

    def gen_unop(self, expr: expressions.UnaryOperator):
        """ Generate code for unary operator """
        if expr.op in ["x++", "x--", "--x", "++x"]:
            # Increment and decrement in pre and post form
            # Determine increment or decrement:
            op = expr.op[1]
            pre = expr.op[0] == "x"
            value = self.gen_inplace_mutation(expr, op, pre)
        elif expr.op == "*":
            value = self.gen_expr(expr.a, rvalue=True)
            assert expr.lvalue
        elif expr.op == "&":
            assert expr.a.lvalue
            value = self.gen_expr(expr.a, rvalue=False)
        elif expr.op in ["-", "~"]:
            a = self.gen_expr(expr.a, rvalue=True)
            ir_typ = self.get_ir_type(expr.typ)
            value = self.emit(ir.Unop(expr.op, a, "unop", ir_typ))
        elif expr.op in ["!"]:
            value = self.gen_condition_to_integer(expr)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr.op))
        return value

    def gen_inplace_mutation(self, expr, op, pre):
        """ Generate code for x++ or --y. """
        ir_a = self.gen_expr(expr.a, rvalue=False)
        assert expr.a.lvalue

        ir_typ = self.get_ir_type(expr.typ)
        loaded = self._load_value(ir_a, expr.typ)
        # for pointers, this is not one, but sizeof
        if isinstance(expr.typ, types.PointerType):
            one = self.sizeof(expr.typ.element_type)
        else:
            one = 1

        changed = self.builder.emit_binop(loaded, op, one, ir_typ)
        self._store_value(changed, ir_a)

        # Determine pre or post form:
        value = loaded if pre else changed
        return value

    def gen_binop(self, expr: expressions.BinaryOperator):
        """ Generate code for binary operation expression """
        if expr.op in ["-", "*", "/", "%", "^", "|", "&", ">>", "<<"]:
            lhs = self.gen_expr(expr.a, rvalue=True)
            rhs = self.gen_expr(expr.b, rvalue=True)
            op = expr.op

            ir_typ = self.get_ir_type(expr.typ)
            value = self.builder.emit_binop(lhs, op, rhs, ir_typ)
        elif expr.op == ",":
            # Handle the comma operator by returning the second result
            self.gen_expr(expr.a, rvalue=True)
            rhs = self.gen_expr(expr.b, rvalue=True)
            value = rhs
        elif expr.op in ["+"]:
            lhs = self.gen_expr(expr.a, rvalue=True)
            rhs = self.gen_expr(expr.b, rvalue=True)
            # Handle pointer arithmatic!
            # Pointer arithmatic is an old artifact from the days
            # when an integer refered always to a array cell!
            if isinstance(expr.a.typ, types.IndexableType):
                # TODO: assert is_integer(expr.b.typ)
                esize = self.sizeof(expr.a.typ.element_type)
                rhs = self.builder.emit_mul(rhs, esize, rhs.ty)
                rhs = self.builder.emit_cast(rhs, ir.ptr)
            elif isinstance(expr.b.typ, types.IndexableType):
                # TODO: assert is_integer(expr.a.typ)
                esize = self.sizeof(expr.b.typ.element_type)
                lhs = self.builder.emit_mul(lhs, esize, lhs.ty)
                lhs = self.builder.emit_cast(lhs, ir.ptr)
            else:
                pass

            op = expr.op

            ir_typ = self.get_ir_type(expr.typ)
            value = self.builder.emit_binop(lhs, op, rhs, ir_typ)
        elif expr.op in ["<", ">", "==", "!=", "<=", ">=", "||", "&&"]:
            value = self.gen_condition_to_integer(expr)
        elif expr.op in [
            "=",
            "+=",
            "-=",
            "*=",
            "%=",
            "/=",
            ">>=",
            "<<=",
            "&=",
            "|=",
            "~=",
            "^=",
        ]:
            # Handle struct assignment special case:
            if expr.op == "=" and expr.a.typ.is_struct:
                lhs = self.gen_expr(expr.a, rvalue=False)
                rhs = self.gen_expr(expr.b, rvalue=False)
                amount = self.sizeof(expr.a.typ)
                self.gen_copy_struct(lhs, rhs, amount)
                value = None
            else:
                lhs = self.gen_expr(expr.a, rvalue=False)
                rhs = self.gen_expr(expr.b, rvalue=True)

                if expr.op == "=":
                    value = rhs
                else:
                    # Handle '+=' and friends:
                    op = expr.op[:-1]
                    ir_typ = self.get_ir_type(expr.typ)
                    loaded = self._load_value(lhs, expr.typ)
                    value = self.builder.emit_binop(loaded, op, rhs, ir_typ)
                self._store_value(value, lhs)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr.op))
        return value

    def gen_copy_struct(self, dst, src, amount):
        """ Generate a copy struct action. """
        self.emit(ir.CopyBlob(dst, src, amount))

    def gen_ternop(self, expr: expressions.TernaryOperator):
        """ Generate code for ternary operator a ? b : c """
        if expr.op in ["?"]:
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
            self.builder.emit_jump(end_block)

            # The false path:
            self.builder.set_block(no_block)
            no_value = self.gen_expr(expr.c, rvalue=True)
            final_no_block = self.builder.block
            self.builder.emit_jump(end_block)

            self.builder.set_block(end_block)
            if expr.typ.is_void:
                assert yes_value is None
                assert no_value is None
                value = None
            else:
                ir_typ = self.get_ir_type(expr.typ)
                value = self.emit(ir.Phi("phi", ir_typ))
                value.set_incoming(final_yes_block, yes_value)
                value.set_incoming(final_no_block, no_value)
        else:  # pragma: no cover
            raise NotImplementedError(str(expr.op))
        return value

    def gen_variable_access(self, expr: expressions.VariableAccess):
        """ Generate code for accessing a variable. """
        declaration = expr.variable.declaration
        if isinstance(
            declaration,
            (
                declarations.VariableDeclaration,
                declarations.ParameterDeclaration,
                declarations.ConstantDeclaration,
                declarations.FunctionDeclaration,
            ),
        ):
            value = self.ir_var_map[declaration]
        elif isinstance(declaration, declarations.EnumConstantDeclaration):
            # Enum value declaration!
            constant_value = self.context.get_enum_value(
                declaration.typ, declaration
            )
            value = self.emit_const(constant_value, expr.typ)
        else:  # pragma: no cover
            raise NotImplementedError(str(declaration))
        return value

    def gen_call(self, expr: expressions.FunctionCall):
        """ Generate code for a function call """
        assert expr.callee.typ.is_pointer
        ftyp = expr.callee.typ.element_type
        assert isinstance(ftyp, types.FunctionType)

        ir_arguments, rval_alloc = self.prepare_arguments(ftyp, expr.args)

        callee = self.gen_expr(expr.callee, rvalue=True)

        # Use function or procedure call depending on return type:
        if ftyp.return_type.is_void:
            self.emit(ir.ProcedureCall(callee, ir_arguments))
            value = None
        elif ftyp.return_type.is_struct:
            self.emit(ir.ProcedureCall(callee, ir_arguments))
            value = rval_alloc
        else:
            ir_typ = self.get_ir_type(expr.typ)
            value = self.emit(
                ir.FunctionCall(callee, ir_arguments, "result", ir_typ)
            )

        return value

    def prepare_arguments(self, ftyp, args):
        """ Generate code to evaluate arguments. """
        # Determine fixed and variable arguments:
        if ftyp.is_vararg:
            fixed_amount = len(ftyp.arguments)
            fixed_args = args[:fixed_amount]
            var_args = args[fixed_amount:]
        else:
            fixed_args = args
            var_args = []

        # Evaluate arguments:
        ir_arguments = []

        # If return value is complex, reserve room for it an pass pointer
        if ftyp.return_type.is_struct:
            size, alignment = self.data_layout(ftyp.return_type)
            rval_alloc = self.emit(ir.Alloc("rval_alloc", size, alignment))
            rval_ptr = self.emit(ir.AddressOf(rval_alloc, "rval_ptr"))
            ir_arguments.append(rval_ptr)
        else:
            rval_alloc = None

        # Place other arguments:
        for argument in fixed_args:
            value = self.gen_expr(argument, rvalue=True)
            ir_arguments.append(value)

        # Handle variable arguments:
        if ftyp.is_vararg:
            vararg_ptr = self.gen_fill_varargs(var_args)
            ir_arguments.append(vararg_ptr)
        else:
            assert not var_args

        return ir_arguments, rval_alloc

    def gen_fill_varargs(self, var_args):
        """ Generate code to fill variable arguments.

        This method takes a list of variable arguments, and returns a
        pointer to an allocated memory slab.
        """
        if var_args:
            # Allocate a memory slab:
            size = 0
            alignment = 1
            for va in var_args:
                va_size, va_alignment = self.data_layout(va.typ)
                # If not aligned, make it happen:
                size += required_padding(size, va_alignment)
                size += va_size
                alignment = max(alignment, va_alignment)
            vararg_alloc = self.emit(ir.Alloc("varargs", size, alignment))
            vararg_ptr = self.emit(ir.AddressOf(vararg_alloc, "vaptr"))
            vararg_ptr2 = vararg_ptr

            offset = 0
            for argument in var_args:
                value = self.gen_expr(argument, rvalue=True)
                va_size, va_alignment = self.data_layout(argument.typ)

                # handle alignment:
                padding = required_padding(offset, va_alignment)
                if padding > 0:
                    offset += padding
                    vararg_ptr2 = self.builder.emit_add(
                        vararg_ptr2, padding, ir.ptr
                    )

                # Store value:
                self.emit(ir.Store(value, vararg_ptr2))

                # Increase pointer:
                offset += va_size
                vararg_ptr2 = self.builder.emit_add(
                    vararg_ptr2, va_size, ir.ptr
                )
        else:
            # Emit a null pointer when no arguments given:
            vararg_ptr = self.emit(ir.Const(0, "varargs", ir.ptr))

        return vararg_ptr

    def gen_compound_literal(self, expr: expressions.CompoundLiteral):
        """ Generate code for a compound literal data """
        # Alloc some room:
        ir_addr = self.emit_alloca(expr.typ)
        # ... and fill compound literal:
        self.gen_local_init(ir_addr, expr.typ, expr.init)
        return ir_addr

    def gen_field_select(self, expr: expressions.FieldSelect):
        """ Generate code for field select operation. """
        base = self.gen_expr(expr.base, rvalue=False)
        field_offsets = self.context.get_field_offsets(expr.base.typ)[1]
        offset = field_offsets[expr.field]
        if expr.field.is_bitfield:
            offset, bitshift = offset // 8, offset % 8
            value = self.builder.emit_add(base, offset, ir.ptr)
            bitsize = self.context.eval_expr(expr.field.bitsize)
            signed = expr.field.typ.is_signed
            value = BitFieldAccess(value, bitshift, bitsize, signed)
        else:
            assert offset % 8 == 0
            offset //= 8
            value = self.builder.emit_add(base, offset, ir.ptr)
        return value

    def gen_array_index(self, expr: expressions.ArrayIndex):
        """ Generate code for array indexing """
        # Load base as an rvalue, to make sure we load pointers values.
        base = self.gen_expr(expr.base, rvalue=True)
        index = self.gen_expr(expr.index, rvalue=True)

        # Calculate offset:
        element_size = self.sizeof(expr.base.typ.element_type)
        index = self.builder.emit_cast(index, ir.ptr)
        offset = self.builder.emit_mul(index, element_size, ir.ptr)

        # Calculate address:
        return self.builder.emit_add(base, offset, ir.ptr)

    def gen_builtin(self, expr: expressions.BuiltIn):
        """ Generate appropriate built-in functionality """
        if isinstance(expr, expressions.BuiltInVaArg):
            value = self.gen_va_arg(expr)
        elif isinstance(expr, expressions.BuiltInVaStart):
            value = self.gen_va_start(expr)
        elif isinstance(expr, expressions.BuiltInVaCopy):
            value = self.gen_va_copy(expr)
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
        # TODO: how to deal with proper alignment?
        valist_ptrptr = self.gen_expr(expr.arg_pointer, rvalue=False)
        va_ptr = self.emit(ir.Load(valist_ptrptr, "va_ptr", ir.ptr))
        ir_typ = self.get_ir_type(expr.typ)
        # Load the variable argument:
        value = self.emit(ir.Load(va_ptr, "va_arg", ir_typ))
        size = self.emit(ir.Const(self.sizeof(expr.typ), "size", ir.ptr))
        va_ptr = self.emit(ir.add(va_ptr, size, "incptr", ir.ptr))
        self.emit(ir.Store(va_ptr, valist_ptrptr))
        return value

    def gen_va_copy(self, expr: expressions.BuiltInVaCopy):
        """ Generate code for the va_copy builtin """
        # Fetch source va_list
        valist_ptrptr = self.gen_expr(expr.src, rvalue=False)
        va_ptr = self.emit(ir.Load(valist_ptrptr, "va_ptr", ir.ptr))

        # Save the arg pointer into the ap_list variable:
        valist_ptrptr = self.gen_expr(expr.dest, rvalue=False)
        self.emit(ir.Store(va_ptr, valist_ptrptr))

    def gen_offsetof(self, expr: expressions.BuiltInOffsetOf):
        """ Generate code for offsetof """
        assert isinstance(expr.query_typ, types.StructOrUnionType)
        field = expr.query_typ.get_field(expr.member)
        offset = self.context.offsetof(expr.query_typ, field)
        value = self.emit_const(offset, expr.typ)
        return value

    def gen_cast(self, expr: expressions.Cast):
        """ Generate code for casting operation. """
        if expr.is_array_decay():
            # Pointer decay!
            # assert expr.expr.lvalue
            value = self.gen_expr(expr.expr, rvalue=True)
            # if expr.expr.lvalue:
            #    value = self.emit(ir.AddressOf(value, "decay_ptr"))
        else:
            value = self.gen_expr(expr.expr, rvalue=True)

        # In some cases we do not need to emit a cast instruction:
        if expr.to_typ.is_pointer and isinstance(
            expr.expr.typ, types.FunctionType
        ):
            value
        elif expr.to_typ.is_void:
            value = None
        else:
            ir_typ = self.get_ir_type(expr.to_typ)
            value = self.builder.emit_cast(value, ir_typ)
        return value

    def gen_sizeof(self, expr: expressions.Sizeof):
        """ Generate code for sizeof construction """
        if isinstance(expr.sizeof_typ, types.CType):
            # Get size of the given type:
            type_size = self.sizeof(expr.sizeof_typ)
        else:
            # And get its size:
            type_size = self.sizeof(expr.sizeof_typ.typ)

        return self.emit_const(type_size, expr.typ)

    def get_ir_type(self, typ: types.CType):
        """ Given a C type, get the fitting ir type """
        assert isinstance(typ, types.CType)

        if isinstance(typ, types.BasicType):
            return self.ir_type_map[typ.type_id][0]
        elif isinstance(typ, (types.IndexableType, types.FunctionType)):
            # Pointers and arrays are seen as pointers:
            return ir.ptr
        elif isinstance(typ, types.EnumType):
            return self.get_ir_type(self._root_scope.get_type(["int"]))
        elif isinstance(typ, (types.UnionType, types.StructType)):
            size, alignment = self.data_layout(typ)
            return ir.BlobDataTyp(size, alignment=alignment)
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))

    def data_layout(self, typ: types.CType):
        """ Get size and alignment of the given type. """
        size = self.sizeof(typ)
        alignment = self.context.alignment(typ)
        return size, alignment

    def sizeof(self, typ):
        """ Return the size of the given type. """
        return self.context.sizeof(typ)

    def get_debug_type(self, typ: types.CType):
        """ Get or create debug type info in the debug information """
        # Find cached values:
        if self.debug_db.contains(typ):
            return self.debug_db.get(typ)

        if isinstance(typ, types.BasicType):
            if typ.is_void:
                dbg_typ = debuginfo.DebugBaseType(typ.type_id, 0, 1)
            else:
                dbg_typ = debuginfo.DebugBaseType(
                    typ.type_id, self.sizeof(typ), 1
                )
            self.debug_db.enter(typ, dbg_typ)
        elif isinstance(typ, types.EnumType):
            return self.get_debug_type(self._root_scope.get_type(["int"]))
        elif isinstance(typ, types.FunctionType):
            # This is in most cases a pointer to a function type.
            # Register for now as basetype with 0 size:
            dbg_typ = debuginfo.DebugBaseType("func", 0, 1)
            self.debug_db.enter(typ, dbg_typ)
        elif isinstance(typ, types.PointerType):
            ptype = self.get_debug_type(typ.element_type)
            dbg_typ = debuginfo.DebugPointerType(ptype)
            self.debug_db.enter(typ, dbg_typ)
        elif isinstance(typ, types.StructType):
            dbg_typ = debuginfo.DebugStructType()

            # Ensure to register the type first:
            self.debug_db.enter(typ, dbg_typ)

            if typ.fields:
                for field in typ.fields:
                    if field.name:
                        field_typ = self.get_debug_type(field.typ)
                        field_offset = self.context.offsetof(typ, field)
                        dbg_typ.add_field(field.name, field_typ, field_offset)
        elif isinstance(typ, types.UnionType):
            # Register union type as struct type:
            dbg_typ = debuginfo.DebugStructType()

            # Ensure to register the type first:
            self.debug_db.enter(typ, dbg_typ)

            if typ.fields:
                for field in typ.fields:
                    if field.name:
                        field_typ = self.get_debug_type(field.typ)
                        field_offset = 0
                        dbg_typ.add_field(field.name, field_typ, field_offset)
        elif isinstance(typ, types.ArrayType):
            assert typ.size is not None
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


class LinkTimeExpressionEvaluator(ConstantExpressionEvaluator):
    """ Special purpose evaluator for link time constant expressions. """

    def __init__(self, codegenerator):
        super().__init__(codegenerator.context)
        self.codegenerator = codegenerator

    def eval_global_access(self, declaration):
        # emit reference to global symbol
        cval = (ir.ptr, declaration.name)
        return cval

    def eval_string_literal(self, expr: expressions.StringLiteral):
        text_var = self.codegenerator.gen_global_string_constant(expr)
        cval = (ir.ptr, text_var.name)
        return cval

    def eval_compound_literal(self, expr: expressions.CompoundLiteral):
        """ Evaluate a constant compound literal. """
        compound_literal_var = self.codegenerator.gen_global_compound_literal(
            expr
        )
        cval = (ir.ptr, compound_literal_var.name)
        return cval

    def eval_take_address(self, expr):
        """ Evaluate the '&' operator. """
        if isinstance(expr, expressions.VariableAccess):
            declaration = expr.variable.declaration
            if isinstance(
                declaration,
                (
                    declarations.VariableDeclaration,
                    declarations.ParameterDeclaration,
                    declarations.ConstantDeclaration,
                    declarations.FunctionDeclaration,
                ),
            ):
                value = self.codegenerator.ir_var_map[declaration]
                cval = (ir.ptr, value.name)
            else:  # pragma: no cover
                raise NotImplementedError()
        elif isinstance(expr, expressions.CompoundLiteral):
            cval = self.eval_compound_literal(expr)
        else:  # pragma: no cover
            raise NotImplementedError()
        return cval
