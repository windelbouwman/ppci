""" Read / write cmo files.
"""

import logging
from .io import FileReader
from .marshall import parse_header, read_value
from .bytefile import ByteCodeReader
from .code import load_code


logger = logging.getLogger("ocaml")


def read_file(filename):
    """ Read a cmo or bytecode file.
    """
    if isinstance(filename, str):
        logging.info("Processing %s", filename)
        with open(filename, "rb") as f:
            return read_file(f)
    else:
        f = filename
        if not f.seekable():
            raise ValueError("Can only read from seekable files")

        reader = CmoReader(f)
        if reader.is_cmo():
            logger.debug("File is cmo file")
            f.seek(0)
        else:
            logger.debug("File might be bytecode file")
            reader = ByteCodeReader(FileReader(f))
        return reader.read()


compilation_unit = (
    ("cu_name", "string"),
    ("cu_pos", "int"),
    ("cu_codesize", "int"),
    ("cu_reloc", "int"),
    ("cu_imports", "int"),
    ("cu_required_globals", "int"),
    ("cu_primitives", ("string", "list")),
    ("cu_force_link", "bool"),
    ("cu_debug", "int"),
    ("cu_debugsize", "int"),
)


class CmoReader:
    """ Reader for cmo (caml object) files.
    """

    MAGIC_V023 = "Caml1999O023"

    def __init__(self, f):
        self.reader = FileReader(f)

    def is_cmo(self):
        """ Determine if the current file is a cmo file by reading
        the magic marker.
        """
        try:
            self.read_magic()
        except ValueError:
            return False
        return True

    def read(self):
        self.read_magic()
        # self.read_code()
        offset = self.reader.read_u32()
        print(offset)
        self.reader.f.seek(offset)
        cu_unit = self.read_value(compilation_unit)
        print(cu_unit)
        cu_pos = cu_unit[1]
        cu_codesize = cu_unit[2]
        end_pos = cu_pos + cu_codesize
        assert end_pos <= offset
        if cu_codesize % 4 != 0:
            raise ValueError("codesize must be a multiple of 4")

        # Load code:
        self.reader.f.seek(cu_pos)
        code_data = self.reader.read_bytes(cu_codesize)
        return load_code(code_data)

    def read_magic(self):
        """ Read magic header """
        magic_len = len(self.MAGIC_V023)
        magic = self.reader.read_bytes(magic_len)
        magic = magic.decode("ascii")
        if magic != self.MAGIC_V023:
            raise ValueError("Unexpected magic value {}".format(magic))

    def read_value(self, typ):
        """ Read arbitrary ocaml object.

        An object is stored with a header first, then a marshalled object.
        """
        header = parse_header(self.reader)
        print(header)
        value = read_value(self.reader)
        assert len(value) == len(typ)
        for field, val in zip(typ, value):
            print(field, val)
        return value
