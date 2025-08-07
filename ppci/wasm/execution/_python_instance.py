"""Instatiate wasm module as python code."""

import logging
import io
from types import ModuleType
from ...arch.arch_info import TypeInfo
from ...irutils import verify_module
from ... import ir
from ..components import Table
from .. import wasm_to_ir
from ..util import PAGE_SIZE
from ._base_instance import ModuleInstance
from ._base_instance import WasmMemory, WasmGlobal, WasmTable

logger = logging.getLogger("instantiate")


def create_py_module(modname: str, pysrc: str) -> ModuleType:
    """Create a loaded python module from source"""
    pycode = compile(pysrc, "<string>", "exec")
    py_module = ModuleType(modname)
    # py_module.__dict__.upd
    exec(pycode, py_module.__dict__)
    return py_module


def get_irpy_rt() -> ModuleType:
    """Return singleton runtime instance"""
    if hasattr(get_irpy_rt, "_instance"):
        return getattr(get_irpy_rt, "_instance")
    from ...lang.python.ir2py import irpy_runtime_code

    f = io.StringIO()
    irpy_runtime_code(f)
    pysrc = f.getvalue()
    py_module = create_py_module("irpy_rt", pysrc)
    setattr(get_irpy_rt, "_instance", py_module)
    return py_module


def python_instantiate(
    module, imports, reporter, cache_file
) -> "PythonModuleInstance":
    """Load wasm module as a PythonModuleInstance"""
    from ...api import ir_to_python

    logger.info("Instantiating wasm module as python")
    ptr_info = TypeInfo(4, 4)
    ppci_module = wasm_to_ir(module, ptr_info, reporter=reporter)
    verify_module(ppci_module)
    f = io.StringIO()
    ir_to_python([ppci_module], f, reporter=reporter, runtime=False)
    pysrc = f.getvalue()
    pycode = compile(pysrc, "<string>", "exec")
    py_module = ModuleType("gen")
    rt_module = get_irpy_rt()
    rt = rt_module.rt.clone()
    py_module.rt = rt
    exec(pycode, py_module.__dict__)

    instance = PythonModuleInstance(py_module, imports)
    instance._wasm_function_names = ppci_module._wasm_function_names
    instance._wasm_global_names = ppci_module._wasm_global_names
    return instance


class PythonModuleInstance(ModuleInstance):
    """Wasm module loaded a generated python module"""

    def __init__(self, py_module, imports):
        super().__init__()
        self._py_module = py_module

        # Magical python memory interface, add it now:
        imports["wasm_rt_memory_grow"] = self.memory_grow
        imports["wasm_rt_memory_size"] = self.memory_size
        imports["wasm_rt_memory_init"] = self.memory_init
        imports["wasm_rt_memory_copy"] = self.memory_copy
        imports["wasm_rt_memory_fill"] = self.memory_fill

        # Link all imports:
        for name, obj in imports.items():
            if isinstance(obj, Table):
                # print(name, obj)
                ptr_size = 4
                table_byte_size = obj.max * ptr_size
                table_addr = self._py_module.rt.heap_top()
                self._py_module.rt._heap.extend(bytes(table_byte_size))
                obj = table_addr
                self.define("func_table", table_addr)
            elif callable(obj):
                self.define(name, obj)
            elif isinstance(obj, PythonWasmGlobal):
                # self.define(name, obj.)
                pass
            else:
                raise NotImplementedError(f"Cannot link: {obj}")

    def define(self, name: str, obj):
        """Define a symbol"""
        assert name not in self._py_module.rt.externals
        self._py_module.rt.externals[name] = obj

    def _run_init(self):
        self._py_module._run_init()

    def memory_create(self, min_size, max_size):
        """Create memory."""
        assert max_size is not None

        # Allow only a single memory:
        assert len(self._memories) == 0

        # Create memory object:
        mem0 = PythonWasmMemory(self, min_size, max_size)
        self._memories.append(mem0)

    def get_func_by_index(self, index: int):
        exported_name = self._wasm_function_names[index]
        # TODO: handle multiple return values.
        return self._py_module.rt.externals[exported_name]

    def get_global_by_index(self, index: int):
        ty, name = self._wasm_global_names[index]
        return PythonWasmGlobal(ty, name, self)


class PythonWasmMemory(WasmMemory):
    """Python wasm memory emulation"""

    def __init__(self, instance, min_size, max_size):
        super().__init__(min_size, max_size)
        self._module = instance

        # Allocate room on top of python heap:
        self._mem0_start = self._module._py_module.rt.heap_top()
        initial_data = bytes(min_size * PAGE_SIZE)
        self._module._py_module.rt.heap.extend(initial_data)

        # Store pointer to heap top:
        mem0_ptr_ptr = self._module._py_module.wasm_mem0_address
        self._module._py_module.rt.store_i32(mem0_ptr_ptr, self._mem0_start)

    def grow(self, amount):
        """Grow memory and return the old size"""
        max_size = self.max_size
        assert max_size is not None
        old_size = self.size()
        new_size = old_size + amount
        if new_size > max_size:
            return -1

        new_data = bytes(amount * PAGE_SIZE)
        self._module._py_module.rt.heap.extend(new_data)
        return old_size

    def size(self) -> int:
        """return memory size in pages"""
        size = (
            self._module._py_module.rt.heap_top() - self._mem0_start
        ) // PAGE_SIZE
        return size

    def write(self, address: int, data: bytes):
        address = self._mem0_start + address
        self._module._py_module.rt.write_mem(address, data)

    def read(self, address: int, size: int) -> bytes:
        address = self._mem0_start + address
        data = self._module._py_module.rt.read_mem(address, size)
        assert len(data) == size
        return data


# TODO: we might implement the descriptor protocol in some way?
class PythonWasmGlobal(WasmGlobal):
    def __init__(self, ty, name, instance):
        super().__init__(ty, name)
        self.instance = instance

    def _get_ptr(self):
        addr = self.instance._py_module.rt.externals[self.name]
        return addr

    def read(self):
        address = self._get_ptr()
        mp = {
            ir.i32: self.instance._py_module.rt.load_i32,
            ir.i64: self.instance._py_module.rt.load_i64,
        }
        f = mp[self.ty]
        return f(address)

    def write(self, value):
        address = self._get_ptr()
        mp = {
            ir.i32: self.instance._py_module.rt.store_i32,
            ir.i64: self.instance._py_module.rt.store_i64,
        }
        f = mp[self.ty]
        f(address, value)


class PythonWasmTable(WasmTable):
    def __init__(self, instance):
        super().__init__()
        self._instance = instance
