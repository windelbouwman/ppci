import unittest
import sys
from ppci.gen_sled import Spec, Generator


class SledTestCase(unittest.TestCase):
    def testSpecApi(self):
        spec = Spec()
        sg = Generator()
        sg.generate(spec)


if __name__ == '__main__':
    unittest.main()
    sys.exit()
