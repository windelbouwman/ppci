
from ..header import Header


class DosHeader(Header):
    """ Representation of the dos header """
    _fields = (
        ('e_magic', 'H'),  # magic id 'MZ' (Mark Zbikowski)
        ('e_cblp', 'H'),  # bytes on last page
        ('e_cp', 'H'),  # pages in file, one page is 512 bytes
        ('e_crlc', 'H'),  # relocations
        ('e_cparhdr', 'H'),  # size of header in paragraphs
        ('e_minalloc', 'H'),  # mininum extra paragraphs of memory needed
        ('e_maxalloc', 'H'),  # maximum extra memory required, if not all
        ('e_ss', 'H'),  # initial ss value
        ('e_sp', 'H'),  # initial sp value
        ('e_csum', 'H'),  # Checksum
        ('e_ip', 'H'),  # initial ip value
        ('e_cs', 'H'),  # initial cs value
        ('e_lfarlc', 'H'),  # file address of relocation table
        ('e_ovno', 'H'),  # overlay number, 0 means main program
        (None, 'H'),  # 4 reserved words
        (None, 'H'),
        (None, 'H'),
        (None, 'H'),
        ('e_oemid', 'H'),
        ('e_oeminfo', 'H'),
        (None, 'H'),  # 10 reserved words
        (None, 'H'),
        (None, 'H'),
        (None, 'H'),
        (None, 'H'),
        (None, 'H'),
        (None, 'H'),
        (None, 'H'),
        (None, 'H'),
        (None, 'H'),
        ('e_lfanew', 'I'),  # file address of new exe header
    )

    def __init__(self):
        super().__init__()
        # one page is 512 bytes
        # one paragraph is 16 bytes
        self.e_magic = 0x5A4D  # magic id 'MZ' (Mark Zbikowski)
        self.e_cblp = 0   # bytes on last page
        self.e_cp = 0  # pages in file, one page is 512 bytes
        self.e_crlc = 0  # relocations
        self.e_cparhdr = 4  # size of header in paragraphs
        self.e_minalloc = 0  # mininum extra paragraphs of memory needed
        self.e_maxalloc = 0xffff  # maximum extra memory required, if not all
        self.e_ss = 0  # initial ss value
        self.e_sp = 0xb8  # initial sp value
        self.e_csum = 0  # Checksum
        self.e_ip = 0  # initial ip value
        self.e_cs = 0  # initial cs value
        self.e_lfarlc = 0  # file address of relocation table
        self.e_ovno = 0  # overlay number, 0 means main program
        self.e_oemid = 0
        self.e_oeminfo = 0
        self.e_lfanew = 0  # file address of new exe header

    def serialize(self):
        assert self.size == self.e_cparhdr * 16
        return super().serialize()


class PeHeader(Header):
    """ PE signature """
    def serialize(self):
        return 'PE\x00\x00'.encode('ascii')


class CoffHeader(Header):
    """ Coff header """
    _fields = (
        ('e_machine', 'H'),
        ('e_number_of_sections', 'H'),
        ('e_time_date_stamp', 'I'),
        ('e_pointer_to_symbol_table', 'I'),
        ('e_number_of_symbols', 'I'),
        ('e_size_of_optional_header', 'H'),
        ('e_characteristics', 'H'),
    )

    IMAGE_FILE_RELOCS_STRIPPED = 0x0001
    IMAGE_FILE_EXECUTABLE_IMAGE = 0x0002
    IMAGE_FILE_LINE_NUMS_STRIPPED = 0x0004
    IMAGE_FILE_LARGE_ADDRESS_AWARE = 0x0020

    IMAGE_FILE_MACHINE_I386 = 0x14c
    IMAGE_FILE_MACHINE_AMD64 = 0x8664
    IMAGE_FILE_MACHINE_ARM = 0x1c0
    IMAGE_FILE_MACHINE_RISCV32 = 0x5032
    IMAGE_FILE_MACHINE_RISCV64 = 0x5064


class PeOptionalHeader64(Header):
    """ Required optional header (64 bit variant) """
    _fields = (
        ('e_signature', 'H'),
        ('e_major_linker_version', 'B'),
        ('e_minor_linker_version', 'B'),
        ('e_size_of_code', 'I'),
        ('e_size_of_initialized_data', 'I'),
        ('e_size_of_uninitialized_data', 'I'),
        ('e_address_of_entry_point', 'I'),
        ('e_base_of_code', 'I'),
        ('e_image_base', 'Q'),
        ('e_section_alignment', 'I'),
        ('e_file_alignment', 'I'),
        ('e_major_os_version', 'H'),
        ('e_minor_os_version', 'H'),
        ('e_major_image_version', 'H'),
        ('e_minor_image_version', 'H'),
        ('e_major_subsystem_version', 'H'),
        ('e_minor_subsystem_version', 'H'),
        ('e_win32_version_value', 'I'),
        ('e_size_of_image', 'I'),
        ('e_size_of_headers', 'I'),
        ('e_checksum', 'I'),
        ('e_subsystem', 'H'),
        ('e_dll_characteristics', 'H'),
        ('e_size_of_stack_reserve', 'Q'),
        ('e_size_of_stack_commit', 'Q'),
        ('e_size_of_heap_reserve', 'Q'),
        ('e_size_of_heap_commit', 'Q'),
        ('e_loader_flags', 'I'),
        ('e_number_of_rva_and_sizes', 'I'),  # always 16
    )

    IMAGE_SUBSYSTEM_WINDOWS_CUI = 3

    def __init__(self):
        super().__init__()
        # Set some sensible defaults:
        self.e_number_of_rva_and_sizes = 16


class DataDirectoryHeader(Header):
    """ Single entry in the table after the optional header """
    _fields = (
        ('e_virtual_address', 'I'),
        ('e_size', 'I'),
    )


class ImportDirectoryTable(Header):
    _fields = (
        ('e_import_table_rva', 'I'),  # Previously known as characteristics
        ('e_time_date_stamp', 'I'),
        ('e_forward_chain', 'I'),
        ('e_name_rva', 'I'),
        ('e_import_address_table_rva', 'I'),
    )


class ImageSectionHeader(Header):
    _fields = (
        ('e_virtual_size', 'I'),
        ('e_virtual_address', 'I'),
        ('e_size_of_raw_data', 'I'),
        ('e_pointer_to_raw_data', 'I'),
        ('e_pointer_to_relocations', 'I'),
        ('e_pointer_to_line_numbers', 'I'),
        ('e_number_of_relocations', 'H'),
        ('e_number_of_line_numbers', 'H'),
        ('e_characteristics', 'I'),
    )

    IMAGE_SCN_CNT_CODE = 0x000000020
    IMAGE_SCN_CNT_INITIALIZED_DATA = 0x000000040
    IMAGE_SCN_MEM_EXECUTE = 0x20000000
    IMAGE_SCN_MEM_READ = 0x40000000
    IMAGE_SCN_MEM_WRITE = 0x80000000

    def __init__(self):
        super().__init__()
        self.e_name = ''

    def serialize(self):
        name = self.e_name.encode('utf-8')
        assert len(name) <= 8
        padding_count = 8 - len(name)
        padding = bytes([0] * padding_count)
        name = name + padding
        rest = super().serialize()
        return name + rest

    @classmethod
    def deserialize(cls, f):
        name = f.read(8)
        d = super(ImageSectionHeader, cls).deserialize(f)
        d.e_name = name
        return d
