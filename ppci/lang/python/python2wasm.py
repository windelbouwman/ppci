"""
Compile a very strict subset of Python (in which the only types are floats)
to WASM.
"""

from time import time as perf_counter  # cause perf_counter not available in pypy3
import ast

from ppci.irs import wasm


class Context:
    
    def __init__(self):
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


def py_to_wasm(code):
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
        raise ValueError('py_to_wasm() expecteded root node to be a ast.Module.')
    
    # Compile to instructions
    ctx = Context()
    for node in root.body:
        _compile_expr(node, ctx, False)
    locals = ['f64' for i in ctx.names]
    
    # Produce wasm
    module = wasm.Module(
        wasm.ImportedFuncion('print_ln', ['f64'], [], 'js', 'print_ln'),
        wasm.ImportedFuncion('perf_counter', [], ['f64'], 'js', 'perf_counter'),
        wasm.Function('$main', [], [], locals, ctx.instructions),
        )
    return module


def _compile_expr(node, ctx, push_stack):
    
    if isinstance(node, ast.Expr):
        _compile_expr(node.value, ctx, push_stack)
    
    elif isinstance(node, ast.Assign):
        if not (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)):
            raise SyntaxError('Unsupported assignment at line', node.lineno)
        idx = ctx.name_idx(node.targets[0].id)
        _compile_expr(node.value, ctx, True)
        ctx.instructions.append(('set_local', idx))
        assert not push_stack
    
    elif isinstance(node, ast.Name):
        assert push_stack
        ctx.instructions.append(('get_local', ctx.name_idx(node.id)))
    
    elif isinstance(node, ast.Num):
        ctx.instructions.append(('f64.const', node.n))
    
    elif isinstance(node, ast.UnaryOp):
        _compile_expr(node.operand, ctx, True)
        if isinstance(node.op, ast.USub):
            ctx.instructions.append(('f64.neg'))
        else:
            raise SyntaxError('Unsupported unary operator: %s' % node.op.__class__.__name__)
    
    elif isinstance(node, ast.BinOp):
        _compile_expr(node.left, ctx, True)
        _compile_expr(node.right, ctx, True)
        if isinstance(node.op, ast.Add):
            ctx.instructions.append(('f64.add'))
        elif isinstance(node.op, ast.Sub):
            ctx.instructions.append(('f64.sub'))
        elif isinstance(node.op, ast.Mult):
            ctx.instructions.append(('f64.mul'))
        elif isinstance(node.op, ast.Div):
            ctx.instructions.append(('f64.div'))
        elif isinstance(node.op, ast.Mod):
            # todo: this is fragile. E.g. for negative numbers
            _compile_expr(node.left, ctx, True)  # push again
            _compile_expr(node.right, ctx, True)
            ctx.instructions.append(('f64.div'))
            ctx.instructions.append(('f64.floor'))
            ctx.instructions.append(('f64.mul'))  # consumes last right
            ctx.instructions.append(('f64.sub'))  # consumes last left
        elif isinstance(node.op, ast.FloorDiv):
            ctx.instructions.append(('f64.div'))
            ctx.instructions.append(('f64.floor'))  # not trunc
        else:
            raise SyntaxError('Unsuppored binary op: %s' % node.op.__class__.__name__)
        if not push_stack:
            ctx.instructions.append(('drop'))
    
    elif isinstance(node, ast.Compare):
        if len(node.ops) != 1:
            raise SyntaxError('Only supports binary comparators (one operand).')
        _compile_expr(node.left, ctx, True)
        _compile_expr(node.comparators[0], ctx, True)
        op = node.ops[0]
        if isinstance(op, ast.Eq):
            ctx.instructions.append(('f64.eq'))
        elif isinstance(op, ast.NotEq):
            ctx.instructions.append(('f64.ne'))
        elif isinstance(op, ast.Gt):
            ctx.instructions.append(('f64.gt'))
        elif isinstance(op, ast.Lt):
            ctx.instructions.append(('f64.lt'))
        elif isinstance(op, ast.GtE):
            ctx.instructions.append(('f64.ge'))
        elif isinstance(op, ast.LtE):
            ctx.instructions.append(('f64.le'))
        else:
            raise SyntaxError('Unsupported operand: %s' % op)
    
    elif isinstance(node, ast.If):
        _compile_expr(node.test, ctx, True)
        assert not push_stack  # Python is not an expression lang
        ctx.push_block('if')
        ctx.instructions.append(('if', 'emptyblock'))
        for e in node.body:
            _compile_expr(e, ctx, False)
        if node.orelse:
            ctx.instructions.append(('else', ))
            for e in node.orelse:
                _compile_expr(e, ctx, False)
        ctx.instructions.append(('end', ))
        ctx.pop_block('if')
    
    elif isinstance(node, ast.For):
        # Check whether this is the kind of simple for-loop that we support
        if not (isinstance(node.iter, ast.Call) and node.iter.func.id == 'range'):
            raise SyntaxError('For-loops are limited to range().')
        if node.orelse:
            raise SyntaxError('For-loops do not support orelse.')
        if not isinstance(node.target, ast.Name):
            raise SyntaxError('For-loops support just one iterable.')
        # Prepare start, stop, step
        start_stub = ctx.new_stub()
        end_stub = ctx.new_stub()
        step_stub = ctx.new_stub()
        if len(node.iter.args) == 1:
            ctx.instructions.append(('f64.const', 0))
            _compile_expr(node.iter.args[0], ctx, True)
            ctx.instructions.append(('f64.const', 1))
        elif len(node.iter.args) == 2:
            _compile_expr(node.iter.args[0], ctx, True)
            _compile_expr(node.iter.args[1], ctx, True)
            ctx.instructions.append(('f64.const', 1))
        elif len(node.iter.args) == 3:
            _compile_expr(node.iter.args[0], ctx, True)
            _compile_expr(node.iter.args[1], ctx, True)
            _compile_expr(node.iter.args[2], ctx, True)
        else:
            raise SyntaxError('range() should have 1, 2, or 3 args')
        ctx.instructions.append(('set_local', step_stub))  # reversed order, pop from stack
        ctx.instructions.append(('set_local', end_stub))
        ctx.instructions.append(('set_local', start_stub))
        # Body
        target = ctx.name_idx(node.target.id)
        ctx.push_block('for')
        for i in [('get_local', start_stub), ('set_local', target), # Init target
                  ('block', 'emptyblock'), ('loop', 'emptyblock'),  # enter loop
                  ('get_local', target), ('get_local', end_stub), ('f64.ge'), ('br_if', 1),  # break (level 2)
                  ]:
            ctx.instructions.append(i)
        for subnode in node.body:
            _compile_expr(subnode, ctx, False)
        for i in [('get_local', target), ('get_local', step_stub), ('f64.add'), ('set_local', target),  # next iter
                  ('br', 0),  # loop
                  ('end'), ('end'),  # end of loop and outer block
                  ]:
            ctx.instructions.append(i)
        ctx.pop_block('for')
    
    elif isinstance(node, ast.While):
        # Check whether this is the kind of simple for-loop that we support
        if node.orelse:
            raise SyntaxError('While-loops do not support orelse.')
        # Body
        ctx.push_block('while')
        for i in [('block', 'emptyblock'), ('loop', 'emptyblock'),  # enter loop (outer block for break)
                  ]:
            ctx.instructions.append(i)
        for subnode in node.body:
            _compile_expr(subnode, ctx, False)
        _compile_expr(node.test, ctx, True)
        for i in [('br_if', 0),  # loop
                  ('end'), ('end'),  # end of loop
                  ]:
            ctx.instructions.append(i)
        ctx.pop_block('while')
    
    elif isinstance(node, ast.Pass):
        pass
    
    elif isinstance(node, ast.Continue):
        ctx.instructions.append(('br', ctx.get_block_level()))
    
    elif isinstance(node, ast.Break):
        ctx.instructions.append(('br', ctx.get_block_level() + 1))
    
    elif isinstance(node, ast.Return):
        assert node.value is not None
        _compile_expr(node.value, ctx, True)
        ctx.instructions.append(('return', ))
    
    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise SyntaxError('Only support simple function names')
        if node.keywords:
            raise SyntaxError('No support for keyword args')
        name = node.func.id
        if name == 'print':
            assert len(node.args) == 1, 'print() accepts exactly one argument'
            _compile_expr(node.args[0], ctx, True)
            ctx.instructions.append(('call', 0))
        elif name == 'perf_counter':
            assert len(node.args) == 0, 'perf_counter() accepts exactly zero arguments'
            ctx.instructions.append(('call', 1))
        else:
            raise SyntaxError('Not a supported function: %s' % name)
    else:
        raise SyntaxError('Unsupported syntax: %s' % node.__class__.__name__)
