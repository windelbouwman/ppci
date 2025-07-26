"""Logic to process the text based representation of wasm."""

from .parser import load_tuple, load_s_expr

__all__ = ["load_tuple", "load_s_expr"]
