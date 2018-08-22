
""" Link two ir-modules, such that external references are resolved.

Example:

>>> import ir
>>> from ir_link import ir_link
>>> m1 = ir.Module('m1')
>>> m2 = ir.Module('m2')
>>> m3 = ir_link([m1, m2])

Note that the original modules are not usable after this action.

TODO: TBD: do not modify source modules?

"""

from . import ir
from .irutils import verify_module


def ir_link(ir_modules, name='linked') -> ir.Module:
    mod0 = ir.Module(name)

    # Add all variables and functions:
    for m in ir_modules:
        for v in m.variables:
            mod0.add_variable(v)
        for p in m.functions:
            mod0.add_function(p)

    # Add externals, if not already resolved:
    internal_functions = {p.name: p for p in mod0.functions}
    for m in ir_modules:
        for e in m.externals:
            if isinstance(e, ir.ExternalSubRoutine):
                if e.name in internal_functions:
                    p = internal_functions[e.name]
                    e.replace_by(p)
                else:
                    mod0.add_external(e)
            else:
                # TODO: link external variables?
                mod0.add_external(e)

    # Verify, just to be sure:
    verify_module(mod0)
    return mod0

