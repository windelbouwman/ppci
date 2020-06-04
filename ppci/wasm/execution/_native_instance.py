""" Instantiate wasm as native code.

"""

import logging
import os
import shelve
import struct

from ...utils.codepage import load_obj, MemoryPage
from ...irutils import verify_module
from .. import wasm_to_ir
from ..components import Table
from ..util import PAGE_SIZE
from ._base_instance import ModuleInstance, WasmMemory, WasmGlobal


logger = logging.getLogger("instantiate")


def native_instantiate(module, imports, reporter, cache_file):
    """ Load wasm module native """
    from ...api import ir_to_object, get_current_arch

    logger.info("Instantiating wasm module as native code")
    arch = get_current_arch()
    # key = (arch, module)
    # TODO: think of clever caching trickery:
    cache_file = None
    if cache_file and os.path.exists(cache_file):
        logger.info("Using cached object from %s", cache_file)
        with shelve.open(cache_file) as s:
            obj = s["obj"]
            ppci_module = s["ppci_module"]
    else:
        # TODO: use cache here to short circuit re-compilation
        # hash(key)
        # print(hash(key))
        # hgkfdg
        ppci_module = wasm_to_ir(
            module, arch.info.get_type_info("ptr"), reporter=reporter
        )
        verify_module(ppci_module)
        obj = ir_to_object([ppci_module], arch, debug=True, reporter=reporter)
        if cache_file:
            logger.info("Saving object to %s for later use", cache_file)
            with shelve.open(cache_file) as s:
                s["obj"] = obj
                s["ppci_module"] = ppci_module
    instance = NativeModuleInstance(obj, imports)
    instance._wasm_function_names = ppci_module._wasm_function_names
    instance._wasm_global_names = ppci_module._wasm_global_names
    return instance


class NativeModuleInstance(ModuleInstance):
    """ Wasm module loaded as natively compiled code """

    def __init__(self, obj, imports2):
        super().__init__()
        imports = {}

        imports["wasm_rt_memory_grow"] = self.memory_grow
        imports["wasm_rt_memory_size"] = self.memory_size

        for name, imp_obj in imports2.items():
            assert name not in imports
            if isinstance(imp_obj, Table):

                # print(name, obj)
                ptr_size = 8  # TODO: determine this?
                table_byte_size = imp_obj.max * ptr_size

                # Allocate native memory page for table.
                self._table_obj = MemoryPage(table_byte_size)

                # Enter table memory page in extra symbols:
                magic_key = "func_table"
                assert magic_key not in imports
                imports[magic_key] = self._table_obj
                imports[name] = self._table_obj
            else:
                imports[name] = imp_obj

        self._code_module = load_obj(obj, imports=imports)

    def _run_init(self):
        self._code_module._run_init()

    def memory_size(self) -> int:
        """ return memory size in pages """
        return self._memory_data_page.size // PAGE_SIZE

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
        self._memory_data_page.seek(0)
        old_data = self._memory_data_page.read()

        # Create new page and fill with old data:
        self._memory_data_page = MemoryPage(new_size * PAGE_SIZE)
        self._memory_data_page.write(old_data)

        # Update pointer:
        self.set_mem_base_ptr(self._memory_data_page.addr)
        return old_size

    def memory_create(self, min_size, max_size):
        assert len(self._memories) == 0
        self._memory_data_page = MemoryPage(min_size * PAGE_SIZE)
        mem0 = NativeWasmMemory(self, min_size, max_size)
        self._memories.append(mem0)
        self.set_mem_base_ptr(self._memory_data_page.addr)

    def set_mem_base_ptr(self, base_addr):
        """ Set memory base address """
        baseptr = self._code_module.get_symbol_offset("wasm_mem0_address")
        # print(baseptr)
        # TODO: major hack:
        # TODO: too many assumptions made here ...
        self._code_module._data_page.seek(baseptr)
        self._code_module._data_page.write(struct.pack("Q", base_addr))

    def get_func_by_index(self, index: int):
        exported_name = self._wasm_function_names[index]
        return getattr(self._code_module, exported_name)

    def get_global_by_index(self, index: int):
        global_name = self._wasm_global_names[index]
        return NativeWasmGlobal(global_name, self._code_module)


class NativeWasmMemory(WasmMemory):
    """ Native wasm memory emulation """
    def __init__(self, instance, min_size, max_size):
        super().__init__(min_size, max_size)
        self._instance = instance

    def memory_size(self) -> int:
        """ return memory size in pages """
        return self._memory_data_page.size // PAGE_SIZE

    def write(self, address: int, data):
        """ Write some data to memory """
        self._instance._memory_data_page.seek(address)
        self._instance._memory_data_page.write(data)

    def read(self, address: int, size: int) -> bytes:
        self._instance._memory_data_page.seek(address)
        data = self._instance._memory_data_page.read(size)
        assert len(data) == size
        return data


class NativeWasmGlobal(WasmGlobal):
    def __init__(self, name, code_obj):
        super().__init__(name)
        self._code_obj = code_obj

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
