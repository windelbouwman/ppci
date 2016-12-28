"""
Cool idea to load actual object code into memory and execute it from python
using ctypes

Credits for idea: Luke Campagnola
"""

import sys
import platform
import io
import mmap
import ctypes
from ..api import c3c, link, get_arch
from ..binutils import debuginfo


def get_ctypes_type(debug_type):
    if isinstance(debug_type, debuginfo.DebugBaseType):
        mapping = {
            'int': ctypes.c_int,
            'void': ctypes.c_int,
            'double': ctypes.c_double
            }
        return mapping[debug_type.name]
    elif isinstance(debug_type, debuginfo.DebugPointerType):
        return ctypes.c_int
    raise NotImplementedError(str(debug_type) + str(type(debug_type)))


class WinPage:
    """ Nice windows hack to emulate mmap.

    Copied from:
    https://github.com/campagnola/pycca/blob/master/pycca/asm/codepage.py
    """
    def __init__(self, size):
        kern = ctypes.windll.kernel32
        valloc = kern.VirtualAlloc
        valloc.argtypes = (ctypes.c_uint32,) * 4
        valloc.restype = ctypes.c_uint32
        self.addr = valloc(0, size, 0x1000 | 0x2000, 0x40)
        self.ptr = 0
        self.size = size
        self.mem = (ctypes.c_char * size).from_address(self.addr)

    def write(self, data):
        self.mem[self.ptr:self.ptr+len(data)] = data
        self.ptr += len(data)

    def __len__(self):
        return self.size

    def __del__(self):
        kern = ctypes.windll.kernel32
        vfree = kern.VirtualFree
        vfree.argtypes = (ctypes.c_uint32,) * 3
        vfree(self.addr, self.size, 0x8000)


class Mod:
    """ Container for machine code """
    def __init__(self, obj):
        size = obj.byte_size

        # Create a code page into memory:
        if sys.platform == 'win32':
            self._page = WinPage(size)
            page_addr = self._page.addr
        else:
            self._page = mmap.mmap(-1, size, prot=1 | 2 | 4)
            buf = (ctypes.c_char * size).from_buffer(self._page)
            page_addr = ctypes.addressof(buf)

        # Load the code into the page:
        code = bytes(obj.get_section('code').data)
        self._page.write(code)

        # Get a function pointer
        for function in obj.debug_info.functions:
            function_name = function.name

            # Determine the function type:
            restype = get_ctypes_type(function.return_type)
            argtypes = [get_ctypes_type(a.typ) for a in function.arguments]
            ftype = ctypes.CFUNCTYPE(restype, *argtypes)

            # Create a function pointer:
            fpointer = ftype(page_addr + function.begin.offset)

            # Set the attribute:
            setattr(self, function_name, fpointer)


def platform_supported():
    """ Determine if this platform is supported """
    return get_current_arch() is not None


def get_current_arch():
    """ Determine the correct architecture based on the current machine """
    if sys.platform == 'linux' and platform.architecture()[0] == '64bit':
        march = get_arch('x86_64')
    # TODO: implement mac and windows support!
    # elif sys.platform == 'win32' and platform.architecture()[0] == '64bit':
    #    # windows 64 bit
    #    march = get_arch('x86_64:wincc')
    else:
        march = None
    return march


def load_code_as_module(source_file):
    """ Load c3 code as a module """

    # Compile a simple function
    march = get_current_arch()
    if march is None:
        raise NotImplementedError(sys.platform)

    obj1 = c3c([source_file], [], march, debug=True)
    # print(obj1)
    obj = link([obj1], debug=True)
    # print(obj)

    # Convert obj to executable module
    m = Mod(obj)
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
