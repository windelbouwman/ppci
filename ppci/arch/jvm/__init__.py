
""" Java virtual machine (JVM).

This module supports loading and saving of java bytecode.

See also:

https://en.wikipedia.org/wiki/Java_bytecode_instruction_listings
"""

from .io import read_jar, read_class_file
from .class2ir import class_to_ir


__all__ = ['class_to_ir', 'read_class_file', 'read_jar']
