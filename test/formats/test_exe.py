import io
import unittest

from ppci.api import get_arch
from ppci.binutils.objectfile import ObjectFile
from ppci.formats.exefile import ExeWriter


class ExeFileTestCase(unittest.TestCase):
    @unittest.skip('TODO')
    def test_save(self):
        """ Test the generation of a windows exe file """
        arch = get_arch('x86_64')
        obj = ObjectFile(arch)
        obj.get_section('code', create=True)
        obj.get_section('data', create=True)
        f = io.BytesIO()
        # TODO:
        ExeWriter().write(obj, f)


if __name__ == '__main__':
    unittest.main()
