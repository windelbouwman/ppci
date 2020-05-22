import unittest
import io

from ppci.binutils.objectfile import ObjectFile
from ppci.format.elf import ElfFile, write_elf
from ppci.api import get_arch


class ElfFileTestCase(unittest.TestCase):
    def test_save_load(self):
        arch = get_arch('arm')
        f = io.BytesIO()
        write_elf(ObjectFile(arch), f)
        f2 = io.BytesIO(f.getvalue())
        ElfFile.load(f2)


if __name__ == '__main__':
    unittest.main()
