"""
Cool idea to load actual object code into memory and execute it from python
using ctypes

Credits for idea: Luke Campagnola
"""

import io, mmap, ctypes
from ppci.api import c3c, link


class Mod:
    """ Container for machine code """
    def __init__(self, obj):
        size = obj.byte_size
        self._page = page = mmap.mmap(-1, size, prot=1 | 2 | 4)

        buf = (ctypes.c_char * size).from_buffer(self._page)
        page_addr = ctypes.addressof(buf)
        code = obj.get_section('code').data
        page.write(code)

        # Get a function pointer
        for function in obj.debug_info.functions:
            function_name = function.name

            # TODO: do not assume int, int int types here:
            ftype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int)
            f = ftype(page_addr + function.begin.offset)
            setattr(self, function_name, f)


def load_code_as_module(source_file):
    """ Load c3 code as a module """

    # Compile a simple function
    obj1 = c3c([source_file], [], 'x86_64', debug=True)
    # obj = link([obj1])

    # Convert obj to executable module
    m = Mod(obj1)
    return m


if __name__ == '__main__':
    source_file = io.StringIO("""
          module main;
          function int add(int a, int b) {
            return a + b;
          }

          function int sub(int a, int b) {
            return a - b;
          }
        """)
    m = load_code_as_module(source_file)

    # Cross fingers
    print(m.add(1, 2))
    print(m.sub(10, 2))
