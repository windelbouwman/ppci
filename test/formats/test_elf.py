import unittest
import io

from ppci.binutils.objectfile import ObjectFile
from ppci.formats.elf import ElfFile
from ppci.arch.example import ExampleArch


class ElfFileTestCase(unittest.TestCase):
    def test_save_load(self):
        arch = ExampleArch()
        ef1 = ElfFile()
        f = io.BytesIO()
        ef1.save(f, ObjectFile(arch))
        f2 = io.BytesIO(f.getvalue())
        ElfFile.load(f2)


if __name__ == '__main__':
    unittest.main()
