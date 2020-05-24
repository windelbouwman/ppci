import unittest
import io

from ppci.binutils.archive import archive, get_archive
from ppci.binutils.linker import link
from ppci.binutils.objectfile import ObjectFile
from ppci.api import get_arch


class ArchiveFileTestCase(unittest.TestCase):
    def test_save_load(self):
        """ Test some simple code paths of save and load. """
        lib = archive([])
        f = io.StringIO()
        lib.save(f)
        f2 = io.StringIO(f.getvalue())
        lib2 = get_archive(f2)
        self.assertTrue(lib2)

    def test_linking(self):
        """ Test pull in of undefined symbols from libraries. """
        arch = get_arch('msp430')
        obj1 = ObjectFile(arch)
        obj1.create_section('foo')
        obj1.add_symbol(0, 'printf', 'global', None, None, 'func', 0)  # undefined

        obj2 = ObjectFile(arch)
        obj3 = ObjectFile(arch)
        obj3.create_section('foo')
        obj3.add_symbol(0, 'syscall', 'global', 0, 'foo', 'func', 0)  # defined
        lib1 = archive([obj2, obj3])

        obj4 = ObjectFile(arch)
        obj4.create_section('foo')
        obj4.add_symbol(0, 'putc', 'global', 0, 'foo', 'func', 0)  # defined
        obj4.add_symbol(1, 'syscall', 'global', None, None, 'func', 0)  # undefined
        obj5 = ObjectFile(arch)
        obj5.create_section('foo')
        obj5.add_symbol(0, 'printf', 'global', 0, 'foo', 'func', 0)  # defined
        obj5.add_symbol(1, 'putc', 'global', None, None, 'func', 0)  # undefined
        lib2 = archive([obj4, obj5])

        obj = link([obj1], libraries=[lib1, lib2])


if __name__ == '__main__':
    unittest.main()
