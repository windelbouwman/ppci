"""
Cool idea to load actual object code into memory and execute it from python
using ctypes

Credits for idea: Luke Campagnola
"""

import inspect
import sys
import mmap
import struct
import logging
import ctypes
from ..arch import get_current_arch
from .. import ir
from ..binutils import debuginfo, layout
from ..binutils.linker import link


def get_ctypes_type(debug_type):
    mapping = {
        'int': ctypes.c_int,
        'char': ctypes.c_int,  # TODO: how to handle this?
        'long': ctypes.c_long,
        'void': ctypes.c_int,  # TODO: what to do?
        'double': ctypes.c_double,
        'float': ctypes.c_float,
        'bool': ctypes.c_int,
        'byte': ctypes.c_int,
        }

    if isinstance(debug_type, debuginfo.DebugBaseType):
        return mapping[debug_type.name]
    elif isinstance(debug_type, debuginfo.DebugPointerType):
        if isinstance(debug_type.pointed_type, debuginfo.DebugStructType):
            # TODO: treat struct pointers as void pointers for now.
            # TODO: fix this?
            return ctypes.c_voidp
        else:
            return ctypes.POINTER(get_ctypes_type(debug_type.pointed_type))
    elif debug_type is None:
        return
    elif isinstance(debug_type, type):
        mapping = {
            int: ctypes.c_int,
            float: ctypes.c_double,
        }
        return mapping[debug_type]
    elif isinstance(debug_type, ir.BasicTyp):
        mapping = {
            ir.f32: ctypes.c_float,
            ir.f64: ctypes.c_double,
            ir.i32: ctypes.c_int32,
            ir.i64: ctypes.c_int64,  # TODO: which one of 32 and 64 is int?
        }
        return mapping[debug_type]
    else:  # pragma: no cover
        raise NotImplementedError(str(debug_type) + str(type(debug_type)))


uintt = ctypes.c_uint64 if struct.calcsize('P') == 8 else ctypes.c_uint32


class WinPage:
    """ Nice windows hack to emulate mmap.

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

    def write(self, data):
        self.mem[self.ptr:self.ptr+len(data)] = data
        self.ptr += len(data)

    def seek(self, pos):
        self.ptr = pos

    def read(self):
        return bytes(self.mem[self.ptr:self.size])

    def __len__(self):
        return self.size

    def __del__(self):
        kern = ctypes.windll.kernel32
        vfree = kern.VirtualFree
        vfree.argtypes = (uintt,) * 3
        vfree(self.addr, self.size, 0x8000)


logger = logging.getLogger('codepage')


class MemoryPage:
    """ Allocate a memory slab in the current process. """
    def __init__(self, size):
        self.size = size
        if size > 0:
            if sys.platform == 'win32':
                self._page = WinPage(size)
                self.addr = self._page.addr
            else:
                self._page = mmap.mmap(-1, size, prot=1 | 2 | 4)
                buf = (ctypes.c_char * size).from_buffer(self._page)
                self.addr = ctypes.addressof(buf)
            logger.debug('Allocated %s bytes at 0x%x', size, self.addr)
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


class Mod:
    """ Container for machine code """
    def __init__(self, obj, imports=None):
        size = obj.byte_size

        if not obj.debug_info:
            raise ValueError(
                'Unable to load "{}"'
                ' because it does not contain debug info.'.format(obj))

        # Create a code page into memory:
        self._code_page = MemoryPage(size)
        self._data_page = MemoryPage(size)

        # Create callback pointers if any:
        self._import_symbols = []
        if imports:
            for name, function in imports.items():
                signature = inspect.signature(function)
                if signature.return_annotation is inspect._empty:
                    raise ValueError(
                        '"{}" requires return type annotations'.format(name))
                return_type = signature.return_annotation
                argument_types = [
                    p.annotation for p in signature.parameters.values()]
                restype = get_ctypes_type(return_type)
                argtypes = [get_ctypes_type(a) for a in argument_types]
                ftype = ctypes.CFUNCTYPE(restype, *argtypes)
                cb = ftype(function)
                logger.debug('Import name %s', name)
                self._import_symbols.append((name, cb, ftype))

        # Link to e.g. apply offset to global literals
        layout2 = layout.Layout()
        layout_code_mem = layout.Memory('codepage')
        layout_code_mem.location = self._code_page.addr
        layout_code_mem.size = size
        layout_code_mem.add_input(layout.Section('code'))
        layout2.add_memory(layout_code_mem)
        layout_data_mem = layout.Memory('datapage')
        layout_data_mem.location = self._data_page.addr
        layout_data_mem.size = size
        layout_data_mem.add_input(layout.Section('data'))
        layout2.add_memory(layout_data_mem)

        # Link the object into memory:
        extra_symbols = {
            name: ctypes.cast(cb, ctypes.c_void_p).value
            for name, cb, _ in self._import_symbols}
        obj = link(
            [obj], layout=layout2, debug=True, extra_symbols=extra_symbols)
        assert obj.byte_size == size

        # Load the code into the page:
        code = bytes(obj.get_section('code').data)
        self._code_page.write(code)
        data = bytes(obj.get_section('data').data)
        self._data_page.write(data)
        # TODO: we might have more sections!

        # Get a function pointer
        for function in obj.debug_info.functions:
            function_name = function.name

            # Determine the function type:
            restype = get_ctypes_type(function.return_type)
            argtypes = [get_ctypes_type(a.typ) for a in function.arguments]
            logger.debug('function sig %s %s', restype, argtypes)
            ftype = ctypes.CFUNCTYPE(restype, *argtypes)

            # Create a function pointer:
            fpointer = ftype(self._code_page.addr + function.begin.offset)

            # Set the attribute:
            setattr(self, function_name, fpointer)

        # Get a variable pointers
        for variable in obj.debug_info.variables:
            variable_name = variable.name
            assert variable.address.section == 'data'
            vaddress = self._data_page.addr + variable.address.offset
            var_ctyp = ctypes.POINTER(get_ctypes_type(variable.typ))
            vpointer = ctypes.cast(vaddress, var_ctyp)

            # Set the attribute:
            setattr(self, variable_name, vpointer)

        # Store object for later usage:
        self._obj = obj

    def get_symbol_offset(self, name):
        """ Get the memory address of a symbol """
        return self._obj.get_symbol(name).value


def load_code_as_module(source_file, reporter=None):
    """ Load c3 code as a module """

    from ..api import c3c
    # Compile a simple function
    march = get_current_arch()
    if march is None:
        raise NotImplementedError(sys.platform)

    obj = c3c(
        [source_file], [], march, debug=True, opt_level=2, reporter=reporter)

    # Convert obj to executable module
    m = Mod(obj)
    return m


def load_obj(obj, imports=None):
    """ Load an object into memory.

    Args:
        obj: the code object to load.
        imports: A dictionary of functions to attach.

    Optionally a dictionary of functions that must be imported can
    be provided.
    """
    return Mod(obj, imports=imports)
