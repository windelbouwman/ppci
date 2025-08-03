import logging
import abc
from .. import components

logger = logging.getLogger("instantiate")


class ModuleInstance(abc.ABC):
    """Web assembly module instance"""

    """ Instantiated module """

    def __init__(self):
        self.exports = Exports()
        self._memories = []
        self._datas = []

    @abc.abstractmethod
    def _run_init(self):
        raise NotImplementedError()

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
                    assert len(offset) == 1
                    assert offset[0].opcode == "i32.const"
                    offset = offset[0].args[0]
                    memory_index = ref.index
                    assert isinstance(memory_index, int)
                    data = definition.data
                    initializations.append((memory_index, offset, data))
                self._datas.append(definition.data)

        # Initialize various parts:
        for memory_index, offset, data in initializations:
            memory = self._memories[memory_index]
            memory.write(offset, data)

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
                    logger.debug("global exported")
                    item = self.get_global_by_index(definition.ref.index)
                elif definition.kind == "memory":
                    logger.debug("memory exported")
                    item = self._memories[definition.ref.index]
                elif definition.kind == "table":
                    logger.error("table not yet exported")
                    item = None
                else:  # pragma: no cover
                    raise NotImplementedError(definition.kind)
                self.exports._function_map[definition.name] = item


class WasmMemory(abc.ABC):
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


class WasmGlobal(abc.ABC):
    """Base class for an exported wasm global."""

    def __init__(self, name):
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
        self._function_map = {}

    def __getitem__(self, key):
        assert isinstance(key, str)
        return self._function_map[key]

    def __getattr__(self, name):
        if name in self._function_map:
            return self._function_map[name]
        else:
            raise AttributeError('Name "{}" was not exported'.format(name))
