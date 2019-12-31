""" Java virtual machine (JVM).

This module supports loading and saving of java bytecode.

See also:

https://en.wikipedia.org/wiki/Java_bytecode_instruction_listings
"""

from .io import read_jar, read_class_file
from .class2ir import class_to_ir
from .class_loader import ClassLoader
from .dynload import load_class
from .printer import print_class_file


__all__ = [
    "class_to_ir",
    "read_class_file",
    "read_jar",
    "load_class",
    "print_class_file",
    "ClassLoader",
]
