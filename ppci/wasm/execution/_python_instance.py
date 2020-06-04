""" Instatiate wasm module as python code.
"""

import logging
import io
from types import ModuleType
from ...arch.arch_info import TypeInfo
from ...irutils import verify_module
from ... import ir
from ..components import Table
from .. import wasm_to_ir
from ..util import PAGE_SIZE
from ._base_instance import ModuleInstance, WasmMemory, WasmGlobal

logger = logging.getLogger("instantiate")


def python_instantiate(module, imports, reporter, cache_file):
    """ Load wasm module as a PythonModuleInstance """
    from ...api import ir_to_python

    logger.info("Instantiating wasm module as python")
    ptr_info = TypeInfo(4, 4)
    ppci_module = wasm_to_ir(module, ptr_info, reporter=reporter)
    verify_module(ppci_module)
    f = io.StringIO()
    ir_to_python([ppci_module], f, reporter=reporter)
    pysrc = f.getvalue()
    pycode = compile(pysrc, "<string>", "exec")
    _py_module = ModuleType("gen")
    exec(pycode, _py_module.__dict__)

    instance = PythonModuleInstance(_py_module, imports)
    instance._wasm_function_names = ppci_module._wasm_function_names
    instance._wasm_global_names = ppci_module._wasm_global_names
    return instance


class PythonModuleInstance(ModuleInstance):
    """ Wasm module loaded a generated python module """

    def __init__(self, py_module, imports):
        super().__init__()
        self._py_module = py_module

        # Magical python memory interface, add it now:
        imports["wasm_rt_memory_grow"] = self.memory_grow
        imports["wasm_rt_memory_size"] = self.memory_size

        # Link all imports:
        for name, obj in imports.items():
            if isinstance(obj, Table):
                # print(name, obj)
                ptr_size = 4
                table_byte_size = obj.max * ptr_size
                table_addr = self._py_module._irpy_heap_top()
                self._py_module._irpy_heap.extend(bytes(table_byte_size))
                obj = table_addr
                magic_key = "func_table"
                assert magic_key not in self._py_module._irpy_externals
                self._py_module._irpy_externals[magic_key] = table_addr

            self._py_module._irpy_externals[name] = obj

    def _run_init(self):
        self._py_module._run_init()

    def memory_create(self, min_size, max_size):
        """ Create memory. """
        assert max_size is not None

        # Allow only a single memory:
        assert len(self._memories) == 0

        # Allocate room on top of python heap:
        self.mem0_start = self._py_module._irpy_heap_top()
        initial_data = bytes(min_size * PAGE_SIZE)
        self._py_module._irpy_heap.extend(initial_data)

        # Store pointer to heap top:
        mem0_ptr_ptr = self._py_module.wasm_mem0_address
        self._py_module.store_i32(self.mem0_start, mem0_ptr_ptr)

        # Create memory object:
        mem0 = PythonWasmMemory(self, min_size, max_size)
        self._memories.append(mem0)

    def memory_grow(self, amount):
        """ Grow memory and return the old size """
        max_size = self._memories[0].max_size
        assert max_size is not None
        old_size = self.memory_size()
        new_size = old_size + amount
        if new_size > max_size:
            return -1
        else:
            self._py_module._irpy_heap.extend(bytes(amount * PAGE_SIZE))
            return old_size

    def memory_size(self):
        """ return memory size in pages """
        size = (
            self._py_module._irpy_heap_top() - self.mem0_start
        ) // PAGE_SIZE
        return size

    def get_func_by_index(self, index: int):
        exported_name = self._wasm_function_names[index]
        # TODO: handle multiple return values.
        return getattr(self._py_module, exported_name)

    def get_global_by_index(self, index: int):
        global_name = self._wasm_global_names[index]
        return PythonWasmGlobal(global_name, self)


class PythonWasmMemory(WasmMemory):
    """ Python wasm memory emulation """

    def __init__(self, instance, min_size, max_size):
        super().__init__(min_size, max_size)
        self._module = instance

    def write(self, address: int, data: bytes):
        address = self._module.mem0_start + address
        self._module._py_module.write_mem(address, data)

    def read(self, address: int, size: int) -> bytes:
        address = self._module.mem0_start + address
        data = self._module._py_module.read_mem(address, size)
        assert len(data) == size
        return data


# TODO: we might implement the descriptor protocol in some way?
class PythonWasmGlobal(WasmGlobal):
    def __init__(self, name, instance):
        super().__init__(name)
        self.instance = instance

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
