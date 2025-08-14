"""Instatiate wasm module as python code."""

import logging
import io
from types import ModuleType
from ...arch.arch_info import TypeInfo
from ...irutils import verify_module
from ... import ir
from ..components import Table, Global, Memory
from .. import wasm_to_ir
from ..util import PAGE_SIZE
from ._base_instance import ModuleInstance, WasmTrapException
from ._base_instance import MemoryInstance, GlobalInstance
from ._base_instance import TableInstance, ElemInstance

logger = logging.getLogger("instantiate")


def create_py_module(modname: str, pysrc: str) -> ModuleType:
    """Create a loaded python module from source"""
    pycode = compile(pysrc, "<string>", "exec")
    py_module = ModuleType(modname)
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

    instance = PythonModuleInstance(py_module, imports, ppci_module._wasm_info)
    return instance


class PythonModuleInstance(ModuleInstance):
    """Wasm module loaded a generated python module"""

    def __init__(self, py_module, imports, wasm_info):
        super().__init__(wasm_info)
        self._py_module = py_module

        # Magical python memory interface, add it now:
        imports["wasm_rt_table_grow"] = self.table_grow
        imports["wasm_rt_table_size"] = self.table_size
        imports["wasm_rt_table_init"] = self.table_init
        imports["wasm_rt_table_copy"] = self.table_copy
        imports["wasm_rt_table_fill"] = self.table_fill
        imports["wasm_rt_elem_drop"] = self.elem_drop

        imports["wasm_rt_memory_grow"] = self.memory_grow
        imports["wasm_rt_memory_size"] = self.memory_size
        imports["wasm_rt_memory_init"] = self.memory_init
        imports["wasm_rt_memory_copy"] = self.memory_copy
        imports["wasm_rt_memory_fill"] = self.memory_fill

        # Link all imports:
        for name, obj in imports.items():
            if isinstance(obj, Table):
                table = self.create_table(obj.min, obj.max)
                self._tables.append(table)
                table_ptr = self.malloc(4)
                self.store_ptr(table_ptr, table._get_ptr())
                self.define(name, table_ptr)
            elif isinstance(obj, PythonWasmFunc):
                self.define(name, obj._f)
                ptr = obj._get_ptr()
                self._py_module.rt.f_ptrs_by_name[name] = ptr
            elif isinstance(obj, Global):
                addr = self.malloc(8)
                self.define(name, addr)
                index = len(self._globals)
                g = self.create_global(index)
                v = self.eval_expression(obj.init)
                g.write(v)
                self._globals.append(g)
            elif isinstance(obj, PythonGlobalInstance):
                self.define(name, obj._get_ptr())
                self._globals.append(obj)
            elif isinstance(obj, PythonTableInstance):
                self._tables.append(obj)
                table_ptr = self.malloc(4)
                self.store_ptr(table_ptr, obj._get_ptr())
                self.define(name, table_ptr)
            elif isinstance(obj, Memory):
                self.memory_create(obj.min, obj.max)
            elif callable(obj):
                self.define(name, obj)
            else:
                raise NotImplementedError(f"Cannot link: {name}={obj}")

    def define(self, name: str, obj):
        """Define a symbol"""
        if name in self._py_module.rt.externals:
            raise ValueError(f"{name} already defined")
        self._py_module.rt.externals[name] = obj

    def malloc(self, size: int):
        addr = self._py_module.rt.heap_top()
        self._py_module.rt.heap.extend(bytes(size))
        return addr

    def invoke(self, name, *args):
        """Invoke the function 'name'"""
        f = self._py_module.rt.externals[name]
        f(*args)

    def memory_create(self, min_size, max_size):
        """Create memory."""
        assert max_size is not None

        # Allow only a single memory:
        assert len(self._memories) == 0

        # Create memory object:
        mem0 = PythonMemoryInstance(self, min_size, max_size)
        self._memories.append(mem0)

    def create_table(self, size, max_size) -> "PythonTableInstance":
        """Create table according to format

        format:
        - ptr -> pointer to data
        - i32 -> size of table
        """
        ptr_size = 4
        meta_size = ptr_size + 4
        meta_addr = self.malloc(meta_size)
        data_addr = self.malloc(size * ptr_size)
        self.store_ptr(meta_addr, data_addr)
        self.store_i32(meta_addr + ptr_size, size)
        table = PythonTableInstance(meta_addr, self, max_size)
        return table

    def set_table_ptr(self, index, table):
        # Store ptr:
        name = self._wasm_info.table_names[index]
        addr = getattr(self._py_module, name)
        self.store_ptr(addr, table._get_ptr())

    def create_elem(self, index: int, size: int) -> "PythonElemInstance":
        name = self._wasm_info.elem_names[index]
        addr = getattr(self._py_module, name)
        return PythonElemInstance(addr, self, size)

    def get_func_by_index(self, index: int):
        exported_name = self._wasm_info.function_names[index]
        # TODO: handle multiple return values.
        # pi = self._py_module.rt.f_ptrs_by_name[exported_name]
        f = self._py_module.rt.externals[exported_name]
        return PythonWasmFunc(f, exported_name, self)

    def create_global(self, index: int) -> "PythonGlobalInstance":
        ty, name = self._wasm_info.global_names[index]
        return PythonGlobalInstance(ty, name, self)

    def load_i32(self, address: int) -> int:
        return self._py_module.rt.load_i32(address)

    def store_i32(self, address, value: int):
        self._py_module.rt.store_i32(address, value)

    def load_i64(self, address: int) -> int:
        return self._py_module.rt.load_i64(address)

    def store_i64(self, address, value: int):
        self._py_module.rt.store_i64(address, value)

    def load_ptr(self, address: int) -> int:
        return self._py_module.rt.load_u32(address)

    def store_ptr(self, address, value: int):
        self._py_module.rt.store_u32(address, value)


class PythonMemoryInstance(MemoryInstance):
    """Python wasm memory emulation"""

    def __init__(self, instance, min_size, max_size):
        super().__init__(min_size, max_size)
        self._module = instance

        # Allocate room on top of python heap:
        self._mem0_start = self._module.malloc(min_size * PAGE_SIZE)

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
class PythonGlobalInstance(GlobalInstance):
    def __init__(self, ty, name, instance):
        super().__init__(ty, name)
        self.instance = instance

    def _get_ptr(self):
        addr = self.instance._py_module.rt.externals[self.name]
        return addr

    def read(self):
        address = self._get_ptr()
        mp = {
            ir.i32: self.instance.load_i32,
            ir.i64: self.instance.load_i64,
        }
        f = mp[self.ty]
        return f(address)

    def write(self, value):
        address = self._get_ptr()
        mp = {
            ir.i32: self.instance.store_i32,
            ir.i64: self.instance.store_i64,
        }
        f = mp[self.ty]
        f(address, value)


class PythonWasmFunc:
    def __init__(self, f, name, instance):
        self._f = f
        self._name = name
        self._instance = instance

    def __call__(self, *args):
        try:
            return self._f(*args)
        except ZeroDivisionError as ex:
            raise WasmTrapException("integer divide by zero") from ex

    def _get_ptr(self):
        return self._instance._py_module.rt.f_ptrs_by_name[self._name]


class PythonTableInstance(TableInstance):
    def __init__(self, addr: int, instance: "PythonModuleInstance", max_size):
        super().__init__(max_size)
        if not isinstance(addr, int):
            raise TypeError("addr must be int")
        self._addr = addr
        assert isinstance(instance, PythonModuleInstance)
        self._instance = instance

    def _get_ptr(self) -> int:
        return self._addr

    def size(self) -> int:
        base_ptr = self._get_ptr()
        size_ptr = base_ptr + 4
        return self._instance.load_i32(size_ptr)

    def grow(self, val, count: int) -> int:
        ptr_size = 4
        old_size = self._instance.load_i32(self._addr + ptr_size)
        new_size = old_size + count
        if new_size > 0xFFFF_FFFF:
            return -1
        if self._max_size is not None and new_size > self._max_size:
            return -1
        old_addr = self._instance.load_ptr(self._addr)
        new_addr = self._instance.malloc(new_size * ptr_size)
        for i in range(new_size):
            offset = i * ptr_size
            if i < old_size:
                p = self._instance.load_ptr(old_addr + offset)
            else:
                p = val
            self._instance.store_ptr(new_addr + offset, p)
        self._instance.store_ptr(self._addr, new_addr)
        self._instance.store_ptr(self._addr + ptr_size, new_size)
        return old_size

    def set_item(self, index: int, value):
        base_ptr = self._get_ptr()
        data_ptr = self._instance.load_ptr(base_ptr) + 4 * index
        self._instance.store_ptr(data_ptr, value)

    def get_item(self, index: int):
        base_ptr = self._get_ptr()
        data_ptr = self._instance.load_ptr(base_ptr) + 4 * index
        return self._instance.load_ptr(data_ptr)


class PythonElemInstance(ElemInstance):
    def __init__(self, addr: int, instance, size):
        super().__init__(size)
        self._addr = addr
        self._instance = instance

    def get_item(self, index: int):
        return self._instance.load_ptr(self._addr + index * 4)
