"""Logic to process the text based representation of wasm."""

from .parser import load_tuple, load_s_expr, load_from_s_tokens

__all__ = ["load_tuple", "load_s_expr", "load_from_s_tokens"]
