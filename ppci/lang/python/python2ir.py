""" Python to IR transpilation.

"""

import logging
import ast
import inspect
from ... import ir, irutils
from ...common import SourceLocation, CompilerError
from ...binutils import debuginfo


def get_fty(fn):
    pass


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
        >>> python_to_ir(f) # doctest: +ELLIPSIS
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
    logger = logging.getLogger('p2p')

    def __init__(self):
        self.type_mapping = {
            'int': ir.i64,
            'float': ir.f64,
        }

    def compile(self, f, imports=None):
        """ Convert python into IR-code.

        Arguments:
            f: the with the python code

        Returns:
            the ir-module.
        """
        self.debug_db = debuginfo.DebugDb()
        src = f.read()
        self._filename = getattr(f, 'name', None)
        # Parse python code:
        x = ast.parse(src)

        self.function_map = {}

        self.builder = irutils.Builder()
        self.builder.prepare()
        self.builder.set_module(ir.Module('foo', debug_db=self.debug_db))

        if imports:
            # Fill imported functions:
            for name, signature in imports.items():
                # Determine function type:
                if isinstance(signature, tuple):
                    return_type, arg_types = signature
                else:
                    # Assume that we have a function:
                    signature = inspect.signature(signature)
                    return_type = signature.return_annotation
                    arg_types = [
                        p.annotation for p in signature.parameters.values()]

                # Create external function:
                ir_arg_types = [self.get_ty(t) for t in arg_types]
                if return_type:
                    ir_function = ir.ExternalFunction(
                        name, ir_arg_types, self.get_ty(ir.ptr))
                else:
                    ir_function = ir.ExternalProcedure(name, ir_arg_types)

                self.function_map[name] = ir_function, return_type, arg_types

        for df in x.body:
            self.logger.debug('Processing %s', df)
            if isinstance(df, ast.FunctionDef):
                self.gen_function(df)
            else:
                raise NotImplementedError('Cannot do {}!'.format(df))
        mod = self.builder.module
        irutils.Verifier().verify(mod)
        return mod

    def emit(self, instruction):
        """ Emit an instruction """
        self.builder.emit(instruction)
        return instruction

    def get_ty(self, annotation) -> ir.Typ:
        """ Get the type based on type annotation """
        if isinstance(annotation, type):
            type_name = annotation.__name__
        else:
            if isinstance(annotation, ast.NameConstant) and \
                    annotation.value is None:
                return
            type_name = annotation.id

        if type_name in self.type_mapping:
            return self.type_mapping[type_name]
        else:
            self.error(annotation, 'Unhandled type: {}'.format(type_name))

    def get_variable(self, name):
        if name not in self.local_map:
            # Create a variable with the given name
            # TODO: for now i64 is assumed to be the only type!
            mem = self.emit(ir.Alloc('alloc_{}'.format(name), 8, 8))
            addr = self.emit(ir.AddressOf(mem, 'addr_{}'.format(name)))
            self.local_map[name] = Var(addr, True, ir.i64)
        return self.local_map[name]

    def gen_function(self, df):
        """ Transform a python function into an IR-function """
        self.local_map = {}

        function_name = df.name
        dbg_int = debuginfo.DebugBaseType('int', 8, 1)
        return_type = self.get_ty(df.returns)
        if return_type:
            ir_function = self.builder.new_function(function_name, return_type)
        else:
            ir_function = self.builder.new_procedure(function_name)
        dbg_args = []
        arg_types = []
        for arg in df.args.args:
            if not arg.annotation:
                self.error(arg, 'Need type annotation for {}'.format(arg.arg))
            aty = self.get_ty(arg.annotation)
            arg_types.append(aty)
            arg_name = arg.arg

            # Debug info:
            param = ir.Parameter(arg_name, aty)
            dbg_args.append(debuginfo.DebugParameter(arg_name, dbg_int))

            ir_function.add_parameter(param)

        # Register function as known:
        self.function_map[function_name] = ir_function, return_type, arg_types

        self.logger.debug('Created function %s', ir_function)
        self.builder.block_number = 0
        self.builder.set_function(ir_function)

        dfi = debuginfo.DebugFunction(
            ir_function.name,
            SourceLocation('foo.py', 1, 1, 1),
            dbg_int,
            dbg_args)
        self.debug_db.enter(ir_function, dfi)

        first_block = self.builder.new_block()
        self.builder.set_block(first_block)
        ir_function.entry = first_block

        # Copy the parameters to variables (so they can be modified):
        for parameter in ir_function.arguments:
            # self.local_map[name] = Var(param, False, aty)
            para_var = self.get_variable(parameter.name)
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
        elif isinstance(statement, ast.Pass):
            pass  # No comments :)
        elif isinstance(statement, ast.Return):
            value = self.gen_expr(statement.value)
            self.emit(ir.Return(value))
            void_block = self.builder.new_block()
            self.builder.set_block(void_block)
        elif isinstance(statement, ast.If):
            ja_block = self.builder.new_block()
            else_block = self.builder.new_block()
            continue_block = self.builder.new_block()
            self.gen_cond(statement.test, ja_block, else_block)

            # Yes
            self.builder.set_block(ja_block)
            self.gen_statement(statement.body)
            self.emit(ir.Jump(continue_block))

            # Else:
            self.builder.set_block(else_block)
            self.gen_statement(statement.orelse)
            self.emit(ir.Jump(continue_block))

            self.builder.set_block(continue_block)
        elif isinstance(statement, ast.While):
            if statement.orelse:
                self.error(statement, 'while-else not supported')
            test_block = self.builder.new_block()
            body_block = self.builder.new_block()
            continue_block = self.builder.new_block()

            # Test:
            self.emit(ir.Jump(test_block))
            self.builder.set_block(test_block)
            self.gen_cond(statement.test, body_block, continue_block)

            # Body:
            self.block_stack.append(continue_block)
            self.builder.set_block(body_block)
            self.gen_statement(statement.body)
            self.emit(ir.Jump(test_block))
            self.block_stack.pop()

            # The end:
            self.builder.set_block(continue_block)
        elif isinstance(statement, ast.Break):
            unreachable_block = self.builder.new_block()
            break_block = self.block_stack[-1]
            self.emit(ir.Jump(break_block))
            self.builder.set_block(unreachable_block)
        elif isinstance(statement, ast.For):
            # Check else-clause:
            if statement.orelse:
                self.error(statement, 'for-else not supported')

            # Allow for loop with range in it:
            if not isinstance(statement.iter, ast.Call):
                self.error(statement.iter, 'Only range supported in for loops')

            if statement.iter.func.id != 'range':
                self.error(statement.iter, 'Only range supported in for loops')

            # Determine start and end values:
            ra = statement.iter.args
            if len(ra) == 1:
                i_init = self.emit(ir.Const(0, 'i_init', ir.i64))
                n2 = self.gen_expr(ra[0])
            elif len(ra) == 2:
                i_init = self.gen_expr(ra[0])
                n2 = self.gen_expr(ra[1])
            else:
                self.error(
                    statement.iter,
                    'Does not support {} arguments'.format(len(ra)))

            entry_block = self.builder.block
            test_block = self.builder.new_block()
            body_block = self.builder.new_block()
            continue_block = self.builder.new_block()

            self.emit(ir.Jump(test_block))

            # Test block:
            self.builder.set_block(test_block)
            i_phi = self.emit(ir.Phi('i_phi', ir.i64))
            i_phi.set_incoming(entry_block, i_init)
            self.emit(ir.CJump(i_phi, '<', n2, body_block, continue_block))

            # Publish looping variable:
            self.local_map[statement.target.id] = Var(i_phi, False, ir.i64)

            # Body:
            self.block_stack.append(continue_block)
            self.builder.set_block(body_block)
            self.gen_statement(statement.body)
            self.block_stack.pop()

            # Increment loop variable:
            one = self.emit(ir.Const(1, 'one', ir.i64))
            i_inc = self.emit(ir.add(i_phi, one, 'i_inc', ir.i64))
            i_phi.set_incoming(body_block, i_inc)

            # Jump to start again:
            self.emit(ir.Jump(test_block))

            # The end:
            self.builder.set_block(continue_block)
        elif isinstance(statement, ast.Assign):
            assert len(statement.targets) == 1
            name = statement.targets[0].id
            var = self.get_variable(name)
            assert var.lvalue
            value = self.gen_expr(statement.value)
            self.emit(ir.Store(value, var.value))
        elif isinstance(statement, ast.Expr):
            self.gen_expr(statement.value)
        elif isinstance(statement, ast.AugAssign):
            name = statement.target.id
            assert isinstance(name, str)
            var = self.get_variable(name)
            assert var.lvalue
            lhs = self.emit(ir.Load(var.value, 'load', var.ty))
            rhs = self.gen_expr(statement.value)
            op = self.binop_map[type(statement.op)]
            value = self.emit(ir.Binop(lhs, op, rhs, 'augassign', var.ty))
            self.emit(ir.Store(value, var.value))
        else:  # pragma: no cover
            self.not_impl(statement)

    def gen_cond(self, c, yes_block, no_block):
        if isinstance(c, ast.Compare):
            # print(dir(c), c.ops, c.comparators)
            assert len(c.ops) == len(c.comparators)
            assert len(c.ops) == 1
            op_map = {
                ast.Gt: '>', ast.Lt: '<',
                ast.Eq: '=', ast.NotEq: '!=',
            }

            a = self.gen_expr(c.left)
            op = op_map[type(c.ops[0])]
            b = self.gen_expr(c.comparators[0])
            self.emit(ir.CJump(a, op, b, yes_block, no_block))
        else:  # pragma: no cover
            self.not_impl(c)

    binop_map = {
        ast.Add: '+', ast.Sub: '-',
        ast.Mult: '*', ast.Div: '/',
    }

    def gen_expr(self, expr):
        """ Generate code for a single expression """
        if isinstance(expr, ast.BinOp):
            a = self.gen_expr(expr.left)
            b = self.gen_expr(expr.right)
            op = self.binop_map[type(expr.op)]
            value = self.emit(ir.Binop(a, op, b, 'add', ir.i64))
        elif isinstance(expr, ast.Name):
            var = self.local_map[expr.id]
            if var.lvalue:
                value = self.emit(ir.Load(var.value, 'load', ir.i64))
            else:
                value = var.value
        elif isinstance(expr, ast.Num):
            value = self.emit(ir.Const(expr.n, 'num', ir.i64))
        elif isinstance(expr, ast.Call):
            assert isinstance(expr.func, ast.Name)
            name = expr.func.id

            # Lookup function and check types:
            ir_function, return_type, arg_types = self.function_map[name]
            self.logger.warning('Function arguments not type checked!')

            # Evaluate arguments:
            args = [self.gen_expr(a) for a in expr.args]

            # Emit call:
            if return_type:
                value = self.emit(ir.FunctionCall(
                    ir_function, args, 'res', return_type))
            else:
                self.emit(ir.ProcedureCall(ir_function, args))
                value = None
        else:  # pragma: no cover
            self.not_impl(expr)
        return value

    def not_impl(self, node):  # pragma: no cover
        print(dir(node))
        self.error(node, 'Cannot do {}'.format(node))

    def error(self, node, message):
        """ Raise a nice error message as feedback """
        location = SourceLocation(
            self._filename, node.lineno, node.col_offset + 1, 1)
        raise CompilerError(message, location)
