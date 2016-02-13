import unittest
from ppci.fortran import FortranParser

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


class FortranTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = FortranParser()

    def do(self, src):
        self.parser.parse(src)

    def test_hello_world(self):
        self.do(hello_world_src)

    def test_example(self):
        self.do(example)

if __name__ == '__main__':
    unittest.main()
