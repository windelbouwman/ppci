""" Support to process an ELF file.
"""

from .file import ElfFile

# TODO: move some parts from ElfFile to this file.


def read_elf(f):
    """ Read an ELF file """
    return ElfFile.load(f)
