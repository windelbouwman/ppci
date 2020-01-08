""" Link two ir-modules, such that external references are resolved.

"""

from .. import ir
from .verify import verify_module


def ir_link(ir_modules, name="linked") -> ir.Module:
    """ Link IR-modules into a single module.

    Example:

    .. doctest::

        >>> from ppci import ir
        >>> from ppci.irutils import ir_link
        >>> m1 = ir.Module('m1')
        >>> m2 = ir.Module('m2')
        >>> m3 = ir_link([m1, m2])

    Note that the original modules are not usable after this action.

    TODO: TBD: do not modify source modules?
    """
    mod0 = ir.Module(name)

    # Add all variables and functions:
    for module in ir_modules:
        for variable in module.variables:
            mod0.add_variable(variable)

        for p in module.functions:
            mod0.add_function(p)

    # Add externals, if not already resolved:
    internal_functions = {p.name: p for p in mod0.functions}
    for module in ir_modules:
        for external in module.externals:
            if isinstance(external, ir.ExternalSubRoutine):
                # TODO: check argument similarity?
                if external.name in internal_functions:
                    p = internal_functions[external.name]
                    external.replace_by(p)
                else:
                    mod0.add_external(external)
                    internal_functions[external.name] = external
            else:
                # TODO: link external variables?
                mod0.add_external(external)
                internal_functions[external.name] = external

    # Verify, just to be sure:
    verify_module(mod0)
    return mod0
