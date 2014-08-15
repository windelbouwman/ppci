import unittest
import io
from ppci.utils.hexfile import HexFile, HexFileException


class HexFileTestCase(unittest.TestCase):
    def saveload(self, hf):
        f = io.StringIO()
        hf.save(f)
        hf2 = HexFile()
        hf2.load(io.StringIO(f.getvalue()))
        self.assertEqual(hf, hf2)

    def testSave1(self):
        hf = HexFile()
        hf.add_region(0x8000, bytes.fromhex('aabbcc'))
        self.saveload(hf)

    def testSave2(self):
        hf = HexFile()
        hf.add_region(0x8000, bytes.fromhex('aabbcc'))
        hf.add_region(0x118000, bytes.fromhex('aabbcc'))
        self.saveload(hf)

    def testSave3(self):
        hf = HexFile()
        hf.add_region(0x8000, bytes.fromhex('aabbcc'))
        hf.add_region(0xFFFE, bytes.fromhex('aabbcc'))
        self.saveload(hf)

    def testSave4(self):
        hf = HexFile()
        hf.add_region(0xF000, bytes.fromhex('ab')*0x10000)
        self.saveload(hf)

    def testSave5(self):
        hf = HexFile()
        hf.add_region(0xF003, bytes.fromhex('ab')*0x10000)
        self.saveload(hf)

    def testTwoRegions(self):
        hf = HexFile()
        hf2 = HexFile()
        hf.add_region(0x100, bytes.fromhex('abcd'))
        hf.add_region(0x200, bytes.fromhex('beef'))
        hf2.add_region(0x200, bytes.fromhex('beef'))
        hf2.add_region(0x100, bytes.fromhex('abcd'))
        self.assertEqual(hf, hf2)

    def testMerge(self):
        hf = HexFile()
        hf.add_region(0x10, bytes.fromhex('abcdab'))
        hf.add_region(0x13, bytes.fromhex('abcdab'))
        self.assertEqual(1, len(hf.regions))

    def testOverlapped(self):
        hf = HexFile()
        hf.add_region(0x10, bytes.fromhex('abcdab'))
        with self.assertRaisesRegex(HexFileException, 'verlap'):
            hf.add_region(0x12, bytes.fromhex('abcdab'))

    def testEqual(self):
        hf1 = HexFile()
        hf2 = HexFile()
        hf1.add_region(10, bytes.fromhex('aabbcc'))
        hf2.add_region(10, bytes.fromhex('aabbcc'))
        self.assertEqual(hf1, hf2)

    def testNotEqual(self):
        hf1 = HexFile()
        hf2 = HexFile()
        hf1.add_region(10, bytes.fromhex('aabbcc'))
        hf2.add_region(10, bytes.fromhex('aabbdc'))
        self.assertNotEqual(hf1, hf2)

    def testNotEqual2(self):
        hf1 = HexFile()
        hf2 = HexFile()
        hf1.add_region(10, bytes.fromhex('aabbcc'))
        hf2.add_region(10, bytes.fromhex('aabbcc'))
        hf2.add_region(22, bytes.fromhex('aabbcc'))
        self.assertNotEqual(hf1, hf2)

    def testLoad(self):
        hf = HexFile()
        dummyhex = """:01400000aa15"""
        f = io.StringIO(dummyhex)
        hf.load(f)
        self.assertEqual(1, len(hf.regions))
        self.assertEqual(0x4000, hf.regions[0].address)
        self.assertSequenceEqual(bytes.fromhex('aa'), hf.regions[0].data)

    def testIncorrectCrc(self):
        hf = HexFile()
        txt = ":01400000aabb"
        f = io.StringIO(txt)
        with self.assertRaisesRegex(HexFileException, 'crc'):
            hf.load(f)

    def testIncorrectLength(self):
        hf = HexFile()
        txt = ":0140002200aabb"
        f = io.StringIO(txt)
        with self.assertRaisesRegex(HexFileException, 'count'):
            hf.load(f)

if __name__ == '__main__':
    unittest.main()
