import unittest
import io

from ppci.binutils.objectfile import ObjectFile
from ppci.format.elf import ElfFile, write_elf
from ppci.format.elf.writer import elf_hash
from ppci.api import get_arch


class ElfFileTestCase(unittest.TestCase):
    def test_save_load(self):
        arch = get_arch('arm')
        f = io.BytesIO()
        write_elf(ObjectFile(arch), f)
        f2 = io.BytesIO(f.getvalue())
        ElfFile.load(f2)

    def test_hash_function(self):
        examples = [
            ("jdfgsdhfsdfsd 6445dsfsd7fg/*/+bfjsdgf%$^",  248446350),
            ("", 0),
            ("printf", 0x077905a6),
            ("exit", 0x0006cf04),
            ("syscall", 0x0b09985c),
            ("flapenguin.me", 0x03987915),
            ("isnan", 0x0070a47e),
            ("freelocal", 0x0bc334fc),
            ("hcreate_", 0x0a8b8c4f),
            ("getopt_long_onl", 0x0f256dbc),
        ]
        for name, hash_value in examples:
            self.assertEqual(elf_hash(name), hash_value)


if __name__ == '__main__':
    unittest.main()
