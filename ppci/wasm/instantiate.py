""" Provide function to load a wasm module into the current process. """

from ..api import ir_to_object, get_current_arch
from ..utils.codepage import load_obj
from . import wasm_to_ir
from .components import Export

__all__ = ('instantiate',)


def instantiate(module, imports):
    """ Instantiate a wasm module.
    """
    ppci_module = wasm_to_ir(module)
    arch = get_current_arch()
    obj = ir_to_object([ppci_module], arch, debug=True)
    instance = ModuleInstance()
    instance._module = load_obj(obj, imports=flatten_imports(imports))
    # Export all exported functions
    i = 0
    for definition in module:
        if isinstance(definition, Export):
            if definition.kind != 'func':
                raise NotImplementedError(definition.kind)
            exported_name = definition.name
            ppci_id = str(i)
            # wasm_id = definition.ref  # not used here (int or str starting with $)
            # TODO: why is ppci_id a number? This is incorrect.
            # AK: Dunno, that's what wasm2ppci does, I guess
            setattr(
                instance.exports, exported_name,
                getattr(instance._module, ppci_id))
            i += 1

    return instance


def flatten_imports(imports):
    """ Go from a two level dict to a single level dict """
    flat_imports = {}
    for mod_name, funcs in imports.items():
        for func_name, func in funcs.items():
            flat_imports['{}_{}'.format(mod_name, func_name)] = func
    return flat_imports


class ModuleInstance:
    def __init__(self):
        self.exports = Exports()


class Exports:
    pass
