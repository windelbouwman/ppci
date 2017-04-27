import unittest
import io
from ppci.api import ws2ir
from ppci.common import CompilerError


# Below the example as of wikipedia:
hello_world_source = """   \t  H\t   
\t
     \t\t  e\t \t
\t
     \t\t l\t\t  
\t
     \t\t l\t\t  
\t
     \t\t o\t\t\t\t
\t
     \t ,\t\t  
\t
     \t     
\t
     \t\t\t W\t\t\t
\t
     \t\t o\t\t\t\t
\t
     \t\t\tr  \t 
\t
     \t\t l\t\t  
\t
     \t\t  d\t  
\t
     \t    !\t
\t
  


"""


class WhitespaceTestCase(unittest.TestCase):
    """ Test whitespace frontend """
    def test_hello_world(self):
        src = hello_world_source
        print('src=', src.encode('ascii'))
        f = io.StringIO(src)
        ws2ir(f)

    @unittest.skip('todo')
    def test_error(self):
        src = ""
        with self.assertRaises(CompilerError):
            ws2ir(src)


if __name__ == '__main__':
    unittest.main()
