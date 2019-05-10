""" Handling of OCaml bytecode files ending with .byte extension. """

import logging
from .code import load_code
from .marshall import read_value


logger = logging.getLogger("ocaml")


class ByteCodeReader:
    """ Reader for bytecode files.
    """

    MAGIC_V023 = "Caml1999X023"

    def __init__(self, reader):
        self.reader = reader

    def read(self):
        num_sections = self.read_trailer()
        section_size = 8
        section_header_pos = -16 - num_sections * section_size
        self.reader.f.seek(section_header_pos, 2)
        sections = self.read_section_descriptions(num_sections)

        all_sections_size = sum(s[1] for s in sections)
        self.reader.f.seek(section_header_pos - all_sections_size, 2)
        return self.read_sections(sections)

    def read_sections(self, sections):
        fn_map = {
            "CODE": self.read_code_section,
            "DATA": self.process_data_section,
        }
        result = {}
        for name, length in sections:
            data = self.reader.read_bytes(length)
            if name in fn_map:
                logger.info("Processing: %s", name)
                value = fn_map[name](data)
                result[name] = value
            else:
                logger.error("TODO: %s", name)
        return result

    def read_trailer(self):
        """ Read magic header """
        self.reader.f.seek(-16, 2)
        num_sections = self.reader.read_u32()
        magic_len = len(self.MAGIC_V023)
        magic = self.reader.read_bytes(magic_len)
        magic = magic.decode("ascii")
        if magic != self.MAGIC_V023:
            raise ValueError("Unexpected magic value {}".format(magic))
        return num_sections

    def read_section_descriptions(self, num_sections):
        sections = []
        for _ in range(num_sections):
            name = self.reader.read_bytes(4).decode("ascii")
            length = self.reader.read_u32()
            logger.debug("section %s with %s bytes", name, length)
            sections.append((name, length))
        return sections

    def read_code_section(self, data):
        if len(data) % 4 != 0:
            raise ValueError("Code must be a multiple of 4 bytes")
        return load_code(data)

    def process_data_section(self, data):
        read_value(data)
