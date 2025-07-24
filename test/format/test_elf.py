import unittest
import io

from ppci.binutils.objectfile import ObjectFile
from ppci.format.elf import ElfFile, write_elf
from ppci.format.elf.writer import elf_hash
from ppci.api import get_arch


class ElfFileTestCase(unittest.TestCase):
    def test_save_load(self):
        arch = get_arch("arm")
        f = io.BytesIO()
        write_elf(ObjectFile(arch), f)
        f2 = io.BytesIO(f.getvalue())
        ElfFile.load(f2)

    def test_hash_function(self):
        examples = [
            ("jdfgsdhfsdfsd 6445dsfsd7fg/*/+bfjsdgf%$^", 248446350),
            ("", 0),
            ("printf", 0x077905A6),
            ("exit", 0x0006CF04),
            ("syscall", 0x0B09985C),
            ("flapenguin.me", 0x03987915),
            ("isnan", 0x0070A47E),
            ("freelocal", 0x0BC334FC),
            ("hcreate_", 0x0A8B8C4F),
            ("getopt_long_onl", 0x0F256DBC),
        ]
        for name, hash_value in examples:
            self.assertEqual(elf_hash(name), hash_value)


if __name__ == "__main__":
    unittest.main()
