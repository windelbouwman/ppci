from ._instantiate import instantiate
from .execute import execute_wasm
from ._base_instance import WasmTrapException

__all__ = ("instantiate", "execute_wasm", "WasmTrapException")
