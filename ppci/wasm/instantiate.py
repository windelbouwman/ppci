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
from ..utils.reporting import DummyReportGenerator
from ..irutils import verify_module
from . import wasm_to_ir
from .components import Export, Import
from .wasm2ppci import create_memories
from .util import sanitize_name, PAGE_SIZE

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

    def clz(v: int, bits) -> int:
        """ count leading zeroes """
        return bits - len(bin(v)[2:])  # todo: the bin (i.e. tostring) is probably inefficient

    def ctz(v: int, bits) -> int:
        """ count trailing zeroes """
        count = 0
        while count < bits and (v % 2) == 0:
            count += 1
            v //= 2
        return count
    
    def i32_clz(v: int) -> int:
        return ctz(v, 32)
        
    def i64_clz(v: int) -> int:
        return ctz(v, 64)
    
    def i32_ctz(v: int) -> int:
        return ctz(v, 32)

    def i64_ctz(v: int) -> int:
        return ctz(v, 64)
    
    def i32_shr_s(v: int, s: int) -> int:
        return v >> s
    
    def i32_shr_u(v: int, s: int) -> int:
        return v >> s  # todo: this is probably wrong?
    
    def i32_rem_s(n: int, d: int) -> int:
        return n % d  # n - d*(n//d)
    
    def i32_rem_u(n: int, d: int) -> int:  # todo: different from signed, nan if d is zero?
        return n % d  # n - d*(n//d)

    # i64:
    def i64_rem_s(n: int, d: int) -> int:
        return n % d  # n - d*(n//d)

    def i64_rem_u(n: int, d: int) -> int:
        return n % d  # n - d*(n//d)

    def i64_shr_s(v: int, s: int) -> int:
        return v >> s

    def i64_shr_u(v: int, s: int) -> int:
        return v >> s  # todo: this is probably wrong?

    # Conversions:
    def i32_trunc_s_f32(v: float) -> int:
        return int(v)

    def i32_trunc_u_f32(v: float) -> int:
        return int(v)

    def i32_trunc_s_f64(v: float) -> int:
        return int(v)

    def i32_trunc_u_f64(v: float) -> int:
        return int(v)

    def i64_trunc_s_f32(v: float) -> int:
        return int(v)

    def i64_trunc_u_f32(v: float) -> int:
        return int(v)

    def i64_trunc_s_f64(v: float) -> int:
        return int(v)

    def i64_trunc_u_f64(v: float) -> int:
        return int(v)

    def f64_promote_f32(v: float) -> float:
        return v

    def f64_reinterpret_i64(v: float) -> int:
        x = struct.pack('<d', v)
        return struct.unpack('<q', x)[0]

    def f32_reinterpret_i32(v: float) -> int:
        x = struct.pack('<f', v)
        return struct.unpack('<i', x)[0]
    
    def unreachable() -> None:
        raise Unreachable('WASM KERNEL panic!')

    def memory_size() -> int:
        return 1
    
    def memory_grow(s: int) ->int:
        return 1

    # TODO: merge with opcode table?
    runtime = {
        'f32_sqrt': sqrt,
        'f64_sqrt': sqrt,
        'i32_rotl': i32_rotl,
        'i64_rotl': i64_rotl,
        'i32_rotr': i32_rotr,
        'i64_rotr': i64_rotr,
        'i32_asr': asr,
        'i64_asr': asr,
        'i32_clz': i32_clz,
        'i64_clz': i64_clz,
        'i32_ctz': i32_ctz,
        'i64_ctz': i64_ctz,
        'i32_shr_s': i32_shr_s,
        'i32_rem_u': i32_rem_u,
        'i32_rem_s': i32_rem_s,
        'i64_rem_u': i64_rem_u,
        'i64_rem_s': i64_rem_s,
        'i64_shr_s': i64_shr_s,
        'i64_shr_u': i64_shr_u,
        'i32_trunc_s_f32': i32_trunc_s_f32,
        'i32_trunc_u_f32': i32_trunc_u_f32,
        'i32_trunc_s_f64': i32_trunc_s_f64,
        'i32_trunc_u_f64': i32_trunc_u_f64,
        'i64_trunc_s_f32': i64_trunc_s_f32,
        'i64_trunc_u_f32': i64_trunc_u_f32,
        'i64_trunc_s_f64': i64_trunc_s_f64,
        'i64_trunc_u_f64': i64_trunc_u_f64,
        'f64_promote_f32': f64_promote_f32,
        'f64_reinterpret_i64': f64_reinterpret_i64,
        'f32_reinterpret_i32': f32_reinterpret_i32,
        'unreachable': unreachable,
        # todo: 'memory_size': memory_size,
        # todo: 'memory_grow': memory_grow,
    }

    return runtime
