import unittest

from ppci.utils import header


class HeaderTestCase(unittest.TestCase):
    def test_header_type(self):
        Hdr = header.mk_header('myheader', [
            header.Byte('b1'),
            header.Uint32('u32'),
            header.Byte('b2'),
        ])
        print(Hdr)
        h1 = Hdr()
        h2 = Hdr()
        self.assertEqual(0, h1.u32)
        self.assertEqual(6, Hdr.size)
        h1.b1 = 2
        h1.u32 = 0x1234
        assert isinstance(h1, header.BaseHeader)
        self.assertEqual(bytes([2, 0x34, 0x12, 0, 0, 0]), h1.serialize())
        self.assertEqual(bytes([0, 0, 0, 0, 0, 0]), h2.serialize())
        h3 = Hdr.deserialize(h1.serialize())
        self.assertEqual(h3.b1, 2)
        self.assertEqual(h3.u32, 0x1234)
        # TODO: __eq__? self.assertEqual(h1, h3)

    def test_header_type2(self):
        Hdr = header.mk_header('my_header', [
            header.Byte('b1'),
            header.Uint32('u32'),
        ])
        h1 = Hdr()
        self.assertEqual(0, h1.u32)
        self.assertEqual(5, Hdr.size)

    def test_const_padding(self):
        Hdr = header.mk_header('myheader', [
            header.Const(b'ELF'),
            header.Uint32('u32'),
        ])
        h1 = Hdr()
        self.assertEqual(0, h1.u32)
        self.assertEqual(7, Hdr.size)
        h1.u32 = 13
        self.assertEqual(b'ELF\x0d\x00\x00\x00', h1.serialize())


if __name__ == '__main__':
    unittest.main()
