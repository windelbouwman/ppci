""" Provide function to load a wasm module into the current process.

Note that for this to work, we require compiled wasm code and a runtime.

The wasm runtime contains the following:

- Implement function like sqrt, floor, bit rotations etc..
"""

import io
import struct
import logging
from types import ModuleType

from ..api import ir_to_object, get_current_arch, ir_to_python
from ..arch.arch_info import TypeInfo
from ..utils.codepage import load_obj
from ..utils.bitfun import rotr, rotl, to_signed, to_unsigned
from ..utils.bitfun import clz, ctz, popcnt
from ..utils.reporting import DummyReportGenerator
from ..irutils import verify_module
from . import wasm_to_ir
from .components import Export, Import
from .wasm2ppci import create_memories
from .util import sanitize_name, PAGE_SIZE, make_int

__all__ = ('instantiate',)


logger = logging.getLogger('instantiate')


def instantiate(module, imports, target='native', reporter=None):
    """ Instantiate a wasm module.

    Args:
        module (ppci.wasm.Module): The wasm-module to instantiate
        imports: A collection of functions available to the wasm module.
        target: Use 'native' to compile wasm to machine code.
                Use 'python' to generate python code. This option is slower
                but more reliable.

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
        raise ValueError('Unknown instantiation target {}'.format(target))

    # Call magic function _run_init which initializes tables and optionally
    # calls start function as defined by the wasm start section.
    instance._run_init()
    return instance


def native_instantiate(module, imports, reporter):
    """ Load wasm module native """
    logger.info('Instantiating wasm module as native code')
    arch = get_current_arch()
    ppci_module = wasm_to_ir(
        module, arch.info.get_type_info('ptr'), reporter=reporter)
    verify_module(ppci_module)
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

    # Fetch init function:
    fname = '_run_init'
    setattr(instance.exports, fname, getattr(instance._module, fname))

    memories = create_memories(module)
    # TODO: Load memories.

    return instance


def python_instantiate(module, imports, reporter):
    """ Load wasm module as a PythonModuleInstance """
    logger.info('Instantiating wasm module as python')
    ptr_info = TypeInfo(4, 4)
    ppci_module = wasm_to_ir(module, ptr_info, reporter=reporter)
    verify_module(ppci_module)
    f = io.StringIO()
    ir_to_python([ppci_module], f, reporter=reporter)
    pysrc = f.getvalue()
    pycode = compile(pysrc, '<string>', 'exec')
    _module = ModuleType('gen')
    exec(pycode, _module.__dict__)
    instance = PythonModuleInstance(_module)

    # Magical python memory interface, add it now:
    imports['wasm_rt_memory_grow'] = instance.memory_grow
    imports['wasm_rt_memory_size'] = instance.memory_size

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
            if definition.kind == 'func':
                exported_name = sanitize_name(definition.name)
                setattr(
                    instance.exports, exported_name,
                    getattr(instance._module, exported_name))
            elif definition.kind == 'global':
                logger.error('global not exported')
            else:
                raise NotImplementedError(definition.kind)

    memories = create_memories(module)
    if memories:
        assert len(memories) == 1
        memory = list(memories.values())[0]

        instance.mem0_start = instance._module.heap_top()
        instance._module.heap.extend(memory)
        mem0_ptr_ptr = instance._module.wasm_mem0_address
        instance._module.store_i32(instance.mem0_start, mem0_ptr_ptr)

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
    def memory_grow(self, amount):
        """ Grow memory and return the old size """
        raise NotImplementedError()

    def memory_size(self):
        """ return memory size in pages """
        raise NotImplementedError()


class PythonModuleInstance(ModuleInstance):
    """ Wasm module loaded a generated python module """
    def __init__(self, module):
        super().__init__(module)
        self.mem_end = self._module.heap_top()

    def memory_grow(self, amount):
        """ Grow memory and return the old size """
        # Limit the bounds of memory somewhat:
        if amount > 2**12:
            return -1
        else:
            old_size = self.memory_size()
            self._module.heap.extend(bytes(amount * PAGE_SIZE))
            return old_size

    def memory_size(self):
        """ return memory size in pages """
        size = (self._module.heap_top() - self.mem0_start) // PAGE_SIZE
        return size


class Exports:
    """ Container for exported functions """
    pass

##
class Unreachable(RuntimeError):
    """ WASM kernel panic. Having an exception for this allows catching it
    in tests.
    """
    pass


# See also:
# https://github.com/kanaka/warpy/blob/master/warpy.py
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
        return to_signed(rotr(to_unsigned(v, 32), cnt, 32), 32)

    def i64_rotr(v: int, cnt: int) -> int:
        """ Rotate right """
        return rotr(v, cnt, 64)

    def i32_rotl(v: int, cnt: int) -> int:
        """ Rotate left """
        return to_signed(rotl(to_unsigned(v, 32), cnt, 32), 32)

    def i64_rotl(v: int, cnt: int) -> int:
        """ Rotate left """
        return rotl(v, cnt, 64)

    def floor(v: int) -> int:
        """ Round to floor """
        raise NotImplementedError()

    # Bit counting:
    def i32_clz(v: int) -> int:
        return clz(v, 32)

    def i64_clz(v: int) -> int:
        return clz(v, 64)

    def i32_ctz(v: int) -> int:
        return ctz(v, 32)

    def i64_ctz(v: int) -> int:
        return ctz(v, 64)

    def i32_popcnt(v: int) -> int:
        return popcnt(v, 32)

    def i64_popcnt(v: int) -> int:
        return popcnt(v, 64)

    # Conversions:
    def i32_trunc_s_f32(v: float) -> int:
        return int(v)

    def i32_trunc_u_f32(v: float) -> int:
        return make_int(v, 32)

    def i32_trunc_s_f64(v: float) -> int:
        return int(v)

    def i32_trunc_u_f64(v: float) -> int:
        return make_int(v, 32)

    def i64_trunc_s_f32(v: float) -> int:
        return int(v)

    def i64_trunc_u_f32(v: float) -> int:
        return make_int(v, 64)

    def i64_trunc_s_f64(v: float) -> int:
        return int(v)

    def i64_trunc_u_f64(v: float) -> int:
        return make_int(v, 64)

    def f64_promote_f32(v: float) -> float:
        return v

    def f32_demote_f64(v: float) -> float:
        return v

    def f64_reinterpret_i64(v: int) -> float:
        x = struct.pack('<q', v)
        return struct.unpack('<d', x)[0]

    def i64_reinterpret_f64(v: float) -> int:
        x = struct.pack('<d', v)
        return struct.unpack('<q', x)[0]

    def f32_reinterpret_i32(v: int) -> float:
        x = struct.pack('<i', v)
        return struct.unpack('<f', x)[0]

    def i32_reinterpret_f32(v: float) -> int:
        x = struct.pack('<f', v)
        return struct.unpack('<i', x)[0]

    def f32_copysign(x: float, y: float) -> float:
        return math.copysign(x, y)

    def f64_copysign(x: float, y: float) -> float:
        return math.copysign(x, y)

    def f32_min(x: float, y: float) -> float:
        return min(x, y)

    def f64_min(x: float, y: float) -> float:
        return min(x, y)

    def f32_max(x: float, y: float) -> float:
        return max(x, y)

    def f64_max(x: float, y: float) -> float:
        return max(x, y)

    def f32_abs(x: float) -> float:
        return math.fabs(x)

    def f64_abs(x: float) -> float:
        return math.fabs(x)

    def f32_floor(x: float) -> float:
        return float(math.floor(x))

    def f64_floor(x: float) -> float:
        return float(math.floor(x))

    def f32_ceil(x: float) -> float:
        return float(math.ceil(x))

    def f64_ceil(x: float) -> float:
        return float(math.ceil(x))

    def f32_nearest(x: float) -> float:
        return float(round(x))

    def f64_nearest(x: float) -> float:
        return float(round(x))

    def f32_trunc(x: float) -> float:
        return float(math.trunc(x))

    def f64_trunc(x: float) -> float:
        return float(math.trunc(x))

    def unreachable() -> None:
        raise Unreachable('WASM KERNEL panic!')

    # TODO: merge with opcode table?
    runtime = {
        'f32_sqrt': sqrt,
        'f64_sqrt': sqrt,
        'i32_rotl': i32_rotl,
        'i64_rotl': i64_rotl,
        'i32_rotr': i32_rotr,
        'i64_rotr': i64_rotr,
        'i32_clz': i32_clz,
        'i64_clz': i64_clz,
        'i32_ctz': i32_ctz,
        'i64_ctz': i64_ctz,
        'i32_popcnt': i32_popcnt,
        'i64_popcnt': i64_popcnt,
        'i32_trunc_s_f32': i32_trunc_s_f32,
        'i32_trunc_u_f32': i32_trunc_u_f32,
        'i32_trunc_s_f64': i32_trunc_s_f64,
        'i32_trunc_u_f64': i32_trunc_u_f64,
        'i64_trunc_s_f32': i64_trunc_s_f32,
        'i64_trunc_u_f32': i64_trunc_u_f32,
        'i64_trunc_s_f64': i64_trunc_s_f64,
        'i64_trunc_u_f64': i64_trunc_u_f64,
        'f64_promote_f32': f64_promote_f32,
        'f32_demote_f64': f32_demote_f64,
        'f64_reinterpret_i64': f64_reinterpret_i64,
        'i64_reinterpret_f64': i64_reinterpret_f64,
        'f32_reinterpret_i32': f32_reinterpret_i32,
        'i32_reinterpret_f32': i32_reinterpret_f32,
        'f32_copysign': f32_copysign,
        'f64_copysign': f64_copysign,
        'f32_min': f32_min,
        'f32_max': f32_max,
        'f64_min': f64_min,
        'f64_max': f64_max,
        'f32_abs': f32_abs,
        'f64_abs': f64_abs,
        'f32_floor': f32_floor,
        'f64_floor': f64_floor,
        'f32_nearest': f32_nearest,
        'f64_nearest': f64_nearest,
        'f32_ceil': f32_ceil,
        'f64_ceil': f64_ceil,
        'f32_trunc': f32_trunc,
        'f64_trunc': f64_trunc,
        'unreachable': unreachable,
        # todo: 'memory_size': memory_size,
        # todo: 'memory_grow': memory_grow,
    }

    return runtime
