""" Various utilities to operate on IR-code.
"""

from .verify import verify_module, Verifier
from .writer import Writer, print_module
from .reader import Reader, read_module
from .builder import Builder, split_block
from .link import ir_link
from .io import to_json, from_json
from .instrument import add_tracer

__all__ = [
    "Builder",
    "ir_link",
    "print_module",
    "read_module",
    "Reader",
    "split_block",
    "Verifier",
    "verify_module",
    "Writer",
    "to_json",
    "from_json",
    "add_tracer",
]
