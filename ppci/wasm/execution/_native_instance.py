"""Instantiate wasm as native code."""

import logging
import os
import shelve

from ...utils.codepage import load_obj, MemoryPage
from ...irutils import verify_module
from .. import wasm_to_ir
from ..components import Table
from ..util import PAGE_SIZE
from ._base_instance import ModuleInstance
from ._base_instance import MemoryInstance, GlobalInstance
from ._base_instance import TableInstance, ElemInstance


logger = logging.getLogger("instantiate")


def native_instantiate(module, imports, reporter, cache_file):
    """Load wasm module native"""
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

        # This is fun: optimizing might slow down actual performance X-(
        # from ...api import optimize
        # optimize(ppci_module, level=2, reporter=reporter)

        obj = ir_to_object([ppci_module], arch, debug=True, reporter=reporter)
        if cache_file:
            logger.info("Saving object to %s for later use", cache_file)
            with shelve.open(cache_file) as s:
                s["obj"] = obj
                s["ppci_module"] = ppci_module
    instance = NativeModuleInstance(obj, imports)
    instance._wasm_info = ppci_module._wasm_info
    return instance


class NativeModuleInstance(ModuleInstance):
    """Wasm module loaded as natively compiled code"""

    def __init__(self, obj, imports2):
        super().__init__()
        imports = {}

        imports["wasm_rt_table_grow"] = self.table_grow
        imports["wasm_rt_table_size"] = self.table_size
        imports["wasm_rt_table_init"] = self.table_init
        imports["wasm_rt_table_copy"] = self.table_copy
        imports["wasm_rt_table_fill"] = self.table_fill

        imports["wasm_rt_memory_grow"] = self.memory_grow
        imports["wasm_rt_memory_size"] = self.memory_size
        imports["wasm_rt_memory_init"] = self.memory_init
        imports["wasm_rt_memory_copy"] = self.memory_copy
        imports["wasm_rt_memory_fill"] = self.memory_fill

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

    def invoke(self, name, *args):
        f = getattr(self._code_module, name)
        f(*args)

    def memory_create(self, min_size, max_size):
        assert len(self._memories) == 0
        mem0 = NativeMemoryInstance(self, min_size, max_size)
        self._memories.append(mem0)

    def create_table(self, size, max_size):
        return NativeTableInstance(size, max_size)

    def set_table_ptr(self, index, table):
        name = self._wasm_info.table_names[index]
        table_ptr = self._code_module.get_symbol_offset(name)
        table_addr = table._meta_page.addr
        self._code_module._data_page.write_fmt(table_ptr, "Q", table_addr)

    def create_elem(self, index: int, size: int) -> "NativeElemInstance":
        name = self._wasm_info.elem_names[index]
        offset = self._code_module.get_symbol_offset(name)
        return NativeElemInstance(offset, self._code_module._data_page, size)

    def set_mem_base_ptr(self, base_addr):
        """Set memory base address"""
        baseptr = self._code_module.get_symbol_offset("wasm_mem0_address")
        # print(baseptr)
        # TODO: major hack:
        # TODO: too many assumptions made here ...
        self._code_module._data_page.write_fmt(baseptr, "Q", base_addr)

    def get_func_by_index(self, index: int):
        exported_name = self._wasm_info.function_names[index]
        return getattr(self._code_module, exported_name)

    def get_global_by_index(self, index: int):
        ty, name = self._wasm_info.global_names[index]
        return NativeGlobalInstance(ty, name, self._code_module)


class NativeMemoryInstance(MemoryInstance):
    """Native wasm memory emulation"""

    def __init__(self, instance, min_size, max_size):
        super().__init__(min_size, max_size)
        self._instance = instance
        self._memory_data_page = MemoryPage(min_size * PAGE_SIZE)
        self._instance.set_mem_base_ptr(self._memory_data_page.addr)

    def grow(self, amount: int) -> int:
        """Grow memory and return the old size.

        Current strategy:
        - claim new memory
        - copy all data
        - free old memory
        - update wasm memory base pointer
        """
        max_size = self.max_size
        old_size = self.size()
        new_size = old_size + amount

        # Keep memory within sensible bounds:
        if new_size >= 0x10000:
            return -1

        if max_size is not None and new_size > max_size:
            return -1

        # Read old data:
        self._memory_data_page.seek(0)
        old_data = self._memory_data_page.read(old_size * PAGE_SIZE)

        # Create new page and fill with old data:
        self._memory_data_page = MemoryPage(new_size * PAGE_SIZE)
        self._memory_data_page.seek(0)
        self._memory_data_page.write(old_data)

        # Update pointer:
        self._instance.set_mem_base_ptr(self._memory_data_page.addr)
        return old_size

    def size(self) -> int:
        """return memory size in pages"""
        return self._memory_data_page.size // PAGE_SIZE

    def write(self, address: int, data: bytes):
        """Write some data to memory"""
        self._memory_data_page.seek(address)
        self._memory_data_page.write(data)

    def read(self, address: int, size: int) -> bytes:
        self._memory_data_page.seek(address)
        data = self._memory_data_page.read(size)
        assert len(data) == size
        return data


class NativeGlobalInstance(GlobalInstance):
    def __init__(self, ty, name, code_obj):
        super().__init__(ty, name)
        self._code_obj = code_obj

    def _get_ptr(self):
        vpointer = getattr(self._code_obj, self.name)
        return vpointer

    def read(self):
        addr = self._get_ptr()
        value = addr.contents.value
        return value

    def write(self, value):
        addr = self._get_ptr()
        addr.contents.value = value


class NativeTableInstance(TableInstance):
    def __init__(self, size: int, max_size):
        super().__init__(max_size)
        ptr_size = 8
        meta_size = ptr_size + 4 + 4
        n_bytes = size * ptr_size
        self._meta_page = MemoryPage(meta_size)
        self._data_page = MemoryPage(n_bytes)
        self._meta_page.write_fmt(0, "QI", self._data_page.addr, size)

    def size(self) -> int:
        return self._meta_page.read_fmt(8, "I")[0]

    def grow(self, val, count: int) -> int:
        ptr_size = 8
        old_size = self._meta_page.read_fmt(8, "I")[0]
        new_size = old_size + count
        if self._max_size is not None:
            if new_size > self._max_size:
                return -1
        new_page = MemoryPage(new_size * ptr_size)
        for i in range(new_size):
            offset = i * ptr_size
            if i < old_size:
                p = self._data_page.read_fmt(offset, "Q")[0]
            else:
                p = val
            new_page.write_fmt(offset, "Q", p)
        self._data_page = new_page
        self._meta_page.write_fmt(0, "QI", new_page.addr, new_size)
        return old_size

    def set_item(self, index: int, value):
        self._data_page.write_fmt(index * 8, "Q", value)

    def get_item(self, index: int):
        values = self._data_page.read_fmt(index * 8, "Q")
        return values[0]


class NativeElemInstance(ElemInstance):
    def __init__(self, offset, page, size):
        super().__init__(size)
        self._offset = offset
        self._page = page

    def get_item(self, index: int):
        offset = self._offset + index * 8
        return self._page.read_fmt(offset, "Q")[0]
