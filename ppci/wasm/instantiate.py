""" Provide function to load a wasm module into the current process.

Note that for this to work, we require compiled wasm code and a runtime.

The wasm runtime contains the following:

- Implement function like sqrt, floor, bit rotations etc..
"""

import io
from types import ModuleType
from ..api import ir_to_object, get_current_arch, ir_to_python
from ..arch.arch_info import TypeInfo
from ..utils.codepage import load_obj
from ..utils.reporting import DummyReportGenerator
from . import wasm_to_ir
from .components import Export, Import
from .wasm2ppci import create_memories

__all__ = ('instantiate',)


def instantiate(module, imports, target='native', reporter=None):
    """ Instantiate a wasm module.

    Args:
        module (ppci.wasm.Module): The wasm-module to instantiate

    """
    if reporter is None:
        reporter = DummyReportGenerator()

    # Check if all required imports are given:
    for definition in module:
        if isinstance(definition, Import):
            modname, name = definition.modname, definition.name
            if modname not in imports:
                raise ValueError(
                    'imported module "{}" not found'.format(modname))
            if name not in imports[modname]:
                raise ValueError(
                    'imported object "{}" not found in "{}"'.format(
                        name, modname))

    imports = flatten_imports(imports)

    if target == 'native':
        instance = native_instantiate(module, imports, reporter)
    elif target == 'python':
        instance = python_instantiate(module, imports, reporter)
    else:
        raise ValueError('Unknown instantiation target'.format(target))

    # Call magic function _run_init which optionally initializes tables and calls start
    instance._run_init()
    return instance


def native_instantiate(module, imports, reporter):
    """ Load wasm module native """
    arch = get_current_arch()
    ppci_module = wasm_to_ir(module, arch.info.get_type_info('ptr'))
    obj = ir_to_object([ppci_module], arch, debug=True, reporter=reporter)
    _module = load_obj(obj, imports=imports)
    instance = NativeModuleInstance(_module)
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

    memories = create_memories(module)
    # TODO: Load memories.

    return instance


def python_instantiate(module, imports, reporter):
    """ Load wasm module as a PythonModuleInstance """
    ptr_info = TypeInfo(4, 4)
    ppci_module = wasm_to_ir(module, ptr_info, reporter=reporter)
    f = io.StringIO()
    ir_to_python([ppci_module], f, reporter=reporter)
    pysrc = f.getvalue()
    # print(pysrc)
    pycode = compile(pysrc, '<string>', 'exec')
    _module = ModuleType('gen')
    exec(pycode, _module.__dict__)
    instance = PythonModuleInstance(_module)

    # Link all imports:
    for name, f in imports.items():
        # TODO: make a choice between those two options:
        # gen_rocket_wasm.externals[name] = f
        setattr(instance._module, name, f)

    # Export all exported functions
    for definition in module:
        if isinstance(definition, Import):
            pass
            # TODO: maybe validate imported functions?
        elif isinstance(definition, Export):
            if definition.kind != 'func':
                raise NotImplementedError(definition.kind)
            exported_name = definition.name
            setattr(
                instance.exports, exported_name,
                getattr(instance._module, exported_name))

    memories = create_memories(module)
    assert not memories, 'TODO: memories'
    # TODO: Load memories.

    return instance


def flatten_imports(imports):
    """ Go from a two level dict to a single level dict """
    flat_imports = {}
    for mod_name, funcs in imports.items():
        for func_name, func in funcs.items():
            flat_imports['{}_{}'.format(mod_name, func_name)] = func
    return flat_imports


class ModuleInstance:
    """ Instantiated module """
    def __init__(self, module):
        self._module = module
        self.exports = Exports()

    def _run_init(self):
        self._module._run_init()


class NativeModuleInstance(ModuleInstance):
    """ Wasm module loaded as natively compiled code """
    pass


class PythonModuleInstance(ModuleInstance):
    """ Wasm module loaded a generated python module """
    pass


class Exports:
    """ Container for exported functions """
    pass


# See also:
# https://github.com/kanaka/warpy/blob/master/warpy.py
# TODO: merge with ppci.utils.bitfun
def rotl(v, count, bits):
    mask = (1 << bits) - 1
    count = count % bits
    return (((v << count) & mask) | (v >> (bits - count)))


def rotr(v, count, bits):
    mask = (1 << bits) - 1
    count = count % bits
    return ((v >> count) | ((v << (bits - count)) & mask))


def create_runtime():
    """ Create runtime functions.

    These are functions required by some wasm instructions which cannot
    be code generated directly or are too complex.
    """
    import math

    def sqrt(v: float) -> float:
        return math.sqrt(v)

    def i32_rotr(v: int, cnt: int) -> int:
        """ Rotate right """
        return rotr(v, cnt, 32)

    def i64_rotr(v: int, cnt: int) -> int:
        """ Rotate right """
        return rotr(v, cnt, 64)

    def i32_rotl(v: int, cnt: int) -> int:
        """ Rotate left """
        return rotl(v, cnt, 32)

    def i64_rotl(v: int, cnt: int) -> int:
        """ Rotate left """
        return rotl(v, cnt, 64)

    def asr(v: int, b: int) -> int:
        """ Arithmatic shift right """
        raise NotImplementedError()
        return v >> b

    def floor(v: int) -> int:
        """ Round to floor """
        raise NotImplementedError()

    def ctz(v: int, bits) -> int:
        """ count trailing zeroes """
        count = 0
        while count < bits and (v % 2) == 0:
            count += 1
            v //= 2
        return count

    def i32_ctz(v: int) -> int:
        return ctz(v, 32)

    def i64_ctz(v: int) -> int:
        return ctz(v, 64)

    def unreachable():
        raise RuntimeError('WASM KERNEL panic!')

    # TODO: merge with opcode table?
    runtime = {
        'f32_sqrt': sqrt,
        'f64_sqrt': sqrt,
        # 'i32_rotl': i32_rotl,
        # 'i64_rotl': i64_rotl,
        #'i32_rotr': i32_rotr,
        #'i64_rotr': i64_rotr,
        #'i32_asr': asr,
        #'i64_asr': asr,
        #'i32_ctz': i32_ctz,
        #'i64_ctz': i64_ctz,
        'unreachable': unreachable,
    }

    return runtime
