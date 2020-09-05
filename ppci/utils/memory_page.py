import logging
import sys
import ctypes
import struct
import mmap


logger = logging.getLogger("mempage")


class MemoryPage:
    """ Allocate a memory slab in the current process. """

    def __init__(self, size):
        self.size = size
        if size > 0:
            if sys.platform == "win32":
                self._page = WinPage(size)
                self.addr = self._page.addr
            else:
                self._page = mmap.mmap(-1, size, prot=1 | 2 | 4)
                buf = (ctypes.c_char * size).from_buffer(self._page)
                self.addr = ctypes.addressof(buf)
            logger.debug("Allocated %s bytes at 0x%x", size, self.addr)
        else:
            self._page = None
            self.addr = 0

    def write(self, data):
        """ Fill page with the given data """
        if data:
            assert self._page
            self._page.write(data)

    def seek(self, pos):
        if self._page:
            self._page.seek(pos)

    def read(self, size=None):
        if self._page:
            return self._page.read(size)
        else:
            return bytes()


uintt = ctypes.c_uint64 if struct.calcsize("P") == 8 else ctypes.c_uint32


class WinPage:
    """Nice windows hack to emulate mmap.

    Copied from:
    https://github.com/campagnola/pycca/blob/master/pycca/asm/codepage.py
    """

    def __init__(self, size):
        kern = ctypes.windll.kernel32
        valloc = kern.VirtualAlloc
        valloc.argtypes = (uintt,) * 4
        valloc.restype = uintt
        self.addr = valloc(0, size, 0x1000 | 0x2000, 0x40)
        self.ptr = 0
        self.size = size
        self.mem = (ctypes.c_char * size).from_address(self.addr)

    def write(self, data: bytes):
        self.mem[self.ptr : self.ptr + len(data)] = data
        self.ptr += len(data)

    def seek(self, pos):
        self.ptr = pos

    def read(self, size) -> bytes:
        data = bytes(self.mem[self.ptr : self.ptr + size])
        self.ptr += size
        return data

    def __len__(self):
        return self.size

    def __del__(self):
        kern = ctypes.windll.kernel32
        vfree = kern.VirtualFree
        vfree.argtypes = (uintt,) * 3
        vfree(self.addr, self.size, 0x8000)
