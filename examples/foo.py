
import logging
import ast
import io
from ppci import ir, irutils, api
from ppci.common import SourceLocation
from ppci.binutils import debuginfo
from ppci.utils.codepage import load_obj
import demo1

demo2 = '''
def a(x: int, y: int) -> int:
    return x - y + 100
'''

with open('demo1.py', 'r') as f:
    demo = f.read()


class P2P:
    def __init__(self, debug_db):
        self.debug_db = debug_db

    def compile(self, src):
        # Parse python code:
        x = ast.parse(src)
        logger = logging.getLogger()

        self.builder = irutils.Builder()
        self.builder.prepare()
        self.builder.set_module(ir.Module('foo'))
        for df in x.body:
            logger.debug('Processing %s', df)
            if isinstance(df, ast.FunctionDef):
                self.gen_function(df)
            else:
                raise NotImplementedError('Cannot do!'.format(df))
        mod = self.builder.module
        irutils.Verifier().verify(mod)
        txt = io.StringIO()
        writer = irutils.Writer(txt)
        writer.write(mod)
        print(txt.getvalue())
        return mod

    def emit(self, i):
        self.builder.emit(i)
        return i

    def get_ty(self, annotation):
        # TODO: assert isinstance(annotation, ast.Annotation)
        if annotation.id != 'int':
            raise Exception('Need to return int')
        return ir.i64

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

            self.local_map[name] = param
            ir_function.add_parameter(param)
        print(ir_function)
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
        else:
            raise NotImplementedError('Cannot Do {}'.format(statement))

    def gen_cond(self, c, yes_block, no_block):
        if isinstance(c, ast.Compare):
            # print(dir(c), c.ops, c.comparators)
            assert len(c.ops) == len(c.comparators)
            assert len(c.ops) == 1
            op_map = {
                ast.Gt: '>', ast.Lt: '<'
            }

            a = self.gen_expr(c.left)
            op = op_map[type(c.ops[0])]
            b = self.gen_expr(c.comparators[0])
            self.emit(ir.CJump(a, op, b, yes_block, no_block))
        else:
            raise NotImplementedError('Cannot Do {}'.format(statement))
        
    def gen_expr(self, expr):
        if isinstance(expr, ast.BinOp):
            a = self.gen_expr(expr.left)
            b = self.gen_expr(expr.right)
            op_map = {
                ast.Add: '+', ast.Sub: '-',
            }
            op = op_map[type(expr.op)]
            v = self.emit(ir.Binop(a, op, b, 'add', ir.i64))
            return v
        elif isinstance(expr, ast.Name):
            return self.local_map[expr.id]
        elif isinstance(expr, ast.Num):
            return self.emit(ir.Const(expr.n, 'num', ir.i64))
        else:
            raise NotImplementedError('Todo: {}'.format(e))


logging.basicConfig(level=logging.DEBUG)
debug_db = debuginfo.DebugDb()
mod = P2P(debug_db).compile(demo)
obj1 = api.ir_to_object([mod], 'x86_64', debug_db=debug_db, debug=True)
obj = api.link([obj1], debug=True)
m2 = load_obj(obj)
for x in range(20):
    print(x, m2.a(x, 2), demo1.a(x, 2))
