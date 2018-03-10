""" Provide function to load a wasm module into the current process. """

from ..api import ir_to_object, get_current_arch
from ..utils.codepage import load_obj
from . import wasm_to_ir
from .components import Export


def instantiate(module, imports):
    """ Instantiate a wasm module.
    """
    ppci_module = wasm_to_ir(module)
    arch = get_current_arch()
    obj = ir_to_object([ppci_module], arch, debug=True)
    instance = ModuleInstance()
    instance._module = load_obj(obj, imports=flatten_imports(imports))

    i = 0
    for definition in module:
        if isinstance(definition, Export):
            if definition.kind != 'func':
                raise NotImplementedError(definition.kind)
            # TODO: why are the names numbers? This is incorrect.
            func_name = str(i)
            setattr(
                instance.exports, definition.name,
                getattr(instance._module, func_name))
            i += 1

    instance.exports.main = getattr(instance._module, '0')
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
