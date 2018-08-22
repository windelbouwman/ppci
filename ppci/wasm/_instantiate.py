""" Provide function to load a wasm module into the current process.

Note that for this to work, we require compiled wasm code and a runtime.

The wasm runtime contains the following:

- Implement function like sqrt, floor, bit rotations etc..
"""

import os
import abc
import shelve
import io
import struct
import logging
import ctypes
from types import ModuleType

from ..arch.arch_info import TypeInfo
from ..utils.codepage import load_obj, MemoryPage
from ..utils.reporting import DummyReportGenerator
from ..irutils import verify_module
from ..binutils.objectfile import ObjectFile
from . import wasm_to_ir
from .components import Export, Import
from .wasm2ppci import create_memories
from .util import sanitize_name, PAGE_SIZE
from .runtime import create_runtime

__all__ = ('instantiate',)


logger = logging.getLogger('instantiate')


def instantiate(module, imports, target='native', reporter=None, cache_file=None):
    """ Instantiate a wasm module.

    Args:
        module (ppci.wasm.Module): The wasm-module to instantiate
        imports: A collection of functions available to the wasm module.
        target: Use 'native' to compile wasm to machine code.
                Use 'python' to generate python code. This option is slower
                but more reliable.
        reporter: A reporter which can record detailed compilation information.
        cache_file: a file to use as cache

    """
    if reporter is None:
        reporter = DummyReportGenerator()

    reporter.heading(2, 'Wasm instantiation')

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

    # Inject wasm runtime functions:
    if 'wasm_rt' in imports:
        raise ValueError('wasm_rt is a special import section')
    imports = imports.copy() # otherwise we'd render the imports unsuable
    imports['wasm_rt'] = create_runtime()

    imports = flatten_imports(imports)

    if target == 'native':
        instance = native_instantiate(module, imports, reporter, cache_file)
    elif target == 'python':
        instance = python_instantiate(module, imports, reporter, cache_file)
    else:
        raise ValueError('Unknown instantiation target {}'.format(target))

    # Call magic function _run_init which initializes tables and optionally
    # calls start function as defined by the wasm start section.
    instance._run_init()
    return instance


def native_instantiate(module, imports, reporter, cache_file):
    """ Load wasm module native """
    from ..api import ir_to_object, get_current_arch
    logger.info('Instantiating wasm module as native code')
    arch = get_current_arch()
    key = (arch, module)
    # TODO: think of clever caching trickery:
    cache_file = None
    if cache_file and os.path.exists(cache_file):
        logger.info('Using cached object from %s', cache_file)
        with shelve.open(cache_file) as s:
            obj = s['obj']
            ppci_module = s['ppci_module']
    else:
        # TODO: use cache here to short circuit re-compilation
        # hash(key)
        # print(hash(key))
        # hgkfdg
        ppci_module = wasm_to_ir(
            module, arch.info.get_type_info('ptr'), reporter=reporter)
        verify_module(ppci_module)
        obj = ir_to_object([ppci_module], arch, debug=True, reporter=reporter)
        if cache_file:
            logger.info('Saving object to %s for later use', cache_file)
            with shelve.open(cache_file) as s:
                s['obj'] = obj
                s['ppci_module'] = ppci_module
    instance = NativeModuleInstance(obj, imports)

    instance.load_memory(module)

    # Export all exported functions
    for definition in module:
        if isinstance(definition, Export):
            if definition.kind == 'func':
                exported_name = ppci_module._wasm_function_names[definition.ref.index]
                instance.exports._function_map[definition.name] = \
                    getattr(instance._code_module, exported_name)
            elif definition.kind == 'global':
                global_name = ppci_module._wasm_globals[definition.ref.index]
                instance.exports._function_map[definition.name] = \
                    NativeWasmGlobal(global_name, instance._code_module)
                logger.debug('global exported')
            elif definition.kind == 'memory':
                memory = instance._memories[definition.ref.index]
                instance.exports._function_map[definition.name] = memory
                logger.debug('memory exported')
            else:
                raise NotImplementedError(definition.kind)

    return instance


def python_instantiate(module, imports, reporter, cache_file):
    """ Load wasm module as a PythonModuleInstance """
    from ..api import ir_to_python
    logger.info('Instantiating wasm module as python')
    ptr_info = TypeInfo(4, 4)
    ppci_module = wasm_to_ir(module, ptr_info, reporter=reporter)
    verify_module(ppci_module)
    f = io.StringIO()
    ir_to_python([ppci_module], f, reporter=reporter)
    pysrc = f.getvalue()
    pycode = compile(pysrc, '<string>', 'exec')
    _py_module = ModuleType('gen')
    exec(pycode, _py_module.__dict__)
    instance = PythonModuleInstance(_py_module, imports)

    # Initialize memory:
    instance.load_memory(module)

    # Export all exported functions
    for definition in module:
        if isinstance(definition, Import):
            pass
            # TODO: maybe validate imported functions?
        elif isinstance(definition, Export):
            if definition.kind == 'func':
                exported_name = ppci_module._wasm_function_names[definition.ref.index]
                instance.exports._function_map[definition.name] = \
                    getattr(instance._py_module, exported_name)
            elif definition.kind == 'global':
                global_name = ppci_module._wasm_globals[definition.ref.index]
                instance.exports._function_map[definition.name] = \
                    PythonWasmGlobal(global_name, instance)
                logger.debug('global exported')
            elif definition.kind == 'memory':
                memory = instance._memories[definition.ref.index]
                instance.exports._function_map[definition.name] = memory
                logger.debug('memory exported')
            else:
                raise NotImplementedError(definition.kind)

    return instance


def flatten_imports(imports):
    """ Go from a two level dict to a single level dict """
    flat_imports = {}
    for mod_name, funcs in imports.items():
        for func_name, func in funcs.items():
            flat_imports['{}_{}'.format(mod_name, func_name)] = func
    return flat_imports


class ModuleInstance:
    """ Web assembly module instance """
    """ Instantiated module """
    def __init__(self):
        self.exports = Exports()
        self._memories = []

    def memory_size(self) -> int:
        """ return memory size in pages """
        # TODO: idea is to have multiple memories and query the memory:
        memory_index = 0
        memory = self._memories[memory_index]
        return memory.memory_size()


class NativeModuleInstance(ModuleInstance):
    """ Wasm module loaded as natively compiled code """
    def __init__(self, obj, imports):
        super().__init__()
        imports['wasm_rt_memory_grow'] = self.memory_grow
        imports['wasm_rt_memory_size'] = self.memory_size
        self._code_module = load_obj(obj, imports=imports)

    def _run_init(self):
        self._code_module._run_init()

    def memory_size(self) -> int:
        """ return memory size in pages """
        return self._data_page.size // PAGE_SIZE

    def memory_grow(self, amount: int) -> int:
        """ Grow memory and return the old size.

        Current strategy:
        - claim new memory
        - copy all data
        - free old memory
        - update wasm memory base pointer
        """
        max_size = self._memories[0].max_size
        old_size = self.memory_size()
        new_size = old_size + amount

        # Keep memory within sensible bounds:
        if new_size >= 0x10000:
            return -1

        if max_size is not None and new_size > max_size:
            return -1

        # Read old data:
        self._data_page.seek(0)
        old_data = self._data_page.read()

        # Create new page and fill with old data:
        self._data_page = MemoryPage(new_size * PAGE_SIZE)
        self._data_page.write(old_data)

        # Update pointer:
        self.set_mem_base_ptr(self._data_page.addr)
        return old_size

    def load_memory(self, module):
        memories = create_memories(module)
        if memories:
            assert len(memories) == 1
            memory, min_size, max_size = memories[0]
            self._data_page = MemoryPage(len(memory))
            self._data_page.write(memory)
            mem0 = NativeWasmMemory(min_size, max_size)
            # mem0._data_page = self._data_page
            mem0._instance = self
            self._memories.append(mem0)
            base_addr = self._data_page.addr
            self.set_mem_base_ptr(base_addr)

    def set_mem_base_ptr(self, base_addr):
        """ Set memory base address """
        baseptr = self._code_module.get_symbol_offset('wasm_mem0_address')
        print(baseptr)
        # TODO: major hack:
        # TODO: too many assumptions made here ...
        self._code_module._data_page.seek(baseptr)
        self._code_module._data_page.write(struct.pack('Q', base_addr))


class WasmGlobal(metaclass=abc.ABCMeta):
    def __init__(self, name):
        self.name = name

    @abc.abstractmethod
    def read(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def write(self, value):
        raise NotImplementedError()


# TODO: we might implement the descriptor protocol in some way?
class PythonWasmGlobal(WasmGlobal):
    def __init__(self, name, memory):
        super().__init__(name)
        self.instance = memory

    def _get_ptr(self):
        addr = getattr(self.instance._py_module, self.name[1].name)
        return addr

    def read(self):
        addr = self._get_ptr()
        # print('Reading', self.name, addr)
        mp = {
            ir.i32: self.instance._py_module.load_i32,
            ir.i64: self.instance._py_module.load_i64,
        }
        f = mp[self.name[0]]
        return f(addr)

    def write(self, value):
        addr = self._get_ptr()
        # print('Writing', self.name, addr)
        mp = {
            ir.i32: self.instance._py_module.write_i32,
            ir.i64: self.instance._py_module.write_i64,
        }
        f = mp[self.name[0]]
        f(addr, value)


class NativeWasmGlobal(WasmGlobal):
    def __init__(self, name, memory):
        super().__init__(name)
        self._code_obj = memory

    def _get_ptr(self):
        # print('Getting address of', self.name)
        vpointer = getattr(self._code_obj, self.name[1].name)
        return vpointer

    def read(self):
        addr = self._get_ptr()
        # print('Reading', self.name, addr)
        value = addr.contents.value
        return value

    def write(self, value):
        addr = self._get_ptr()
        # print('Writing', self.name, addr, value)
        addr.contents.value = value


class WasmMemory(metaclass=abc.ABCMeta):
    def __init__(self, min_size, max_size):
        self.min_size = min_size
        self.max_size = max_size

    def __setitem__(self, location, data):
        assert isinstance(location, slice)
        assert location.step is None
        if location.start is None:
            address = location.stop
            size = 1
        else:
            address = location.start
            size = location.stop - location.start
        assert len(data) == size
        self.write(address, data)

    def __getitem__(self, location):
        assert isinstance(location, slice)
        assert location.step is None
        if location.start is None:
            address = location.stop
            size = 1
        else:
            address = location.start
            size = location.stop - location.start
        data = self.read(address, size)
        assert len(data) == size
        return data

    @abc.abstractmethod
    def write(self, address, data):
        raise NotImplementedError()

    @abc.abstractmethod
    def read(self, address, size):
        raise NotImplementedError()


class NativeWasmMemory(WasmMemory):
    """ Native wasm memory emulation """
    def memory_size(self) -> int:
        """ return memory size in pages """
        return self._data_page.size // PAGE_SIZE

    def write(self, address, data):
        self._instance._data_page.seek(address)
        self._instance._data_page.write(data)

    def read(self, address, size):
        self._instance._data_page.seek(address)
        data = self._instance._data_page.read(size)
        assert len(data) == size
        return data


class PythonWasmMemory(WasmMemory):
    """ Python wasm memory emulation """
    def write(self, address, data):
        address = self._module.mem0_start + address
        self._module._py_module.write_mem(address, data)

    def read(self, address, size):
        address = self._module.mem0_start + address
        data = self._module._py_module.read_mem(address, size)
        assert len(data) == size
        return data


class PythonModuleInstance(ModuleInstance):
    """ Wasm module loaded a generated python module """
    def __init__(self, module, imports):
        super().__init__()
        self._py_module = module
        self.mem_end = self._py_module.heap_top()

        # Magical python memory interface, add it now:
        imports['wasm_rt_memory_grow'] = self.memory_grow
        imports['wasm_rt_memory_size'] = self.memory_size

        # Link all imports:
        for name, f in imports.items():
            # TODO: make a choice between those two options:
            # gen_rocket_wasm.externals[name] = f
            setattr(self._py_module, name, f)

    def _run_init(self):
        self._py_module._run_init()

    def load_memory(self, module):
        memories = create_memories(module)
        if memories:
            assert len(memories) == 1
            memory, min_size, max_size = memories[0]

            self.mem0_start = self._py_module.heap_top()
            self._py_module.heap.extend(memory)
            mem0_ptr_ptr = self._py_module.wasm_mem0_address
            self._py_module.store_i32(self.mem0_start, mem0_ptr_ptr)
            mem0 = PythonWasmMemory(min_size, max_size)
            # TODO: HACK HACK HACK:
            mem0._module = self
            self._memories.append(mem0)

    def memory_grow(self, amount):
        """ Grow memory and return the old size """
        # Limit the bounds of memory somewhat:
        if amount >= 0x10000:
            return -1
        else:
            max_size = self._memories[0].max_size
            old_size = self.memory_size()
            new_size = old_size + amount
            if max_size is not None and new_size > max_size:
                return -1
            else:
                self._py_module.heap.extend(bytes(amount * PAGE_SIZE))
                return old_size

    def memory_size(self):
        """ return memory size in pages """
        size = (self._py_module.heap_top() - self.mem0_start) // PAGE_SIZE
        return size


class Exports:
    def __init__(self):
        self._function_map = {}

    """ Container for exported functions """
    def __getitem__(self, key):
        assert isinstance(key, str)
        return self._function_map[key]

    def __getattr__(self, name):
        if name in self._function_map:
            return self._function_map[name]
        else:
            raise AttributeError('Name "{}" was not exported'.format(name))
