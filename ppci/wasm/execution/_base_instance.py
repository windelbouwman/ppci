import logging
import abc
from .. import components

logger = logging.getLogger("instantiate")


class ModuleInstance(abc.ABC):
    """Web assembly module instance"""

    def __init__(self):
        self.exports = Exports()
        self._tables = []
        self._memories = []
        self._datas = []
        self._elems = []

    @abc.abstractmethod
    def invoke(self, name, *args):
        raise NotImplementedError()

    def table_grow(self, table_idx: int, val: int, size: int) -> int:
        logger.debug(f"table_grow({table_idx=}, {size=}, {val=})")
        if size < 0:
            # When i32 is large, it's signed value is negative.
            return -1
        table = self._tables[table_idx]
        return table.grow(val, size)

    def table_size(self, table_idx: int) -> int:
        logger.debug(f"table_size({table_idx=})")
        table = self._tables[table_idx]
        return table.size()

    def table_init(
        self, table_idx: int, elem_idx: int, d: int, s: int, n: int
    ) -> None:
        logger.debug(
            f"table_init({table_idx=}, {elem_idx=}, {d=}, {s=}, {n=})"
        )
        table = self._tables[table_idx]
        elem = self._elems[elem_idx]
        if s + n > elem.size():
            raise ValueError("s + n > elem.size")
        if d + n > table.size():
            raise ValueError("d + n > table.size")
        for index in range(n):
            obj = elem.get_item(s + index)
            table.set_item(d + index, obj)

    def table_copy(
        self, x_table_idx: int, y_table_idx: int, d: int, s: int, n: int
    ) -> None:
        logger.debug(
            f"table_copy({x_table_idx=}, {y_table_idx=}, {d=}, {s=}, {n=})"
        )
        x_table = self._tables[x_table_idx]
        y_table = self._tables[y_table_idx]
        if d + n > x_table.size():
            raise ValueError("d + n > x_table.size")
        if s + n > y_table.size():
            raise ValueError("s + n > y_table.size")

        # Regions may overlap, so check dest and source:
        if d <= s:
            for index in range(n):
                obj = y_table.get_item(s + index)
                x_table.set_item(d + index, obj)
        else:
            for index2 in range(n):
                index = n - 1 - index2
                obj = y_table.get_item(s + index)
                x_table.set_item(d + index, obj)

    def table_fill(self, table_idx: int, i: int, val: int, n: int) -> None:
        logger.debug(f"table_fill({table_idx=}, {i=}, {val=}, {n=})")
        table = self._tables[table_idx]
        for x in range(n):
            index = i + x
            table.set_item(index, val)

    def elem_drop(self, elem_idx: int) -> None:
        pass

    def memory_grow(self, memory_idx: int, amount: int) -> int:
        """Grow memory and return the old size"""
        memory = self._memories[memory_idx]
        return memory.grow(amount)

    def memory_size(self, memory_idx: int) -> int:
        """return memory size in pages"""
        memory = self._memories[memory_idx]
        return memory.size()

    def memory_init(
        self, data_idx: int, memory_idx: int, dst: int, src: int, n: int
    ) -> None:
        """Perform memcpy-ish operation"""
        logger.debug(
            f"memory_init {data_idx=}, {memory_idx=}, {dst=}, {src=}, {n=}"
        )
        data = self._datas[data_idx]
        memory = self._memories[memory_idx]
        blob = data[src : src + n]
        memory.write(dst, blob)

    def memory_copy(
        self, memory_idx: int, memory_idx2: int, dst: int, src: int, n: int
    ) -> None:
        """Memcpy operation"""
        assert memory_idx == memory_idx2
        memory = self._memories[memory_idx]
        blob = memory.read(src, n)
        memory.write(dst, blob)

    def memory_fill(self, memory_idx: int, dst: int, val: int, n: int) -> None:
        memory = self._memories[memory_idx]
        blob = bytes([val] * n)
        memory.write(dst, blob)

    @abc.abstractmethod
    def memory_create(self, min_size, max_size):
        raise NotImplementedError()

    @abc.abstractmethod
    def create_table(self, size, max_size):
        raise NotImplementedError()

    @abc.abstractmethod
    def set_table_ptr(self, index, table):
        raise NotImplementedError()

    @abc.abstractmethod
    def create_elem(self, index: int, size: int):
        raise NotImplementedError()

    def eval_expression(self, expr):
        assert len(expr) == 1
        assert expr[0].opcode == "i32.const"
        return expr[0].args[0]

    def load_memory(self, wasm_module):
        """Create memory and load initial data."""
        initializations = []
        for definition in wasm_module:
            if isinstance(definition, components.Memory):
                min_size = definition.min
                max_size = definition.max
                if max_size is None:
                    max_size = 0x10000
                self.memory_create(min_size, max_size)
            elif isinstance(definition, components.Data):
                if definition.mode:
                    ref, offset = definition.mode
                    offset = self.eval_expression(offset)
                    memory_index = ref.index
                    assert ref.space == "memory"
                    assert isinstance(memory_index, int)
                    data = definition.data
                    initializations.append((memory_index, offset, data))
                self._datas.append(definition.data)

        # Initialize various parts:
        for memory_index, offset, data in initializations:
            memory = self._memories[memory_index]
            memory.write(offset, data)

    def load_tables(self, wasm_module):
        """Create tables and initialize them."""
        elems = []
        for definition in wasm_module:
            if isinstance(definition, components.Table):
                index = len(self._tables)
                size = definition.min
                table = self.create_table(size, definition.max)
                self._tables.append(table)
                self.set_table_ptr(index, table)
            elif isinstance(definition, components.Elem):
                elems.append(definition)
                index = len(self._elems)
                size = len(definition.refs)
                self._elems.append(self.create_elem(index, size))

        for index, elem in enumerate(elems):
            if elem.mode:
                # copy elements into table
                ref, offset = elem.mode
                assert ref.space == "table"
                offset = self.eval_expression(offset)
                table = self._tables[ref.index]
                elem_instance = self._elems[index]
                for i, ref in enumerate(elem.refs):
                    ptr = elem_instance.get_item(i)
                    table.set_item(offset + i, ptr)

    @abc.abstractmethod
    def get_func_by_index(self, index: int):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_global_by_index(self, index: int):
        raise NotImplementedError()

    def populate_exports(self, module):
        """Export all exported items"""
        for definition in module:
            if isinstance(definition, components.Export):
                if definition.kind == "func":
                    item = self.get_func_by_index(definition.ref.index)
                    # TODO: handle multiple return values, maybe here?
                elif definition.kind == "global":
                    logger.debug(f"global exported: {definition.name}")
                    item = self.get_global_by_index(definition.ref.index)
                elif definition.kind == "memory":
                    logger.debug("memory exported")
                    item = self._memories[definition.ref.index]
                elif definition.kind == "table":
                    logger.debug(f"exporting table as {definition.name}")
                    item = self._tables[definition.ref.index]
                else:  # pragma: no cover
                    raise NotImplementedError(definition.kind)
                self.exports._add(definition.name, item)


class ElemInstance(abc.ABC):
    """Runtime element instance"""

    def __init__(self, size: int):
        self._size = size

    def size(self) -> int:
        return self._size

    @abc.abstractmethod
    def get_item(self, index: int):
        raise NotImplementedError()


class TableInstance(abc.ABC):
    """Base class for an exported wasm table"""

    def __init__(self, max_size):
        self._max_size = max_size

    @abc.abstractmethod
    def size(self) -> int:
        raise NotImplementedError()

    @abc.abstractmethod
    def grow(self, val, amount: int) -> int:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_item(self, index: int):
        raise NotImplementedError()

    @abc.abstractmethod
    def set_item(self, index: int, value):
        raise NotImplementedError()


class MemoryInstance(abc.ABC):
    """Base class for exported wasm memory."""

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
    def grow(self, amount: int) -> int:
        raise NotImplementedError()

    @abc.abstractmethod
    def size(self) -> int:
        raise NotImplementedError()

    @abc.abstractmethod
    def write(self, address, data):
        raise NotImplementedError()

    @abc.abstractmethod
    def read(self, address, size):
        raise NotImplementedError()


class GlobalInstance(abc.ABC):
    """Base class for an exported wasm global."""

    def __init__(self, ty, name):
        self.ty = ty
        self.name = name

    @property
    def value(self):
        """The value of the global variable"""
        return self.read()

    @abc.abstractmethod
    def read(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def write(self, value):
        raise NotImplementedError()


class Exports:
    """Container for exported functions"""

    def __init__(self):
        self._map = {}

    def __getitem__(self, key):
        assert isinstance(key, str)
        return self._map[key]

    def __getattr__(self, name):
        if name in self._map:
            return self._map[name]
        else:
            raise AttributeError(f'Name "{name}" was not exported')

    def __iter__(self):
        return iter(self._map)

    def _add(self, name, item):
        if name in self._map:
            raise ValueError(f"{name} already exported")
        if name == "_add":
            raise ValueError("Reserved export name: _add")
        self._map[name] = item


class WasmTrapException(Exception):
    pass
