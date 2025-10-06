from ppci.binutils import deserialise
from elf.reader import elf_to_object
from io import FormatError
import json


def load_object_file(file):
    """
    this function converts any supported
    object file format into an instance of ObjectFile.
    The object file should be opened in binary mode.
    """
    start = file.read(4)
    file.seek(0)
    if b"ELF" in start:
        # read elf
        return elf_to_object(file)
    else:
        # assume an json file
        data = file.read().decode()
        if data.isprintable():
            return deserialise(json.loads(data))
        else:
            # Ok not a json file
            raise FormatError("file format not recognised")
