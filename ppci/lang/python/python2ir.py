""" Python to IR compilation.

"""

import logging
import ast
import contextlib
import inspect
from ... import ir, irutils
from ...common import SourceLocation, CompilerError
from ...binutils import debuginfo


def python_to_ir(f, imports=None):
    """ Compile a piece of python code to an ir module.

    Args:
        f (file-like-object): a file like object containing the python code
        imports: Dictionary with symbols that are present.

    Returns:
        A :class:`ppci.ir.Module` module

    .. doctest::

        >>> import io
        >>> from ppci.lang.python import python_to_ir
        >>> f = io.StringIO("def calc(x: int) -> int: return x + 133")
        >>> python_to_ir(f)
        <ppci.ir.Module object at ...>

    """
    mod = PythonToIrCompiler().compile(f, imports=imports)
    return mod


class Var:
    def __init__(self, value, lvalue, ty):
        self.value = value
        self.lvalue = lvalue
        self.ty = ty


class PythonToIrCompiler:
    """ Not peer-to-peer but python to ppci :) """

    logger = logging.getLogger("p2p")

    def __init__(self):
        self.type_mapping = {"int": ir.i64, "float": ir.f64, "str": ir.ptr}

    def compile(self, f, imports=None):
        """ Convert python into IR-code.

        Arguments:
            f: the with the python code

        Returns:
            the ir-module.
        """
        self.debug_db = debuginfo.DebugDb()
        src = f.read()
        self._filename = getattr(f, "name", None)
        # Parse python code:
        x = ast.parse(src)

        self.function_map = {}

        self.builder = irutils.Builder()
        self.builder.prepare()
        self.builder.set_module(ir.Module("foo", debug_db=self.debug_db))

        if imports:
            # Fill imported functions:
            for name, signature in imports.items():
                self.gen_import(name, signature)

        for df in x.body:
            self.logger.debug("Processing %s", df)
            if isinstance(df, ast.FunctionDef):
                self.gen_function(df)
            else:
                self.not_impl(df)

        mod = self.builder.module
        irutils.verify_module(mod)
        return mod

    def gen_import(self, name, signature):
        # Determine function type:
        if isinstance(signature, tuple):
            return_type, arg_types = signature
        else:
            # Assume that we have a function:
            signature = inspect.signature(signature)
            if signature.return_annotation is inspect.Signature.empty:
                return_type = None
            else:
                return_type = signature.return_annotation
            arg_types = [p.annotation for p in signature.parameters.values()]

        # Create external function:
        ir_arg_types = [self.get_ty(t) for t in arg_types]
        if return_type:
            ir_function = ir.ExternalFunction(
                name, ir_arg_types, self.get_ty(return_type)
            )
        else:
            ir_function = ir.ExternalProcedure(name, ir_arg_types)

        self.builder.module.add_external(ir_function)
        self.function_map[name] = ir_function, return_type, arg_types

    def gen_function(self, df):
        """ Transform a python function into an IR-function """
        self.local_map = {}

        function_name = df.name
        binding = ir.Binding.GLOBAL
        dbg_int = debuginfo.DebugBaseType("int", 8, 1)
        return_type = self.get_ty(df.returns)
        if return_type:
            ir_function = self.builder.new_function(
                function_name, binding, return_type
            )
        else:
            ir_function = self.builder.new_procedure(function_name, binding)
        dbg_args = []
        arg_types = []
        for arg in df.args.args:
            if not arg.annotation:
                self.error(arg, "Need type annotation for {}".format(arg.arg))
            aty = self.get_ty(arg.annotation)
            arg_types.append(aty)
            arg_name = arg.arg

            # Debug info:
            param = ir.Parameter(arg_name, aty)
            dbg_args.append(debuginfo.DebugParameter(arg_name, dbg_int))

            ir_function.add_parameter(param)

        # Register function as known:
        self.function_map[function_name] = ir_function, return_type, arg_types

        self.logger.debug("Created function %s", ir_function)
        self.builder.block_number = 0
        self.builder.set_function(ir_function)

        dfi = debuginfo.DebugFunction(
            ir_function.name,
            SourceLocation("foo.py", 1, 1, 1),
            dbg_int,
            dbg_args,
        )
        self.debug_db.enter(ir_function, dfi)

        first_block = self.builder.new_block()
        self.builder.set_block(first_block)
        ir_function.entry = first_block

        # Copy the parameters to variables (so they can be modified):
        for parameter in ir_function.arguments:
            # self.local_map[name] = Var(param, False, aty)
            para_var = self.get_variable(df, parameter.name, ty=parameter.ty)
            self.emit(ir.Store(parameter, para_var.value))

        self.block_stack = []
        self.gen_statement(df.body)
        assert not self.block_stack

        # Return if not yet done
        if not self.builder.block.is_closed:
            if return_type:
                if self.builder.block.is_empty:
                    pass
                else:
                    raise NotImplementedError()
            else:
                self.emit(ir.Exit())

        # TODO: ugly:
        ir_function.delete_unreachable()

    def gen_statement(self, statement):
        """ Generate code for a statement """
        if isinstance(statement, list):
            for inner_statement in statement:
                self.gen_statement(inner_statement)
        else:
            with self.use_location(statement):
                if isinstance(statement, ast.Pass):
                    pass  # No comments :)
                elif isinstance(statement, ast.Return):
                    self.gen_return(statement)
                elif isinstance(statement, ast.If):
                    self.gen_if(statement)
                elif isinstance(statement, ast.While):
                    self.gen_while(statement)
                elif isinstance(statement, ast.Break):
                    self.gen_break(statement)
                elif isinstance(statement, ast.Continue):
                    self.gen_continue(statement)
                elif isinstance(statement, ast.For):
                    self.gen_for(statement)
                elif isinstance(statement, ast.Assign):
                    self.gen_assign(statement)
                elif isinstance(statement, ast.Expr):
                    self.gen_expr(statement.value)
                elif isinstance(statement, ast.AugAssign):
                    self.gen_aug_assign(statement)
                else:  # pragma: no cover
                    self.not_impl(statement)

    def gen_break(self, statement):
        break_block = self.block_stack[-1][1]
        self.builder.emit_jump(break_block)
        unreachable_block = self.builder.new_block()
        self.builder.set_block(unreachable_block)

    def gen_continue(self, statement):
        continue_block = self.block_stack[-1][0]
        self.builder.emit_jump(continue_block)
        unreachable_block = self.builder.new_block()
        self.builder.set_block(unreachable_block)

    def gen_return(self, statement):
        """ Compile return statement. """
        if self.builder.function.is_procedure:
            if statement.value:
                self.error(
                    statement,
                    "Cannot return a value from a function without return type.",
                )
            self.builder.emit_exit()
        else:
            if not statement.value:
                self.error(
                    statement, "Must return a value from this function."
                )
            value = self.gen_expr(statement.value)
            self.builder.emit_return(value)
        void_block = self.builder.new_block()
        self.builder.set_block(void_block)

    def gen_if(self, statement):
        """ Compile a python if-statement. """
        ja_block = self.builder.new_block()
        else_block = self.builder.new_block()
        continue_block = self.builder.new_block()
        self.gen_cond(statement.test, ja_block, else_block)

        # Yes
        self.builder.set_block(ja_block)
        self.gen_statement(statement.body)
        self.builder.emit_jump(continue_block)

        # Else:
        self.builder.set_block(else_block)
        self.gen_statement(statement.orelse)
        self.builder.emit_jump(continue_block)

        self.builder.set_block(continue_block)

    def gen_while(self, statement):
        """ Compile python while-statement. """
        if statement.orelse:
            self.error(statement, "while-else not supported")
        test_block = self.builder.new_block()
        body_block = self.builder.new_block()
        final_block = self.builder.new_block()

        # Test:
        self.builder.emit_jump(test_block)
        self.builder.set_block(test_block)
        self.gen_cond(statement.test, body_block, final_block)

        # Body:
        self.enter_loop(test_block, final_block)
        self.builder.set_block(body_block)
        self.gen_statement(statement.body)
        self.builder.emit_jump(test_block)
        self.leave_loop()

        # The end:
        self.builder.set_block(final_block)

    def gen_for(self, statement):
        """ Compile python for-statement. """
        # Check else-clause:
        if statement.orelse:
            self.error(statement, "for-else not supported")

        # Allow for loop with range in it:
        if not isinstance(statement.iter, ast.Call):
            self.error(statement.iter, "Only range supported in for loops")

        if statement.iter.func.id != "range":
            self.error(statement.iter, "Only range supported in for loops")

        # Determine start and end values:
        ra = statement.iter.args
        if len(ra) == 1:
            i_init = self.builder.emit_const(0, ir.i64)
            n2 = self.gen_expr(ra[0])
        elif len(ra) == 2:
            i_init = self.gen_expr(ra[0])
            n2 = self.gen_expr(ra[1])
        else:
            self.error(
                statement.iter,
                "Does not support {} arguments".format(len(ra)),
            )

        entry_block = self.builder.block
        test_block = self.builder.new_block()
        body_block = self.builder.new_block()
        final_block = self.builder.new_block()

        self.emit(ir.Jump(test_block))

        # Test block:
        self.builder.set_block(test_block)
        i_phi = self.emit(ir.Phi("i_phi", ir.i64))
        i_phi.set_incoming(entry_block, i_init)
        self.emit(ir.CJump(i_phi, "<", n2, body_block, final_block))

        # Publish looping variable:
        self.local_map[statement.target.id] = Var(i_phi, False, ir.i64)

        # Body:
        self.enter_loop(test_block, final_block)
        self.builder.set_block(body_block)
        self.gen_statement(statement.body)
        self.leave_loop()

        # Increment loop variable:
        one = self.builder.emit_const(1, ir.i64)
        i_inc = self.builder.emit_add(i_phi, one, ir.i64)
        i_phi.set_incoming(body_block, i_inc)

        # Jump to start again:
        self.builder.emit_jump(test_block)

        # The end:
        self.builder.set_block(final_block)

    def gen_assign(self, statement):
        """ Compile assignment-statement. """
        if len(statement.targets) == 1:
            target = statement.targets[0]
        else:
            self.error(
                statement, "Only a single assignment target is supported."
            )

        if isinstance(target, ast.Name):
            value = self.gen_expr(statement.value)
            self.store_value(target, value)
        elif isinstance(target, ast.Tuple):
            # Tuple assign like: 'a, b, c = 1, 2, 3'
            assert isinstance(statement.value, ast.Tuple)
            values = statement.value.elts
            targets = target.elts
            assert len(statement.value.elts) == len(targets)
            values = [self.gen_expr(v) for v in values]
            for target, value in zip(targets, values):
                self.store_value(target, value)
        else:  # pragma: no cover
            self.not_impl(statement)

    def gen_aug_assign(self, statement):
        """ Compile augmented assign.

        For example: 'a += 2'
        """
        target = statement.target
        if isinstance(target, ast.Name):
            name = target.id
            assert isinstance(name, str)
            var = self.get_variable(target, name)
            assert var.lvalue
            lhs = self.builder.emit_load(var.value, var.ty)
            rhs = self.gen_expr(statement.value)
            op = self.binop_map[type(statement.op)]
            value = self.emit(ir.Binop(lhs, op, rhs, "augassign", var.ty))
            self.emit(ir.Store(value, var.value))
        else:  # pragma: no cover
            self.not_impl(statement)

    def store_value(self, target, value):
        """ Store an IR-value into a target node. """
        assert isinstance(target, ast.Name)
        name = target.id
        var = self.get_variable(target, name, ty=value.ty)
        assert var.lvalue
        self.emit(ir.Store(value, var.value))

    def gen_cond(self, condition, yes_block, no_block):
        """ Compile a condition. """
        if isinstance(condition, ast.Compare):
            self.gen_compare(condition, yes_block, no_block)
        elif isinstance(condition, ast.BoolOp):
            self.gen_bool_op(condition, yes_block, no_block)
        else:  # pragma: no cover
            self.not_impl(condition)

    def gen_compare(self, condition, yes_block, no_block):
        # print(dir(c), c.ops, c.comparators)
        # TODO: chained operators! ( 'a < b < c < d' )
        assert len(condition.ops) == len(condition.comparators)
        assert len(condition.ops) == 1
        op_map = {
            ast.Gt: ">",
            ast.GtE: ">=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Eq: "==",
            ast.NotEq: "!=",
        }

        a = self.gen_expr(condition.left)
        op = op_map[type(condition.ops[0])]
        b = self.gen_expr(condition.comparators[0])
        if a.ty is not b.ty:
            self.error(condition, "Type mismatch, types must be the same.")

        self.emit(ir.CJump(a, op, b, yes_block, no_block))

    def gen_bool_op(self, condition, yes_block, no_block):
        """ Compile a boolean operator such as 'and' """
        assert len(condition.values) >= 1
        first_values = condition.values[:-1]
        last_value = condition.values[-1]
        if isinstance(condition.op, ast.And):
            # All values must be true here,
            # so bail out on first false value.
            for value in first_values:
                all_true_block = self.builder.new_block()
                self.gen_cond(value, all_true_block, no_block)
                self.builder.set_block(all_true_block)

            self.gen_cond(last_value, yes_block, no_block)
        elif isinstance(condition.op, ast.Or):
            # The first true value is enough to make this work!
            for value in first_values:
                all_false_block = self.builder.new_block()
                self.gen_cond(value, yes_block, all_false_block)
                self.builder.set_block(all_false_block)

            self.gen_cond(last_value, yes_block, no_block)
        else:  # pragma: no cover
            self.not_impl(condition)

    def gen_expr(self, expr):
        """ Generate code for a single expression """
        with self.use_location(expr):
            if isinstance(expr, ast.BinOp):
                value = self.gen_binop(expr)
            elif isinstance(expr, ast.Name):
                value = self.gen_name(expr)
            elif isinstance(expr, ast.Num):
                value = self.gen_num(expr)
            elif isinstance(expr, ast.Call):
                value = self.gen_call(expr)
            elif isinstance(expr, ast.Constant):
                value = self.gen_constant(expr)
            else:  # pragma: no cover
                self.not_impl(expr)
        return value

    def gen_name(self, expr):
        """ Compile name node access. """
        var = self.local_map[expr.id]
        if var.lvalue:
            value = self.builder.emit_load(var.value, var.ty)
        else:
            value = var.value
        return value

    binop_map = {
        ast.Add: "+",
        ast.Sub: "-",
        ast.Mult: "*",
        ast.Div: "/",
        ast.FloorDiv: "/",
    }

    def gen_binop(self, expr):
        """ Compile binary operator. """
        a = self.gen_expr(expr.left)
        b = self.gen_expr(expr.right)
        if a.ty is not b.ty:
            self.error(expr, "Type mismatch, types must be the same.")
            # TODO: automatic coercion
        # TODO: assume type of a?
        ty = a.ty
        op_typ = type(expr.op)
        if op_typ in self.binop_map:
            op = self.binop_map[op_typ]
        else:
            self.not_impl(expr)
        value = self.builder.emit_binop(a, op, b, ty)
        return value

    def gen_call(self, expr):
        """ Compile call-expression. """
        assert isinstance(expr.func, ast.Name)
        name = expr.func.id

        # Lookup function and check types:
        ir_function, return_type, arg_types = self.function_map[name]
        self.logger.warning("Function arguments not type checked!")

        # Evaluate arguments:
        args = [self.gen_expr(a) for a in expr.args]

        # Emit call:
        if return_type:
            value = self.emit(
                ir.FunctionCall(ir_function, args, "res", return_type)
            )
        else:
            self.emit(ir.ProcedureCall(ir_function, args))
            value = None
        return value

    def gen_num(self, expr):
        num = expr.n
        if isinstance(num, int):
            value = self.builder.emit_const(num, ir.i64)
        elif isinstance(num, float):
            value = self.builder.emit_const(num, ir.f64)
        else:  # pragma: no cover
            self.not_impl(expr)
        return value

    def gen_constant(self, expr):
        # TODO: are there different types of constants?
        assert isinstance(expr.value, str)
        data = expr.value.encode("utf8") + bytes([0])
        string_constant = self.emit(ir.LiteralData(data, "string_constant"))
        value = self.emit(ir.AddressOf(string_constant, "string_constant_ptr"))
        return value

    # Helper functions:
    def get_variable(self, node, name, ty=None):
        """ Retrieve a variable, or create it if type is given.
        """
        if name in self.local_map:
            var = self.local_map[name]
        else:
            # Create a variable with the given name
            # TODO: for now i64 is assumed to be the only type!
            if ty is None:
                self.error(node, "Undefined variable")
            else:
                mem = self.emit(ir.Alloc("alloc_{}".format(name), 8, 8))
                addr = self.emit(ir.AddressOf(mem, "addr_{}".format(name)))
                var = Var(addr, True, ty)
                self.local_map[name] = var
        return var

    def common_type(self, ty1, ty2):
        """ Determine the best target type for two input types.

        For example,
            (float, int) -> float
            (int, int) -> int
        """
        type_ranks = {
            float: 10,
            int: 5,
        }
        pass

    def coerce(self, value, ty):
        """ Try to fit the value into a new value of a type. """
        return value

    def not_impl(self, node):  # pragma: no cover
        print(dir(node))
        self.error(node, "Cannot do {}".format(node))

    def node_location(self, node):
        """ Create a source code location for the given node. """
        location = SourceLocation(
            self._filename, node.lineno, node.col_offset + 1, 1
        )
        return location

    def error(self, node, message):
        """ Raise a nice error message as feedback """
        location = self.node_location(node)
        raise CompilerError(message, location)

    def emit(self, instruction):
        """ Emit an instruction """
        self.builder.emit(instruction)
        return instruction

    def get_ty(self, annotation) -> ir.Typ:
        """ Get the type based on type annotation """
        if isinstance(annotation, type):
            type_name = annotation.__name__
        elif annotation is None:
            return
        else:
            if (
                isinstance(annotation, ast.NameConstant)
                and annotation.value is None
            ):
                return
            type_name = annotation.id

        if type_name in self.type_mapping:
            return self.type_mapping[type_name]
        else:
            self.error(annotation, "Unhandled type: {}".format(type_name))

    def enter_loop(self, continue_block, break_block):
        self.block_stack.append((continue_block, break_block))

    def leave_loop(self):
        self.block_stack.pop()

    @contextlib.contextmanager
    def use_location(self, node):
        """ Use the location of the node for all code generated
        within the with clause.
        """
        location = self.node_location(node)
        self.builder.push_location(location)
        yield
        self.builder.pop_location()
