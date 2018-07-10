"""
Compile a very strict subset of Python (in which the only types are floats)
to WASM.
"""

import ast
import inspect
import types

from ...common import SourceLocation, CompilerError
from ...wasm import Module, Func


def syntax_error(filename, node, message):
    """ Raise a nice error message as feedback """
    location = SourceLocation(filename, node.lineno, node.col_offset + 1, 1)
    raise CompilerError(message, location)


def python_to_wasm(*sources):
    """ Compile Python functions to wasm, by using Python's ast parser
    and compiling a very specific subset to WASM instructions. All values 
    are float64. Each source can be a string, a function, or AST.
    """
    
    # Allow simple code snippet as main() (legacy behavior)
    if len(sources) == 1 and isinstance(sources[0], str) and not 'def ' in sources[0]:
        lines = ['def main():'] + ['    ' + line for line in sources[0].splitlines()]
        sources = ['\n'.join(lines)]
    
    # Collect funcdefs
    funcdefs = []
    for source in sources:
        funcdefs.extend(_python_to_wasm_funcdefs(source))
    
    # Produce wasm module
    module = Module(
        '(import "env" "f64_print" (func $print (param f64)))',
        *funcdefs)
    return module


def _python_to_wasm_funcdefs(source):
    
    filename = None
    # Verify / convert input
    if isinstance(source, ast.AST):
        root = source
    elif isinstance(source, str):
        root = ast.parse(source)
    elif isinstance(source, (types.FunctionType, types.MethodType)):
        try:
            filename = inspect.getsourcefile(source)
            lines, linenr = inspect.getsourcelines(source)
        except Exception as err:
            raise ValueError('Could not get source for %r: %s' % (source, err))
        if getattr(source, '__name__', '') in ('', '<lambda>'):
            raise ValueError('Got anonymous function from '
                             '"%s", line %i, %r.' % (filename, linenr, source))
        # Normalize indentation, based on first line
        indent = len(lines[0]) - len(lines[0].lstrip())
        for i in range(len(lines)):
            line = lines[i]
            line_indent = len(line) - len(line.lstrip())
            if line_indent < indent and line.strip():
                assert line.lstrip().startswith('#')  # only possible for comments
                lines[i] = indent * ' ' + line.lstrip()
            else:
                lines[i] = line[indent:]
        # Skip any decorators
        while not lines[0].lstrip().startswith('def '):
            lines.pop(0)
        # join lines and rename
        root = ast.parse(''.join(lines))
    else:
        raise TypeError('python_to_wasm() requires func, str, or AST.')

    if not isinstance(root, ast.Module):
        raise ValueError(
            'python_to_wasm() expecteded root node to be a ast.Module.')
    
    funcdefs = []
    
    # Iterate over content
    for node in root.body:
        if not isinstance(node, ast.FunctionDef):
            syntax_error(filename, node,
                'python_to_wasm() expects only func as toplevel nodes.')
        # Checks
        if node.args.defaults or node.args.vararg:
            syntax_error(filename, node,
                'python_to_wasm() func args cannot have defaults.')
        if node.args.kwonlyargs or node.args.kwonlyargs:
            syntax_error(filename, node,
                'python_to_wasm() func cannot have keyword wargs.')
        assert node.name.isidentifier()
        # Get instructions, params, results, and export
        ctx = PythonFuncToWasmCompiler([a.arg for a in node.args.args], filename)
        ctx.compile_body(node.body)
        # Compose
        params = [('param', 'f64') for a in node.args.args]
        results = [('result', 'f64')] if ctx.returns else []
        locals = [('local', 'f64')
                  for i in range(len(ctx.names) - len(node.args.args))]
        exports = [('export', node.name)]
        funcdefs.append(tuple(['func', '$' + node.name] +
            exports + params + results + locals + ctx.instructions))
        # Main?
        if node.name == 'main':
            funcdefs.append(('start', '$main'))
    
    return funcdefs


class PythonFuncToWasmCompiler:
    """ Compiles one Python function body to wasm instructions.
    """
    
    def __init__(self, args, filename=None):
        self._filename = filename
        self.instructions = []
        self.names = {}
        self._name_counter = 0
        self._block_stack = []
        self.returns = False  # Whether this function returns something
        # Init args
        for name in args:
            self.name_idx(name)
    
    def compile_body(self, body):
        for node in body:
            self._compile_expr(node, False)
    
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
            #self.instructions.append(('if', 'emptyblock'))
            self.instructions.append('if')
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
                    'block',  #('block', 'emptyblock'),
                    'loop',  #('loop', 'emptyblock'),  # enter loop
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
            #for i in [('block', 'emptyblock'), ('loop', 'emptyblock')]:
            for i in ['block', 'loop']:
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
            self.returns = True

        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                self.syntax_error(node, 'Only support simple function names')
            if node.keywords:
                self.syntax_error(node, 'No support for keyword args')
            # We assume that the function is known. Can be imported or
            # compiled along with this function.
            # Push args on stack, then call
            for arg in node.args:
                self._compile_expr(arg, True)
            name = node.func.id
            self.instructions.append(('call', '$' + name))
        else:
            self.syntax_error(
                node, 'Unsupported syntax: %s' % node.__class__.__name__)

    def syntax_error(self, node, message):
        syntax_error(self._filename, node, message)
