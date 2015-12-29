import unittest
import io
from ppci.utils.hexfile import HexFile, HexFileException


class HexFileTestCase(unittest.TestCase):
    def save_load(self, hf):
        f = io.StringIO()
        hf.save(f)
        hf2 = HexFile.load(io.StringIO(f.getvalue()))
        self.assertEqual(hf, hf2)

    def test_save1(self):
        hf = HexFile()
        hf.add_region(0x8000, bytes.fromhex('aabbcc'))
        self.save_load(hf)

    def test_save2(self):
        hf = HexFile()
        hf.add_region(0x8000, bytes.fromhex('aabbcc'))
        hf.add_region(0x118000, bytes.fromhex('aabbcc'))
        self.save_load(hf)

    def test_save3(self):
        hf = HexFile()
        hf.add_region(0x8000, bytes.fromhex('aabbcc'))
        hf.add_region(0xFFFE, bytes.fromhex('aabbcc'))
        self.save_load(hf)

    def test_save4(self):
        hf = HexFile()
        hf.add_region(0xF000, bytes.fromhex('ab')*0x10000)
        self.save_load(hf)

    def test_save5(self):
        hf = HexFile()
        hf.add_region(0xF003, bytes.fromhex('ab')*0x10000)
        self.save_load(hf)

    def test_two_regions(self):
        hf = HexFile()
        hf2 = HexFile()
        hf.add_region(0x100, bytes.fromhex('abcd'))
        hf.add_region(0x200, bytes.fromhex('beef'))
        hf2.add_region(0x200, bytes.fromhex('beef'))
        hf2.add_region(0x100, bytes.fromhex('abcd'))
        self.assertEqual(hf, hf2)

    def test_merge(self):
        hf = HexFile()
        hf.add_region(0x10, bytes.fromhex('abcdab'))
        hf.add_region(0x13, bytes.fromhex('abcdab'))
        self.assertEqual(1, len(hf.regions))

    def test_overlapped(self):
        hf = HexFile()
        hf.add_region(0x10, bytes.fromhex('abcdab'))
        with self.assertRaisesRegex(HexFileException, 'verlap'):
            hf.add_region(0x12, bytes.fromhex('abcdab'))

    def test_equal(self):
        hf1 = HexFile()
        hf2 = HexFile()
        hf1.add_region(10, bytes.fromhex('aabbcc'))
        hf2.add_region(10, bytes.fromhex('aabbcc'))
        self.assertEqual(hf1, hf2)

    def test_not_equal(self):
        hf1 = HexFile()
        hf2 = HexFile()
        hf1.add_region(10, bytes.fromhex('aabbcc'))
        hf2.add_region(10, bytes.fromhex('aabbdc'))
        self.assertNotEqual(hf1, hf2)

    def test_not_equal2(self):
        hf1 = HexFile()
        hf2 = HexFile()
        hf1.add_region(10, bytes.fromhex('aabbcc'))
        hf2.add_region(10, bytes.fromhex('aabbcc'))
        hf2.add_region(22, bytes.fromhex('aabbcc'))
        self.assertNotEqual(hf1, hf2)

    def test_load(self):
        dummyhex = """
         :01400000aa15

         w00t
        """
        f = io.StringIO(dummyhex)
        hf = HexFile.load(f)
        self.assertEqual(1, len(hf.regions))
        self.assertEqual(0x4000, hf.regions[0].address)
        self.assertSequenceEqual(bytes.fromhex('aa'), hf.regions[0].data)

    def test_incorrect_crc(self):
        txt = ":01400000aabb"
        f = io.StringIO(txt)
        with self.assertRaisesRegex(HexFileException, 'crc'):
            HexFile.load(f)

    def test_startaddress(self):
        txt = ":04000005aabbccdde9"
        f = io.StringIO(txt)
        hf = HexFile.load(f)
        self.assertEqual(0xaabbccdd, hf.start_address)

    def test_non_empty_eof(self):
        txt = ":04000001aabbccdded"
        f = io.StringIO(txt)
        with self.assertRaisesRegex(HexFileException, 'end of file not empty'):
            HexFile.load(f)

    def test_data_after_eof(self):
        txt = """:00000001FF
        :04000001aabbccdded
        """
        f = io.StringIO(txt)
        with self.assertRaisesRegex(HexFileException, 'after end of file'):
            HexFile.load(f)

    def test_incorrect_length(self):
        txt = ":0140002200aabb"
        f = io.StringIO(txt)
        with self.assertRaisesRegex(HexFileException, 'count'):
            HexFile.load(f)

if __name__ == '__main__':
    unittest.main()
