"""
Compile a very strict subset of Python (in which the only types are floats)
to WASM.
"""

import ast

from ...common import SourceLocation, CompilerError
from ...irs.wasm.highlevel import ImportedFuncion, Function, make_module


def python_to_wasm(code):
    """ Compile Python code to wasm, by using Python's ast parser
    and compiling a very specific subset to WASM instructions.
    """
    # Verify / convert input
    if isinstance(code, ast.AST):
        root = code
    elif isinstance(code, str):
        root = ast.parse(code)
    else:
        raise TypeError('py_to_wasm() requires (str) code or AST.')

    if not isinstance(root, ast.Module):
        raise ValueError(
            'py_to_wasm() expecteded root node to be a ast.Module.')

    # Compile to instructions
    ctx = PythonToWasmCompiler()
    for node in root.body:
        ctx._compile_expr(node, False)
    locals = ['f64' for i in ctx.names]

    # Produce wasm
    module = make_module([
        ImportedFuncion('print_ln', ['f64'], [], 'js', 'print_ln'),
        ImportedFuncion(
            'perf_counter', [], ['f64'], 'js', 'perf_counter'),
        Function('$main', [], ['f64'], locals, ctx.instructions),
        ])
    return module


class PythonToWasmCompiler:
    """ Transpiler from python wasm """
    def __init__(self):
        self._filename = None
        self.instructions = []
        self.names = {}
        self._name_counter = 0
        self._block_stack = []

    def name_idx(self, name):
        if name not in self.names:
            self.names[name] = self._name_counter
            self._name_counter += 1
        return self.names[name]

    def new_stub(self):
        name = 'stub' + str(self._name_counter)
        return self.name_idx(name)

    def push_block(self, kind):
        assert kind in ('if', 'for', 'while')
        self._block_stack.append(kind)

    def pop_block(self, kind):
        assert self._block_stack.pop(-1) == kind

    def get_block_level(self):
        for i, kind in enumerate(reversed(self._block_stack)):
            if kind in ('for', 'while'):
                return i

    def _compile_expr(self, node, push_stack):
        """ Generate wasm instruction for the given ast node """
        if isinstance(node, ast.Expr):
            self._compile_expr(node.value, push_stack)

        elif isinstance(node, ast.Assign):
            if not (len(node.targets) == 1 and
                    isinstance(node.targets[0], ast.Name)):
                self.syntax_error(node, 'Unsupported assignment')
            idx = self.name_idx(node.targets[0].id)
            self._compile_expr(node.value, True)
            self.instructions.append(('set_local', idx))
            assert not push_stack

        elif isinstance(node, ast.Name):
            assert push_stack
            self.instructions.append(('get_local', self.name_idx(node.id)))

        elif isinstance(node, ast.Num):
            self.instructions.append(('f64.const', node.n))

        elif isinstance(node, ast.UnaryOp):
            self._compile_expr(node.operand, True)
            if isinstance(node.op, ast.USub):
                self.instructions.append(('f64.neg',))
            else:
                self.syntax_error(
                    node, 'Unsupported unary operator: {}'.format(node.op))

        elif isinstance(node, ast.BinOp):
            self._compile_expr(node.left, True)
            self._compile_expr(node.right, True)
            if isinstance(node.op, ast.Add):
                self.instructions.append(('f64.add',))
            elif isinstance(node.op, ast.Sub):
                self.instructions.append(('f64.sub',))
            elif isinstance(node.op, ast.Mult):
                self.instructions.append(('f64.mul',))
            elif isinstance(node.op, ast.Div):
                self.instructions.append(('f64.div',))
            elif isinstance(node.op, ast.Mod):
                # todo: this is fragile. E.g. for negative numbers
                self._compile_expr(node.left, True)  # push again
                self._compile_expr(node.right, True)
                self.instructions.append(('f64.div',))
                self.instructions.append(('f64.floor',))
                self.instructions.append(('f64.mul',))  # consumes last right
                self.instructions.append(('f64.sub',))  # consumes last left
            elif isinstance(node.op, ast.FloorDiv):
                self.instructions.append(('f64.div',))
                self.instructions.append(('f64.floor',))  # not trunc
            else:
                self.syntax_error(node, 'Unsuppored binary op: %s' % node.op)

            if not push_stack:
                self.instructions.append(('drop',))

        elif isinstance(node, ast.Compare):
            if len(node.ops) != 1:
                self.syntax_error(
                    node, 'Only supports binary comparators (one operand).')
            self._compile_expr(node.left, True)
            self._compile_expr(node.comparators[0], True)
            op = node.ops[0]
            if isinstance(op, ast.Eq):
                self.instructions.append(('f64.eq',))
            elif isinstance(op, ast.NotEq):
                self.instructions.append(('f64.ne',))
            elif isinstance(op, ast.Gt):
                self.instructions.append(('f64.gt',))
            elif isinstance(op, ast.Lt):
                self.instructions.append(('f64.lt',))
            elif isinstance(op, ast.GtE):
                self.instructions.append(('f64.ge',))
            elif isinstance(op, ast.LtE):
                self.instructions.append(('f64.le',))
            else:
                self.syntax_error(node, 'Unsupported operand: %s' % op)

        elif isinstance(node, ast.If):
            self._compile_expr(node.test, True)
            assert not push_stack  # Python is not an expression lang
            self.push_block('if')
            self.instructions.append(('if', 'emptyblock'))
            for e in node.body:
                self._compile_expr(e, False)
            if node.orelse:
                self.instructions.append(('else', ))
                for e in node.orelse:
                    self._compile_expr(e, False)
            self.instructions.append(('end', ))
            self.pop_block('if')

        elif isinstance(node, ast.For):
            # Check whether this is the kind of simple for-loop that we support
            if not (isinstance(node.iter, ast.Call)
                    and node.iter.func.id == 'range'):
                self.syntax_error(node, 'For-loops are limited to range().')

            if node.orelse:
                self.syntax_error(node, 'For-loops do not support orelse.')

            if not isinstance(node.target, ast.Name):
                self.syntax_error(node, 'For-loops support just one iterable.')

            # Prepare start, stop, step
            start_stub = self.new_stub()
            end_stub = self.new_stub()
            step_stub = self.new_stub()
            if len(node.iter.args) == 1:
                self.instructions.append(('f64.const', 0))
                self._compile_expr(node.iter.args[0], True)
                self.instructions.append(('f64.const', 1))
            elif len(node.iter.args) == 2:
                self._compile_expr(node.iter.args[0], True)
                self._compile_expr(node.iter.args[1], True)
                self.instructions.append(('f64.const', 1))
            elif len(node.iter.args) == 3:
                self._compile_expr(node.iter.args[0], True)
                self._compile_expr(node.iter.args[1], True)
                self._compile_expr(node.iter.args[2], True)
            else:
                self.syntax_error(
                    node.iter, 'range() should have 1, 2, or 3 args')

            # reversed order, pop from stack
            self.instructions.append(('set_local', step_stub))
            self.instructions.append(('set_local', end_stub))
            self.instructions.append(('set_local', start_stub))

            # Body
            target = self.name_idx(node.target.id)
            self.push_block('for')
            for i in [
                    ('get_local', start_stub),
                    ('set_local', target),  # Init target
                    ('block', 'emptyblock'),
                    ('loop', 'emptyblock'),  # enter loop
                    ('get_local', target),
                    ('get_local', end_stub),
                    ('f64.ge',), ('br_if', 1),  # break (level 2)
                    ]:
                self.instructions.append(i)
            for subnode in node.body:
                self._compile_expr(subnode, False)

            for i in [('get_local', target),
                      ('get_local', step_stub),
                      ('f64.add',),
                      ('set_local', target),  # next iter
                      ('br', 0),  # loop
                      ('end',), ('end',),  # end of loop and outer block
                      ]:
                self.instructions.append(i)
            self.pop_block('for')

        elif isinstance(node, ast.While):
            # Check whether this is the kind of simple for-loop that we support
            if node.orelse:
                self.syntax_error(node, 'While-loops do not support orelse.')

            # Body
            self.push_block('while')
            # enter loop (outer block for break):
            for i in [('block', 'emptyblock'), ('loop', 'emptyblock')]:
                self.instructions.append(i)
            for subnode in node.body:
                self._compile_expr(subnode, False)
            self._compile_expr(node.test, True)
            for i in [('br_if', 0),  # loop
                      ('end',), ('end',),  # end of loop
                      ]:
                self.instructions.append(i)
            self.pop_block('while')

        elif isinstance(node, ast.Pass):
            pass

        elif isinstance(node, ast.Continue):
            self.instructions.append(('br', self.get_block_level()))

        elif isinstance(node, ast.Break):
            self.instructions.append(('br', self.get_block_level() + 1))

        elif isinstance(node, ast.Return):
            assert node.value is not None
            self._compile_expr(node.value, True)
            self.instructions.append(('return', ))

        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                self.syntax_error(node, 'Only support simple function names')

            if node.keywords:
                self.syntax_error(node, 'No support for keyword args')

            name = node.func.id
            if name == 'print':
                if len(node.args) != 1:
                    self.syntax_error(
                        node, 'print() accepts exactly one argument')
                self._compile_expr(node.args[0], True)
                self.instructions.append(('call', 0))
            elif name == 'perf_counter':
                if len(node.args) != 0:
                    self.syntax_error(
                        node, 'perf_counter() accepts exactly zero arguments')
                self.instructions.append(('call', 1))
            else:
                self.syntax_error(node, 'Not a supported function: %s' % name)
        else:
            self.syntax_error(
                node, 'Unsupported syntax: %s' % node.__class__.__name__)

    def syntax_error(self, node, message):
        """ Raise a nice error message as feedback """
        location = SourceLocation(
            self._filename, node.lineno, node.col_offset + 1, 1)
        raise CompilerError(message, location)
