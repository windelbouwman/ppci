"""
Cool idea to load actual object code into memory and execute it from python
using ctypes

Credits for idea: Luke Campagnola
"""

import inspect
import sys
import logging
import ctypes
from ..arch import get_current_arch
from .. import ir
from ..binutils import debuginfo, layout
from ..binutils.linker import link
from .memory_page import MemoryPage


logger = logging.getLogger("codepage")


debug_type_name_mapping = {
    "int": ctypes.c_int,
    "char": ctypes.c_int,  # TODO: how to handle this?
    "long": ctypes.c_long,
    "int8_t": ctypes.c_int8,
    "int16_t": ctypes.c_int16,
    "int32_t": ctypes.c_int32,
    "int64_t": ctypes.c_int64,
    "uint8_t": ctypes.c_uint8,
    "uint16_t": ctypes.c_uint16,
    "uint32_t": ctypes.c_uint32,
    "uint64_t": ctypes.c_uint64,
    "void": ctypes.c_int,  # TODO: what to do?
    "double": ctypes.c_double,
    "float": ctypes.c_float,
    "bool": ctypes.c_int,
    "byte": ctypes.c_int,
}


def get_ctypes_type(debug_type):
    if isinstance(debug_type, debuginfo.DebugBaseType):
        return debug_type_name_mapping[debug_type.name]
    elif isinstance(debug_type, debuginfo.DebugPointerType):
        if isinstance(debug_type.pointed_type, debuginfo.DebugStructType):
            # TODO: treat struct pointers as void pointers for now.
            # TODO: fix this?
            return ctypes.c_voidp
        else:
            return ctypes.POINTER(get_ctypes_type(debug_type.pointed_type))
    elif isinstance(debug_type, debuginfo.DebugArrayType):
        element_type = get_ctypes_type(debug_type.element_type)
        return ctypes.ARRAY(element_type, debug_type.size)
    elif debug_type is None:
        return
    elif isinstance(debug_type, type):
        mapping = {int: ctypes.c_int, float: ctypes.c_double}
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


class Mod:
    """ Container for machine code """

    def __init__(self, obj, imports=None):
        code_size = obj.get_section("code").size
        data_size = obj.get_section("data").size

        if not obj.debug_info:
            raise ValueError(
                'Unable to load "{}"'
                " because it does not contain debug info.".format(obj)
            )

        # Create a code page into memory:
        self._code_page = MemoryPage(code_size)
        self._data_page = MemoryPage(data_size)

        # Create callback pointers if any:
        imports = imports or {}

        # Store reference on self to keep reference to object:
        self._import_symbols = []

        extra_symbols = {}
        for name, imp_obj in imports.items():
            if callable(imp_obj):
                signature = inspect.signature(imp_obj)
                if signature.return_annotation is inspect._empty:
                    raise ValueError(
                        '"{}" requires return type annotations'.format(name)
                    )
                return_type = signature.return_annotation
                argument_types = [
                    p.annotation for p in signature.parameters.values()
                ]
                restype = get_ctypes_type(return_type)
                argtypes = [get_ctypes_type(a) for a in argument_types]
                ftype = ctypes.CFUNCTYPE(restype, *argtypes)
                # print('f type', name, ftype, restype, argtypes)
                callback = ftype(imp_obj)
                logger.debug("Import name %s", name)
                self._import_symbols.append((name, callback, ftype))
                extra_symbols[name] = ctypes.cast(
                    callback, ctypes.c_void_p
                ).value
            elif isinstance(imp_obj, MemoryPage):
                self._import_symbols.append((name, imp_obj))
                extra_symbols[name] = imp_obj.addr
            else:
                raise ValueError(
                    "Cannot import {} of type {}".format(name, type(imp_obj))
                )

        # Link to e.g. apply offset to global literals
        memory_layout = layout.Layout()
        layout_code_mem = layout.Memory("codepage")
        layout_code_mem.location = self._code_page.addr
        layout_code_mem.size = code_size
        layout_code_mem.add_input(layout.Section("code"))
        memory_layout.add_memory(layout_code_mem)
        layout_data_mem = layout.Memory("datapage")
        layout_data_mem.location = self._data_page.addr
        layout_data_mem.size = data_size
        layout_data_mem.add_input(layout.Section("data"))
        memory_layout.add_memory(layout_data_mem)

        # Link the object into memory:
        obj = link(
            [obj],
            layout=memory_layout,
            debug=True,
            extra_symbols=extra_symbols,
        )

        # Load the code into the page:
        code = bytes(obj.get_section("code").data)
        assert len(code) <= code_size
        self._code_page.write(code)

        data = bytes(obj.get_section("data").data)
        assert len(data) <= data_size
        self._data_page.write(data)

        # TODO: we might have more sections!

        # Get a function pointer
        for function in obj.debug_info.functions:
            function_name = function.name

            # Determine the function type:
            restype = get_ctypes_type(function.return_type)
            argtypes = [get_ctypes_type(a.typ) for a in function.arguments]
            logger.debug("function sig %s %s", restype, argtypes)
            ftype = ctypes.CFUNCTYPE(restype, *argtypes)

            # Create a function pointer:
            vaddress = obj.get_symbol_id_value(function.begin.symbol_id)
            fpointer = ftype(vaddress)

            # Set the attribute:
            setattr(self, function_name, fpointer)

        # Get a variable pointers
        for variable in obj.debug_info.variables:
            variable_name = variable.name
            assert isinstance(variable, debuginfo.DebugVariable)
            assert isinstance(variable.address, debuginfo.DebugAddress)
            vaddress = obj.get_symbol_id_value(variable.address.symbol_id)
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
        [source_file], [], march, debug=True, opt_level=2, reporter=reporter
    )

    # Convert obj to executable module
    m = Mod(obj)
    return m


def load_obj(obj, imports=None):
    """Load an object into memory.

    Args:
        obj: the code object to load.
        imports: A dictionary of functions to attach.

    Optionally a dictionary of functions that must be imported can
    be provided.
    """
    return Mod(obj, imports=imports)
