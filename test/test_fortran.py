import unittest
from ppci.fortran import FortranParser


class FortranTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = FortranParser()

    def do(self, src):
        print(src)
        self.parser.parse(src)

    def test_hello_world(self):
        src = """
        PRINT *, "Hello World!"
               END
        """
        self.do(src)


if __name__ == '__main__':
    unittest.main()
