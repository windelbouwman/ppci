"""
    Test fortran front end.

    See for a good test-suite:
    http://www.itl.nist.gov/div897/ctg/fortran_form.htm

"""
import unittest
import glob
from ppci.lang.fortran import FortranParser, Printer
from util import relpath

example = """
C234567890
      PROGRAM PETROL
      INTEGER STOPS, FILLUP
C
C THESE VARIABLES WOULD OTHERWISE BE TYPED REAL BY DEFAULT
C ANY TYPE SPECIFICATIONS MUST PRECEDE THE FIRST EXECUTABLE STATEMENT
C
      READ *, KM,STOPS,FILLUP
      USED = 40*STOPS + FILLUP
C COMPUTES THE PETROL USED AND CONVERTS IT TO REAL
      KPL = KM/USED + 0.5
C 0.5 IS ADDED TO ENSURE THAT THE RESULT IS ROUNDED
      PRINT *, 'AVERAGE KPL WAS',KPL
      END
"""

hello_world_src = """
      PRINT *, "Hello World!"
      END
"""

space_ignoring_src = """
C234567890
      PRO GRAMABC

"""


class FortranTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = FortranParser()
        self.printer = Printer()

    def do(self, src):
        #print('======')
        prog = self.parser.parse(src)
        #self.printer.print(prog)
        #print('======')

    def test_hello_world(self):
        """ Test hello world program """
        self.do(hello_world_src)

    def test_example(self):
        """ Test a simple example """
        self.do(example)

    @unittest.skip('todo')
    def test_spaced_prog(self):
        """ Test if a program with lots of spacing works correctly """
        self.do(space_ignoring_src)

    @unittest.skip('todo')
    def test_samples(self):
        pat = relpath('FORTRAN', '*.FOR')
        for src in sorted(glob.iglob(pat)):
            print(src)
            with open(src) as f:
                srccode = f.read()
            self.do(srccode)


if __name__ == '__main__':
    unittest.main()
