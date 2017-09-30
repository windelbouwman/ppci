from ... import ir
from ...binutils import debuginfo
from .python2ir import python_to_ir


def load_py(f, functions=None, reporter=None):
    """ Load a type annotated python file.

    Args:
        f: a file like object containing the python source code.
    """
    from ... import api
    from ...utils.codepage import load_obj

    mod = python_to_ir(f, functions=functions)
    # txt = io.StringIO()
    # writer = irutils.Writer(txt)
    # writer.write(mod)
    # print(txt.getvalue())
    callbacks = []
    if functions:
        for name, fn, return_type, arg_types in functions:
            return_type = ir_to_dbg(return_type)
            arg_types = [ir_to_dbg(a) for a in arg_types]
            callbacks.append((name, fn, return_type, arg_types))

    arch = api.get_current_arch()
    obj = api.ir_to_object(
        [mod], arch, debug=True, reporter=reporter)
    m2 = load_obj(obj, callbacks=callbacks)
    return m2


def ir_to_dbg(typ):
    if typ is None:
        return
    mp = {
        ir.i64: debuginfo.DebugBaseType('int', 8, 1),
        ir.f64: debuginfo.DebugBaseType('double', 8, 1),
    }
    return mp[typ]
