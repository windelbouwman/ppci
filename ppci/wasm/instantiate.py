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
from ..utils.codepage import load_obj, MemoryPage
from ..utils.reporting import DummyReportGenerator
from ..irutils import verify_module
from . import wasm_to_ir
from .components import Export, Import
from .wasm2ppci import create_memories
from .util import sanitize_name, PAGE_SIZE
from .runtime import create_runtime

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
    instance = NativeModuleInstance(obj, imports)

    # Export all exported functions
    for definition in module:
        if isinstance(definition, Export):
            if definition.kind == 'func':
                exported_name = sanitize_name(definition.name)
                setattr(
                    instance.exports, exported_name,
                    getattr(instance._module, exported_name))
            elif definition.kind == 'global':
                logger.error('global not exported')
            elif definition.kind == 'memory':
                logger.error('memory not exported')
            else:
                raise NotImplementedError(definition.kind)

    # Fetch init function:
    fname = '_run_init'
    setattr(instance.exports, fname, getattr(instance._module, fname))

    instance.load_memory(module)

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
            elif definition.kind == 'memory':
                logger.error('memory not exported')
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
    """ Web assembly module instance """
    """ Instantiated module """
    def __init__(self):
        self.exports = Exports()

    def _run_init(self):
        self._module._run_init()


class NativeModuleInstance(ModuleInstance):
    """ Wasm module loaded as natively compiled code """
    def __init__(self, obj, imports):
        super().__init__()
        imports['wasm_rt_memory_grow'] = self.memory_grow
        imports['wasm_rt_memory_size'] = self.memory_size
        self._module = load_obj(obj, imports=imports)

    def memory_grow(self, amount: int) -> int:
        """ Grow memory and return the old size.

        Current strategy:
        - claim new memory
        - copy all data
        - free old memory
        - update wasm memory base pointer
        """
        old_size = self.memory_size()
        new_size = (old_size + amount) * PAGE_SIZE

        # Read old data:
        self._data_page.seek(0)
        old_data = self._data_page.read()

        # Create new page and fill with old data:
        self._data_page = MemoryPage(new_size)
        self._data_page.write(old_data)

        # Update pointer:
        self.set_mem_base_ptr(self._data_page.addr)
        return old_size

    def memory_size(self) -> int:
        """ return memory size in pages """
        return self._data_page.size // PAGE_SIZE

    def load_memory(self, module):
        memories = create_memories(module)
        if memories:
            assert len(memories) == 1
            memory = list(memories.values())[0]
            self._data_page = MemoryPage(len(memory))
            self._data_page.write(memory)
            base_addr = self._data_page.addr
            self.set_mem_base_ptr(base_addr)

    def set_mem_base_ptr(self, base_addr):
        """ Set memory base address """
        # TODO:
        baseptr = self._module.get_symbol_address('wasm_mem0_address')
        print(baseptr)
        # TODO: major hack:
        # TODO: too many assumptions made here ...
        self._module._data_page.seek(0)
        self._module._data_page.write(struct.pack('Q', base_addr))


class PythonModuleInstance(ModuleInstance):
    """ Wasm module loaded a generated python module """
    def __init__(self, module):
        super().__init__()
        self._module = module
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
