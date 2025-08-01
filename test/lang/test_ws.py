import unittest
import io
from ppci.api import ws_to_ir
from ppci.common import CompilerError

# Prevent error from flake, since this is whitespace language:
# flake8: noqa: W291, W293

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
    """Test whitespace frontend"""

    def test_hello_world(self):
        src = hello_world_source
        print("src=", src.encode("ascii"))
        f = io.StringIO(src)
        ws_to_ir(f)

    @unittest.skip("todo")
    def test_error(self):
        src = ""
        with self.assertRaises(CompilerError):
            ws_to_ir(src)


if __name__ == "__main__":
    unittest.main()
