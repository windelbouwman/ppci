""" Python to ppci conversion.

"""

import logging
import ast
from .. import ir, irutils, api
from ..common import SourceLocation
from ..binutils import debuginfo


def load_py(f, functions=None):
    """ Load a type annotated python file.

    arguments:
    f: a file like object containing the python source code.
    """
    from ..import api
    from .codepage import load_obj

    logging.basicConfig(level=logging.DEBUG)
    debug_db = debuginfo.DebugDb()
    mod = P2P(debug_db).compile(f)
    # txt = io.StringIO()
    # writer = irutils.Writer(txt)
    # writer.write(mod)
    # print(txt.getvalue())
    arch = api.get_current_platform()
    obj = api.ir_to_object([mod], arch, debug_db=debug_db, debug=True)
    m2 = load_obj(obj)
    return m2


def py_to_ir(f):
    """ Compile a piece of python code to an ir module.

    Args:
        f (file-like-object): a file like object containing the python code

    Returns:
        A :class:`ppci.ir.Module` module
    """
    debug_db = debuginfo.DebugDb()
    mod = P2P(debug_db).compile(f)
    return mod


class Var:
    def __init__(self, value, lvalue):
        self.value = value
        self.lvalue = lvalue


class P2P:
    """ Not peer-to-peer but python to ppci :) """
    logger = logging.getLogger('p2p')

    def __init__(self, debug_db):
        self.debug_db = debug_db

    def compile(self, f):
        src = f.read()
        # Parse python code:
        x = ast.parse(src)

        self.builder = irutils.Builder()
        self.builder.prepare()
        self.builder.set_module(ir.Module('foo'))
        for df in x.body:
            self.logger.debug('Processing %s', df)
            if isinstance(df, ast.FunctionDef):
                self.gen_function(df)
            else:
                raise NotImplementedError('Cannot do!'.format(df))
        mod = self.builder.module
        irutils.Verifier().verify(mod)
        return mod

    def emit(self, i):
        self.builder.emit(i)
        return i

    def get_ty(self, annotation):
        # TODO: assert isinstance(annotation, ast.Annotation)
        type_mapping = {
            'int': ir.i64,
            'float': ir.f64,
        }
        type_name = annotation.id
        if type_name in type_mapping:
            return type_mapping[type_name]
        else:
            raise Exception('Need to return int')

    def get_variable(self, name):
        if name not in self.local_map:
            # Create a variable with the given name
            mem = self.emit(ir.Alloc('alloc_{}'.format(name), 8))
            self.local_map[name] = Var(mem, True)
        return self.local_map[name]

    def gen_function(self, df):
        self.local_map = {}

        dbg_int = debuginfo.DebugBaseType('int', 8, 1)
        ir_function = self.builder.new_function(df.name, self.get_ty(df.returns))
        dbg_args = []
        for arg in df.args.args:
            if not arg.annotation:
                raise Exception('Need type annotation for {}'.format(arg.arg))
            aty = self.get_ty(arg.annotation)
            name = arg.arg

            # Debug info:
            param = ir.Parameter(name, aty)
            dbg_args.append(debuginfo.DebugParameter(name, dbg_int))

            self.local_map[name] = Var(param, False)
            ir_function.add_parameter(param)
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

        self.gen_statement(df.body)

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

            self.builder.set_block(ja_block)
            self.gen_statement(statement.body)
            self.emit(ir.Jump(continue_block))

            self.builder.set_block(else_block)
            self.gen_statement(statement.orelse)
            self.emit(ir.Jump(continue_block))

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
        else:  # pragma: no cover
            print(dir(statement))
            raise NotImplementedError('Cannot Do {}'.format(statement))

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
            raise NotImplementedError('Cannot Do {}'.format(statement))

    def gen_expr(self, expr):
        """ Generate code for a single expression """
        if isinstance(expr, ast.BinOp):
            a = self.gen_expr(expr.left)
            b = self.gen_expr(expr.right)
            op_map = {
                ast.Add: '+', ast.Sub: '-',
                ast.Mult: '*', ast.Div: '/',
            }
            op = op_map[type(expr.op)]
            v = self.emit(ir.Binop(a, op, b, 'add', ir.i64))
            return v
        elif isinstance(expr, ast.Name):
            var = self.local_map[expr.id]
            if var.lvalue:
                value = self.emit(ir.Load(var.value, 'load', ir.i64))
            else:
                value = var.value
            return value
        elif isinstance(expr, ast.Num):
            return self.emit(ir.Const(expr.n, 'num', ir.i64))
        else:  # pragma: no cover
            raise NotImplementedError('Todo: {}'.format(expr))
