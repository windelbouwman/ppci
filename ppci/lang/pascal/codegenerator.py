""" This module contains the code generation class. """

import logging
from ... import ir
from ... import irutils
from ...common import CompilerError
from ...binutils import debuginfo
from .nodes import statements, expressions, types, symbols


class CodeGenerator:
    """ Generates intermediate (IR) code.

    The entry function is
    'genModule'. The main task of this part is to rewrite complex control
    structures, such as while and for loops into simple conditional
    jump statements. Also complex conditional statements are simplified.
    Such as 'and' and 'or' statements are rewritten in conditional jumps.
    And structured datatypes are rewritten.

    """

    logger = logging.getLogger("pascal.codegen")

    def __init__(self, diag):
        self.builder = irutils.Builder()
        self.diag = diag
        self.context = None
        self.debug_db = debuginfo.DebugDb()
        self.var_map = {}

    def gencode(self, unit: symbols.Program, context):
        """ Generate code for a single unit """
        assert isinstance(unit, symbols.Program)
        self.context = context
        self.builder.prepare()
        self.var_map = {}
        self.logger.info("Generating ir-code for %s", unit.name)
        self.builder.module = ir.Module(unit.name, debug_db=self.debug_db)
        self._define_builtins()

        self.gen_globals(unit)
        self.gen_functions(unit)
        self.gen_main(unit)

        return self.builder.module

    def gen_main(self, unit):
        """ Generate code for global main script. """
        function_name = unit.name + "_" + "main"
        ir_function = self.builder.new_procedure(
            function_name, ir.Binding.GLOBAL
        )

        # Register debug info for main function:
        dbg_return_type = self.get_debug_type(None)
        dfi = debuginfo.DebugFunction(
            function_name, unit.location, dbg_return_type, [],
        )
        self.debug_db.enter(ir_function, dfi)

        self.builder.set_function(ir_function)
        first_block = self.builder.new_block()
        self.builder.set_block(first_block)
        ir_function.entry = first_block

        self.gen_stmt(unit.main_code)

        self.emit(ir.Exit())
        self.builder.set_function(None)

    def _define_builtins(self):
        """ Create external symbols for the various runtime functions.
        """
        self._add_external_procedure("io_print", [ir.ptr])
        self._add_external_procedure(
            "write_int",
            [self.get_ir_int(), self.get_ir_int(), self.get_ir_int()],
        )

        bsp_putc = ir.ExternalProcedure("bsp_putc", [ir.u8])
        self.builder.module.add_external(bsp_putc)
        self.var_map["io_print_char"] = bsp_putc

        self._add_external_procedure("io_read_int", [self.get_ir_int()])

    def _add_external_procedure(self, name, arg_types):
        external_procedure = ir.ExternalProcedure(name, arg_types)
        self.builder.module.add_external(external_procedure)
        self.var_map[name] = external_procedure

    def gen_globals(self, unit):
        """ Generate global variables and modules """

        # Generate room for global variables:
        for var in unit.inner_scope.variables:
            assert not var.isLocal

            if var.ival:
                cval = self.gen_global_ival(var.ival, var.typ)
                cval = (cval,)
            else:
                cval = None

            size = self.context.size_of(var.typ)
            # TODO:
            alignment = 8
            ir_var = ir.Variable(
                var.name, ir.Binding.GLOBAL, size, alignment, value=cval
            )
            self.var_map[var] = ir_var
            self.builder.module.add_variable(ir_var)

            # Create debug infos:
            # dbg_typ = self.get_debug_type(var.typ)
            # dv = debuginfo.DebugVariable(var.name, dbg_typ, var.loc)
            # self.debug_db.enter(ir_var, dv)

    def gen_global_ival(self, ival, typ):
        """ Create memory image for initial value """
        typ = self.context.get_type(typ)
        if isinstance(typ, types.ArrayType):
            assert isinstance(ival, expressions.ExpressionList)
            assert len(ival.expressions) == self.context.eval_const(typ.size)
            mem = bytes()
            for expr in ival.expressions:
                mem = mem + self.gen_global_ival(expr, typ.element_type)
            return mem
        elif isinstance(typ, types.RecordType):
            assert isinstance(ival, expressions.NamedExpressionList)
            assert len(ival.expressions) == len(typ.fields)
            mem = bytes()
            for field, val in zip(typ.fields, ival.expressions):
                assert field.name == val[0]
                expr = val[1]
                mem = mem + self.gen_global_ival(expr, field.typ)
            return mem
        elif isinstance(typ, types.FloatType):
            cval = self.context.eval_const(ival)
            cval = self.context.pack_float(cval, bits=typ.bits)
            return cval
        elif isinstance(typ, types.SignedIntegerType):
            cval = self.context.eval_const(ival)
            cval = self.context.pack_int(cval, bits=typ.bits, signed=True)
            return cval
        elif isinstance(typ, types.UnsignedIntegerType):
            cval = self.context.eval_const(ival)
            cval = self.context.pack_int(cval, bits=typ.bits, signed=False)
            return cval

    def emit(self, instruction):
        """
            Emits the given instruction to the builder.
            Can be muted for constants.
        """
        return self.builder.emit(instruction)

    def new_block(self):
        return self.builder.new_block()

    def get_debug_type(self, typ):
        """ Get or create debug type info in the debug information """
        # Lookup the type:
        if typ is not None:
            typ = self.context.get_type(typ)

        if self.debug_db.contains(typ):
            return self.debug_db.get(typ)

        if isinstance(typ, types.BaseType):
            size = self.context.size_of(typ)
            if size == 8:
                # TODO: bit of a hack?
                typ_name = "int"
            else:
                typ_name = "int{}".format(size)
            dbg_typ = debuginfo.DebugBaseType(typ_name, size, 1)
            self.debug_db.enter(typ, dbg_typ)
        elif typ is None:
            # Void type
            dbg_typ = debuginfo.DebugBaseType("void", 0, 1)
            self.debug_db.enter(typ, dbg_typ)
        elif isinstance(typ, types.EnumType):
            dbg_typ = self.get_debug_type(self.context.get_type("integer"))
        elif isinstance(typ, types.PointerType):
            ptype = self.get_debug_type(typ.ptype)
            dbg_typ = debuginfo.DebugPointerType(ptype)
            self.debug_db.enter(typ, dbg_typ)
        elif isinstance(typ, types.RecordType):
            dbg_typ = debuginfo.DebugStructType()

            # Enter the type here, so the cached value is taken when
            # a linked list is encountered:
            self.debug_db.enter(typ, dbg_typ)
            for field in typ.fields:
                offset = field.offset
                field_typ = self.get_debug_type(field.typ)
                dbg_typ.add_field(field.name, field_typ, offset)
        elif isinstance(typ, types.ArrayType):
            et = self.get_debug_type(typ.element_type)
            if isinstance(typ.size, int):
                size = typ.size
            else:
                size = self.context.eval_const(typ.size)
            dbg_typ = debuginfo.DebugArrayType(et, size)
            self.debug_db.enter(typ, dbg_typ)
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))
        return dbg_typ

    def error(self, msg, loc=None):
        """ Emit error to diagnostic system and mark package as invalid """
        self.diag.error(msg, loc)

    def gen_functions(self, unit):
        """ Generate code for subroutines. """
        subroutines = unit.functions
        # First create ir-functions:
        # This is required since functions are sorted by
        # name.
        # TODO: sort by name or not?
        # Generate as declared?
        for subroutine in subroutines:
            self.create_subroutine(subroutine)

        for nr, subroutine in enumerate(subroutines, 1):
            self.logger.debug(
                "Generating IR-code for {} ({}/{})".format(
                    subroutine.name, nr, len(subroutines)
                )
            )
            self.gen_subroutine(subroutine)

    def create_subroutine(self, subroutine):
        if subroutine.is_procedure:
            ir_function = self.builder.new_procedure(
                subroutine.name, ir.Binding.GLOBAL
            )
        else:
            assert subroutine.is_function
            return_type = self.get_ir_type(subroutine.typ.return_type)
            ir_function = self.builder.new_function(
                subroutine.name, ir.Binding.GLOBAL, return_type
            )

        self.var_map[subroutine] = ir_function

    def gen_subroutine(self, subroutine):
        """ Generate code for a subroutine.
        
        This involves creating room
        for parameters on the stack, and generating code for the function
        body.
        """
        ir_function = self.var_map[subroutine]

        # Generate inner sub programs:
        for sym in subroutine.inner_scope:
            if sym.is_subroutine:
                raise NotImplementedError("Nested function are TODO")
                self.gen_function(sym)

        self.builder.set_function(ir_function)
        first_block = self.new_block()
        self.builder.set_block(first_block)
        ir_function.entry = first_block

        # generate parameters:
        dbg_args = []
        param_map = {}
        if subroutine.parameters:
            for param in subroutine.parameters:
                # Parameters can only be simple types (pass by value)
                param_ir_typ = self.get_ir_type(param.typ)

                # Define parameter for function:
                ir_parameter = ir.Parameter(param.name, param_ir_typ)
                ir_function.add_parameter(ir_parameter)
                param_map[param] = ir_parameter

                # Debug info for this formal parameter:
                dbg_typ = self.get_debug_type(param.typ)
                dbg_args.append(debuginfo.DebugParameter(param.name, dbg_typ))

        # Generate debug info for function:
        if subroutine.is_function:
            dbg_return_type = self.get_debug_type(subroutine.typ.return_type)
        else:
            dbg_return_type = self.get_debug_type(None)

        dfi = debuginfo.DebugFunction(
            subroutine.name, subroutine.location, dbg_return_type, dbg_args,
        )
        self.debug_db.enter(ir_function, dfi)

        if subroutine.is_function:
            # Create room for return value:
            return_value = self.emit_local(
                "result_{}".format(subroutine.name), subroutine.typ.return_type
            )
            self.var_map[(subroutine, "result")] = return_value

        # generate room for locals:
        for sym in subroutine.inner_scope:
            if isinstance(sym, symbols.Variable):
                var_name = "var_{}".format(sym.name)
                variable = self.emit_local(var_name, sym.typ)
                if sym in param_map:
                    # Get the parameter from earlier:
                    parameter = param_map[sym]

                    # For paramaters, allocate space and copy the value into
                    # memory. Later, the mem2reg pass will extract these values.
                    # Move parameter into local copy:
                    self.emit(ir.Store(parameter, variable))
                self.var_map[sym] = variable
            elif isinstance(sym, symbols.Function):
                # inner function!
                pass
            else:  # pragma: no cover
                raise NotImplementedError(str(sym))

            # Debug info:
            # dbg_typ = self.get_debug_type(sym.typ)
            # dv = debuginfo.DebugVariable(sym.name, dbg_typ, sym.loc)
            # self.debug_db.enter(variable, dv)
            # dfi.add_variable(dv)

        # Generate code for body:
        self.gen_stmt(subroutine.code)

        # Close block:
        if not self.builder.block.is_closed:
            # In case of void function, introduce exit instruction:
            if subroutine.is_procedure:
                self.emit(ir.Exit())
            else:
                value = self.emit(
                    ir.Load(
                        return_value,
                        "res",
                        self.get_ir_type(subroutine.typ.return_type),
                    )
                )
                self.emit(ir.Return(value))

        # Remove unreachable blocks from the function:
        ir_function.delete_unreachable()
        self.builder.set_function(None)

    def emit_local(self, var_name, typ):
        """ Emit stack allocated variable. """
        variable = ir.Alloc(var_name, self.context.size_of(typ), 1)
        self.emit(variable)
        variable = self.emit(ir.AddressOf(variable, var_name))
        return variable

    def get_ir_int(self):
        mapping = {1: ir.i8, 2: ir.i16, 4: ir.i32, 8: ir.i64}
        return mapping[self.context.get_type("integer").byte_size]

    def get_ir_type(self, cty):
        """ Given a certain type, get the corresponding ir-type """
        cty = self.context.get_type(cty)
        if isinstance(cty, types.FloatType):
            float_types = {32: ir.f32, 64: ir.f64}
            ty = float_types[cty.bits]
        elif isinstance(cty, types.SignedIntegerType):
            signed_types = {8: ir.i8, 16: ir.i16, 32: ir.i32, 64: ir.i64}
            ty = signed_types[cty.bits]
        elif isinstance(cty, types.UnsignedIntegerType):
            unsigned_types = {8: ir.u8, 16: ir.u16, 32: ir.u32, 64: ir.u64}
            ty = unsigned_types[cty.bits]
        elif self.context.equal_types(cty, "boolean"):
            # Implement booleans as integers:
            ty = self.get_ir_int()
        elif isinstance(cty, types.PointerType):
            # A pointer is a pointer, no type info in ir.
            ty = ir.ptr
        elif isinstance(cty, types.EnumType):
            ty = self.get_ir_int()
        elif isinstance(cty, (types.ProcedureType, types.FunctionType)):
            # A pointer is a pointer, no type info in ir.
            ty = ir.ptr
        else:  # pragma: no cover
            raise NotImplementedError(str(cty))
        return ty

    def gen_stmt(self, code: statements.Statement):
        """ Generate code for a statement """
        assert isinstance(code, statements.Statement)
        with self.builder.use_location(code.location):
            if isinstance(code, statements.Compound):
                for statement in code.statements:
                    self.gen_stmt(statement)
            elif isinstance(code, statements.Empty):
                pass
            elif isinstance(code, statements.Assignment):
                self.gen_assignment_stmt(code)
            elif isinstance(code, statements.If):
                self.gen_if_stmt(code)
            elif isinstance(code, statements.Return):
                self.gen_return_stmt(code)
            elif isinstance(code, statements.Exit):
                self.gen_exit_stmt(code)
            elif isinstance(code, statements.While):
                self.gen_while(code)
            elif isinstance(code, statements.For):
                self.gen_for_stmt(code)
            elif isinstance(code, statements.Repeat):
                self.gen_repeat_stmt(code)
            elif isinstance(code, statements.CaseOf):
                self.gen_case_of_stmt(code)
            elif isinstance(code, statements.ProcedureCall):
                self.gen_procedure_call(code)
            elif isinstance(code, statements.BuiltinProcedureCall):
                self.gen_builtin_procedure_call(code)
            else:  # pragma: no cover
                raise NotImplementedError(str(code))

    def gen_return_stmt(self, code):
        """ Generate code for return statement """
        ret_val = self.gen_expr_code(code.expr, rvalue=True)
        self.emit(ir.Return(ret_val))
        self.builder.set_block(self.new_block())

    def gen_exit_stmt(self, code):
        """ Generate code for exit statement """
        self.emit(ir.Exit())
        self.builder.set_block(self.new_block())

    def gen_assignment_stmt(self, code):
        """ Generate code for assignment statement """
        # Evaluate right hand side:
        rval = self.gen_expr_code(code.rval, rvalue=True)
        self.gen_store(code.lval, rval)

    def gen_store(self, dest, value):
        if isinstance(dest, symbols.Variable):
            addr = self.var_map[dest]
        else:
            # Evaluate destination:
            addr, lval_lvalue = self.gen_expr_code(dest)

            # Check that left hand is an lvalue:
            assert lval_lvalue

        self.emit(ir.Store(value, addr))

    def gen_local_var_init(self, var):
        """ Initialize a local variable """
        if var.ival is None:
            return
        alloc = self.var_map[var]
        self.gen_expr_at(alloc, var.ival)

    def gen_expr_at(self, ptr, expr):
        """ Generate code at a pointer in memory """
        if isinstance(expr, expressions.ExpressionList):
            # We have list of expressions, recurse!
            for e in expr.expressions:
                ptr = self.gen_expr_at(ptr, e)
            return ptr
        elif isinstance(expr, expressions.NamedExpressionList):
            for _, e in expr.expressions:
                ptr = self.gen_expr_at(ptr, e)
            return ptr
        else:
            # Evaluate expression value:
            rval = self.gen_expr_code(expr, rvalue=True)

            # Store the value at current pointer:
            # TODO: take volatile into account here?
            self.emit(ir.Store(rval, ptr))

            # Increment pointer with appropriate size:
            size = self.context.size_of(expr.typ)
            inc = self.emit(ir.Const(size, "inc", ir.ptr))
            ptr = self.emit(ptr + inc)
            return ptr

    def gen_if_stmt(self, code):
        """ Generate code for if statement """
        true_block = self.new_block()
        false_block = self.new_block()
        final_block = self.new_block()
        self.gen_cond_code(code.condition, true_block, false_block)
        self.builder.set_block(true_block)
        self.gen_stmt(code.truestatement)
        self.emit(ir.Jump(final_block))
        self.builder.set_block(false_block)
        self.gen_stmt(code.falsestatement)
        self.emit(ir.Jump(final_block))
        self.builder.set_block(final_block)

    def gen_while(self, code: statements.While):
        """ Generate code for while statement """
        main_block = self.new_block()
        test_block = self.new_block()
        final_block = self.new_block()
        self.emit(ir.Jump(test_block))
        self.builder.set_block(test_block)
        self.gen_cond_code(code.condition, main_block, final_block)
        self.builder.set_block(main_block)
        self.gen_stmt(code.statement)
        self.emit(ir.Jump(test_block))
        self.builder.set_block(final_block)

    def gen_repeat_stmt(self, code: statements.Repeat):
        """ Generate code for repeat statement. """
        main_block = self.new_block()
        final_block = self.new_block()
        self.emit(ir.Jump(main_block))
        self.builder.set_block(main_block)
        self.gen_stmt(code.statement)
        self.gen_cond_code(code.condition, final_block, main_block)
        self.builder.set_block(final_block)

    def gen_for_stmt(self, code: statements.For):
        """ Generate for-loop code """
        main_block = self.builder.new_block()
        increment_block = self.builder.new_block()
        final_block = self.builder.new_block()

        entry_block = self.builder.block
        ty = self.get_ir_int()
        one = self.emit(ir.Const(1, "one", ty))
        initial_value = self.gen_expr_code(code.start, rvalue=True)
        final_value = self.gen_expr_code(code.final, rvalue=True)

        self.emit(ir.Jump(main_block))
        self.builder.set_block(main_block)

        loop_var = self.emit(ir.Phi("loop_var", ty))
        loop_var.set_incoming(entry_block, initial_value)
        self.gen_store(code.loop_var, loop_var)

        self.gen_stmt(code.statement)

        self.emit(
            ir.CJump(loop_var, "==", final_value, final_block, increment_block)
        )

        self.builder.set_block(increment_block)

        # Update loop variable:
        if code.direction:  # count up
            new_loop_var = self.emit(
                ir.add(loop_var, one, "incremented_loop_var", ty)
            )
        else:
            new_loop_var = self.emit(
                ir.sub(loop_var, one, "decremented_loop_var", ty)
            )

        loop_var.set_incoming(increment_block, new_loop_var)
        self.emit(ir.Jump(main_block))

        self.builder.set_block(final_block)

    def gen_case_of_stmt(self, switch: statements.CaseOf):
        """ Generate code for a case-of statement """
        ir_val = self.gen_expr_code(switch.expression, rvalue=True)
        tha_type = switch.expression.typ
        assert isinstance(tha_type, types.IntegerType)

        final_block = self.builder.new_block()
        test_block = self.builder.new_block()
        self.emit(ir.Jump(test_block))

        default_block = None
        # Generate code in linear way:
        for option_values, option_code in switch.options:
            # Generate code for case:
            code_block = self.builder.new_block()
            self.builder.set_block(code_block)
            self.gen_stmt(option_code)
            self.emit(ir.Jump(final_block))

            if option_values == "else":
                # default case
                default_block = code_block
            else:
                # TODO: type check constant:
                for option in option_values:
                    self.builder.set_block(test_block)
                    o_val = self.gen_expr_code(option, rvalue=True)
                    new_test_block = self.builder.new_block()
                    self.emit(
                        ir.CJump(
                            ir_val, "==", o_val, code_block, new_test_block
                        )
                    )
                    test_block = new_test_block

        self.builder.set_block(test_block)
        assert default_block
        self.emit(ir.Jump(default_block))
        self.builder.set_block(final_block)

    def gen_procedure_call(self, call: statements.ProcedureCall):
        """ Call a user procedure. """
        args = self.gen_subroutine_arguments(call.arguments)
        self.emit_procedure_call(call.callee, args)

    def gen_builtin_procedure_call(
        self, call: statements.BuiltinProcedureCall
    ):
        # TODO: generate other procedures as well.
        # assert isinstance(call.callee, str)

        for (func, args) in call.calls:
            args = self.gen_subroutine_arguments(args)
            self.emit_procedure_call(func, args)

    def gen_subroutine_arguments(self, arguments):
        args = [
            self.gen_expr_code(arg_expr, rvalue=True) for arg_expr in arguments
        ]
        return args

    def emit_procedure_call(self, function_name, arguments):
        # print(function_name, type(function_name))
        callee = self.var_map[function_name]
        # raise NotImplementedError(str(function_name))
        self.emit(ir.ProcedureCall(callee, arguments))

    def gen_cond_code(self, expr: expressions.Expression, bbtrue, bbfalse):
        """ Generate conditional logic.
            Implement sequential logical operators. """
        if isinstance(expr, expressions.Binop):
            if expr.op == "or":
                # Implement sequential logic:
                second_block = self.builder.new_block()
                self.gen_cond_code(expr.a, bbtrue, second_block)
                self.builder.set_block(second_block)
                self.gen_cond_code(expr.b, bbtrue, bbfalse)
            elif expr.op == "and":
                # Implement sequential logic:
                second_block = self.builder.new_block()
                self.gen_cond_code(expr.a, second_block, bbfalse)
                self.builder.set_block(second_block)
                self.gen_cond_code(expr.b, bbtrue, bbfalse)
            elif expr.op in ["=", ">", "<", "<>", "<=", ">="]:
                lhs = self.gen_expr_code(expr.a, rvalue=True)
                rhs = self.gen_expr_code(expr.b, rvalue=True)
                op_map = {
                    "=": "==",
                    "<>": "!=",
                    ">": ">",
                    "<": "<",
                    ">=": ">=",
                    "<=": "<=",
                }
                self.emit(ir.CJump(lhs, op_map[expr.op], rhs, bbtrue, bbfalse))
            else:  # pragma: no cover
                raise NotImplementedError(str(expr.op))
            expr.typ = self.context.get_type("boolean")
        elif isinstance(expr, expressions.Literal):
            self.gen_expr_code(expr)
            if expr.val:
                self.emit(ir.Jump(bbtrue))
            else:
                self.emit(ir.Jump(bbfalse))
        elif isinstance(expr, expressions.Unop) and expr.op == "not":
            # In case of not, simply swap true and false!
            self.gen_cond_code(expr.a, bbfalse, bbtrue)
        elif isinstance(expr, expressions.Expression):
            # Evaluate expression, make sure it is boolean and compare it
            # with true:
            value = self.gen_expr_code(expr, rvalue=True)
            assert self.context.equal_types(expr.typ, "boolean")
            true_val = self.emit(
                ir.Const(1, "true", self.get_ir_type(expr.typ))
            )
            self.emit(ir.CJump(value, "==", true_val, bbtrue, bbfalse))
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))

        # Check that the condition is a boolean value:
        if not self.context.equal_types(expr.typ, "boolean"):
            self.error("Condition must be boolean", expr.loc)

    def gen_expr_code(self, expr: expressions.Expression, rvalue=False):
        """ Generate code for an expression.
        Return the generated ir-value.
        """
        assert isinstance(expr, expressions.Expression)
        if expr.is_bool:
            value, lvalue = self.gen_bool_expr(expr)
        else:
            if isinstance(expr, expressions.Binop):
                value, lvalue = self.gen_binop(expr)
            elif isinstance(expr, expressions.Unop):
                value, lvalue = self.gen_unop(expr)
            elif isinstance(expr, expressions.VariableAccess):
                value, lvalue = self.gen_var_access(expr)
            elif isinstance(expr, expressions.Deref):
                value, lvalue = self.gen_dereference(expr)
            elif isinstance(expr, expressions.Member):
                value, lvalue = self.gen_member_expr(expr)
            elif isinstance(expr, expressions.Index):
                value, lvalue = self.gen_index_expr(expr)
            elif isinstance(expr, expressions.Literal):
                value, lvalue = self.gen_literal_expr(expr)
            elif isinstance(expr, expressions.TypeCast):
                value, lvalue = self.gen_type_cast(expr)
            elif isinstance(expr, expressions.Sizeof):
                value, lvalue = self.gen_sizeof(expr)
            elif isinstance(expr, expressions.FunctionCall):
                value, lvalue = self.gen_function_call(expr)
            elif isinstance(expr, expressions.BuiltInFunctionCall):
                value, lvalue = self.gen_builtin_function_call(expr)
            else:  # pragma: no cover
                raise NotImplementedError(str(expr))

        assert isinstance(value, ir.Value)

        # do rvalue trick here, create a r-value when required:
        if rvalue and lvalue:
            # Generate expression code and insert an extra load instruction
            # when required.
            # This means that the value can be used in an expression or as
            # a parameter.

            val_typ = self.context.get_type(expr.typ)
            assert isinstance(
                val_typ,
                (
                    types.PointerType,
                    types.BaseType,
                    types.FunctionType,
                    types.ProcedureType,
                    types.EnumType,
                ),
            )

            # Determine loaded type:
            load_ty = self.get_ir_type(expr.typ)

            # Load the value:
            value = self.emit(ir.Load(value, "load", load_ty))

            # This expression is no longer an lvalue
            lvalue = False

        if rvalue:
            return value
        else:
            return value, lvalue

    def gen_sizeof(self, expr):
        # This is not a location value..
        lvalue = False

        type_size = self.context.size_of(expr.query_typ)
        value = self.emit(ir.Const(type_size, "sizeof", self.get_ir_int()))
        return value, lvalue

    def gen_dereference(self, expr: expressions.Deref):
        """ dereference pointer type, which means *(expr) """
        assert isinstance(expr, expressions.Deref)

        # Make sure to have the rvalue of the pointer:
        deref_value = self.gen_expr_code(expr.ptr, rvalue=True)

        # A pointer is always a lvalue:
        lvalue = True

        ptr_typ = self.context.get_type(expr.ptr.typ)
        assert isinstance(ptr_typ, types.PointerType)
        return deref_value, lvalue

    def gen_unop(self, expr):
        """ Generate code for unary operator """
        if expr.op == "&":
            rhs, rhs_lvalue = self.gen_expr_code(expr.a)
            assert rhs_lvalue
            lvalue = False
            value = rhs
        elif expr.op == "+":
            value = self.gen_expr_code(expr.a, rvalue=True)
            lvalue = False
        elif expr.op == "-":
            rhs = self.gen_expr_code(expr.a, rvalue=True)
            lvalue = False

            # Implement unary operator with sneaky trick using 0 - v binop:
            zero = self.emit(ir.Const(0, "zero", rhs.ty))
            value = self.emit(ir.Binop(zero, "-", rhs, "unary_minus", rhs.ty))
        else:  # pragma: no cover
            raise NotImplementedError(str(expr.op))
        return value, lvalue

    def gen_bool_expr(self, expr):
        """ Generate code for cases where a boolean value is assigned """
        # In case of boolean assignment like:
        # 'var bool x = true or false;'

        # Use condition machinery:
        true_block = self.builder.new_block()
        false_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.gen_cond_code(expr, true_block, false_block)

        # True path:
        self.builder.set_block(true_block)
        true_val = self.emit(ir.Const(1, "true", self.get_ir_type(expr.typ)))
        self.emit(ir.Jump(final_block))

        # False path:
        self.builder.set_block(false_block)
        false_val = self.emit(ir.Const(0, "false", self.get_ir_type(expr.typ)))
        self.emit(ir.Jump(final_block))

        # Final path:
        self.builder.set_block(final_block)
        phi = self.emit(ir.Phi("bool_res", self.get_ir_type(expr.typ)))
        phi.set_incoming(false_block, false_val)
        phi.set_incoming(true_block, true_val)

        # This is for sure no lvalue:
        lvalue = False
        return phi, lvalue

    def gen_binop(self, expr: expressions.Binop):
        """ Generate code for binary operation """
        assert isinstance(expr, expressions.Binop)
        assert expr.op not in expressions.Binop.cond_ops

        # Dealing with simple arithmatic
        a_val = self.gen_expr_code(expr.a, rvalue=True)
        b_val = self.gen_expr_code(expr.b, rvalue=True)
        assert isinstance(a_val, ir.Value)
        assert isinstance(b_val, ir.Value)

        op_map = {
            "+": "+",
            "-": "-",
            "*": "*",
            "/": "/",
            "div": "/",
            "mod": "%",
        }
        op = op_map[expr.op]

        self.context.equal_types(expr.a.typ, expr.b.typ)

        value = self.emit(ir.Binop(a_val, op, b_val, "binop", a_val.ty))
        lvalue = False
        return value, lvalue

    def gen_var_access(self, expr: expressions.VariableAccess):
        """ Generate code for when an identifier was referenced """
        symbol = expr.variable
        if isinstance(symbol, symbols.EnumValue):
            ty = self.get_ir_type(expr.typ)
            value = int(symbol.value)
            value = self.emit(ir.Const(value, "enum_value", ty))
            lvalue = False
        elif isinstance(symbol, symbols.Constant):
            value, lvalue = self.gen_expr_code(symbol.value)
        elif isinstance(symbol, (symbols.SubRoutine, symbols.Variable)):
            value = self.var_map[expr.variable]
            lvalue = True
        else:
            raise NotImplementedError()
        return value, lvalue

    def gen_member_expr(self, expr):
        """ Generate code for member expression such as struc.mem = 2
        """

        base, base_lvalue = self.gen_expr_code(expr.base)
        # base must be lvalue because we handle with addresses of variables
        assert base_lvalue

        # The base is a valid expression:
        assert isinstance(base, ir.Value)
        lvalue = True
        basetype = self.context.get_type(expr.base.typ)
        assert isinstance(basetype, types.RecordType)
        assert basetype.has_field(expr.field)

        # Calculate offset into struct:
        base_type = self.context.get_type(expr.base.typ)
        offset = self.emit(
            ir.Const(base_type.field_offset(expr.field), "offset", ir.ptr)
        )

        # Calculate memory address of field:
        value = self.emit(ir.add(base, offset, "mem_addr", ir.ptr))
        return value, lvalue

    def gen_index_expr(self, expr):
        """ Array indexing """
        base, base_lvalue = self.gen_expr_code(expr.base)
        # Base address must be a location value:
        assert base_lvalue
        idx = self.gen_expr_code(expr.index, rvalue=True)

        base_typ = self.context.get_type(expr.base.typ)
        assert isinstance(base_typ, types.ArrayType)

        element_type = self.context.get_type(base_typ.element_type)
        element_size = self.context.size_of(element_type)

        int_ir_type = self.get_ir_type("integer")

        # Generate constant:
        e_size = self.emit(ir.Const(element_size, "element_size", int_ir_type))

        # Calculate offset:
        offset = self.emit(ir.mul(idx, e_size, "element_offset", int_ir_type))
        offset = self.emit(ir.Cast(offset, "element_offset", ir.ptr))

        # Calculate address:
        value = self.emit(ir.add(base, offset, "element_address", ir.ptr))
        lvalue = True
        return value, lvalue

    def gen_literal_expr(self, expr):
        """ Generate code for literal """

        # Construct correct const value:
        if self.context.equal_types(expr.typ, "string"):
            cval = self.context.pack_string(expr.val)
            value = self.emit(ir.LiteralData(cval, "strval"))
            value = self.emit(ir.AddressOf(value, "addr"))
        elif self.context.equal_types(expr.typ, "char"):
            val = ord(expr.val)
            value = self.emit(ir.Const(val, "cnst", self.get_ir_type("char")))
        elif self.context.equal_types(expr.typ, "integer"):
            # For booleans, use the integer as storage class:
            val = int(expr.val)
            value = self.emit(ir.Const(val, "cnst", self.get_ir_int()))
        elif self.context.equal_types(expr.typ, "real"):
            val = float(expr.val)
            value = self.emit(ir.Const(val, "cnst", ir.f64))
        else:  # pragma: no cover
            raise NotImplementedError(str(expr.typ))
        lvalue = False
        return value, lvalue

    def gen_type_cast(self, expr):
        """ Generate code for type casting """
        # When type casting, the rvalue property is lost.
        ar = self.gen_expr_code(expr.a, rvalue=True)
        lvalue = False

        from_type = self.context.get_type(expr.a.typ)
        to_type = self.context.get_type(expr.to_type)

        # Evaluate types from pointer, unsigned, signed to floating point:
        if isinstance(from_type, types.PointerType) and isinstance(
            to_type, types.PointerType
        ):
            value = ar
        elif isinstance(from_type, types.IntegerType) and isinstance(
            to_type, types.PointerType
        ):
            value = self.emit(ir.Cast(ar, "int2ptr", ir.ptr))
        elif isinstance(to_type, types.IntegerType) and isinstance(
            from_type, types.PointerType
        ):
            ir_to_type = self.get_ir_type(to_type)
            value = self.emit(ir.Cast(ar, "ptr2int", ir_to_type))
        elif isinstance(
            from_type, (types.IntegerType, types.FloatType)
        ) and isinstance(to_type, (types.IntegerType, types.FloatType)):
            # Any numeric cast
            value = self.emit(ir.Cast(ar, "cast", self.get_ir_type(to_type)))
        else:  # pragma: no cover
            raise NotImplementedError(
                "Cannot cast {} to {}".format(from_type, to_type)
            )
        return value, lvalue

    def gen_function_call(self, expr: expressions.FunctionCall):
        """ Generate code for a function call """
        # Lookup the function in question:
        assert isinstance(expr, expressions.FunctionCall)
        target_func = expr.callee
        # assert isinstance(target_func, symbols.Function)
        ftyp = target_func.typ
        fname = target_func.name
        callee = self.var_map[target_func]

        # Check arguments:
        ptypes = ftyp.parameter_types
        assert len(expr.args) == len(ptypes)

        # Evaluate the arguments:
        args = self.gen_subroutine_arguments(expr.args)

        # assert self.context.is_simple_type(ftyp.returntype)

        # Determine return type:
        ret_typ = self.get_ir_type(expr.typ)

        # Emit call:
        value = self.emit(
            ir.FunctionCall(callee, args, fname + "_rv", ret_typ),
        )

        # Return type will never be an lvalue:
        lvalue = False

        return value, lvalue

    def gen_builtin_function_call(self, expr: expressions.BuiltInFunctionCall):
        """ Generate code for a builtin function call.
        """

        # print(expr.func)
        if expr.func == "succ":
            # Simply add 1:
            (arg,) = expr.args
            lhs = self.gen_expr_code(arg, rvalue=True)
            one = self.emit(ir.Const(1, "one", lhs.ty))
            res = self.emit(ir.Binop(lhs, "+", one, "succ", lhs.ty))
        elif expr.func == "chr":
            (arg,) = expr.args
            value = self.gen_expr_code(arg, rvalue=True)
            res = self.emit(ir.Cast(value, "chr", self.get_ir_type("char")))
        # elif expr.func == "abs":
        elif expr.func in ["arctan", "sqrt", "sqr", "sin", "cos"]:
            (arg,) = expr.args
            x = self.gen_expr_code(arg, rvalue=True)
            # TODO! call func!
            res = x
        else:
            raise NotImplementedError(expr.func)

        # Return type will never be an lvalue:
        lvalue = False

        return res, lvalue
