""" Provide function to load a wasm module into the current process.

Note that for this to work, we require compiled wasm code and a runtime.

The wasm runtime contains the following:

- Implement function like sqrt, floor, bit rotations etc..
"""

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
