from ...binutils import debuginfo
from .python2ir import python_to_ir


def load_py(f, functions=None):
    """ Load a type annotated python file.

    Args:
        f: a file like object containing the python source code.
    """
    from ... import api
    from ...utils.codepage import load_obj

    debug_db = debuginfo.DebugDb()
    mod = python_to_ir(f, functions=functions, debug_db=debug_db)
    # txt = io.StringIO()
    # writer = irutils.Writer(txt)
    # writer.write(mod)
    # print(txt.getvalue())
    if functions:
        for name, fn in functions.items():
            get_ty(fn)

    arch = api.get_current_arch()
    obj = api.ir_to_object([mod], arch, debug_db=debug_db, debug=True)
    m2 = load_obj(obj)
    return m2
