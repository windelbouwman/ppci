
import unittest
try:
    from ppci.utils import stlink
    import usb.core
except ImportError:
    stlink = None


class StLink2TestCase(unittest.TestCase):
    def setUp(self):
        if stlink is None:
            self.skipTest('Stlink not imported')
        try:
            self.stlink = stlink.STLink2()
            self.stlink.open()
            self.stlink.reset()
        except stlink.STLinkException as e:
            self.skipTest('Skipping: {}'.format(e))
        except usb.core.USBError as e:
            self.skipTest('Skipping: {}'.format(e))
        except ValueError as e:
            self.skipTest('Skipping: {}'.format(e))

    def tearDown(self):
        self.stlink.close()

    def testRegisterAccess(self):
        """ test register read and write """
        self.stlink.write_reg(0, 0xdeadbeef)
        self.stlink.write_reg(1, 0xcafebabe)
        self.stlink.write_reg(2, 0xc0ffee)
        self.stlink.write_reg(3, 0x1337)
        self.stlink.write_reg(5, 0x1332)
        self.stlink.write_reg(6, 0x12345)
        regs = self.stlink.read_all_regs()
        self.assertEqual(0x1337, regs[3])
        self.assertEqual(0x1332, regs[5])
        self.assertEqual(0x12345, regs[6])
        self.assertEqual(0x1337, self.stlink.read_reg(3))
        self.assertEqual(0x1332, self.stlink.read_reg(5))
        self.assertEqual(0x12345, self.stlink.read_reg(6))

    def testVersion(self):
        """ Check the stlink read version command """
        assert self.stlink.Version.startswith('stlink=2')
