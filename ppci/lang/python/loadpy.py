import inspect
import io
from ... import ir
from ...binutils import debuginfo
from .python2ir import python_to_ir


def load_py(f, imports=None, reporter=None):
    """ Load a type annotated python file.

    Args:
        f: a file like object containing the python source code.
    """
    from ... import api
    from ...utils.codepage import load_obj

    mod = python_to_ir(f, imports=imports)

    arch = api.get_current_arch()
    obj = api.ir_to_object(
        [mod], arch, debug=True, reporter=reporter)
    m2 = load_obj(obj, imports=imports)
    return m2


class JittedFunction:
    """ This is a wrapper around a compiled function. """
    def __init__(self, original, compiled, mod):
        self.original = original
        self.compiled = compiled
        self.mod = mod

    def __call__(self, *args):
        return self.compiled.__call__(*args)


def jit(function):
    """ Jitting function decorator.

    Can be used to just-in-time (jit) compile and load a function. When
    a function is decorated with this decorator, the python code is translated
    into machine code and this code is loaded in the current process.

    For example:

    .. testcode:: jit

        from ppci.lang.python import jit

        @jit
        def heavymath(a: int, b: int) -> int:
            return a + b

    Now the function can be used as before:

    .. doctest:: jit

        >>> heavymath(2, 7)
        9

    """
    source = inspect.getsource(function)
    mod = load_py(io.StringIO(source))
    name = function.__name__
    return JittedFunction(function, getattr(mod, name), mod)


def ir_to_dbg(typ):
    if typ is None:
        return
    mp = {
        ir.i64: debuginfo.DebugBaseType('int', 8, 1),
        ir.f64: debuginfo.DebugBaseType('double', 8, 1),
    }
    return mp[typ]
