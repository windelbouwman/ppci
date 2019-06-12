import unittest
import io

from ppci.binutils.archive import archive, get_archive


class ArchiveFileTestCase(unittest.TestCase):
    def test_save_load(self):
        """ Test some simple code paths of save and load. """
        lib = archive([])
        f = io.StringIO()
        lib.save(f)
        f2 = io.StringIO(f.getvalue())
        lib2 = get_archive(f2)
        self.assertTrue(lib2)


if __name__ == '__main__':
    unittest.main()
