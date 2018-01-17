""" Implements the exe file format used by windows.

See also:

https://msdn.microsoft.com/en-us/library/windows/desktop/ms680547(v=vs.85).aspx

Another excellent effort: https://github.com/erocarrera/pefile

"""

import io
import struct
import time
from .. import __version_info__
from ..binutils import layout
from ..binutils import linker
from ..binutils.objectfile import ObjectFile
from .pefile.pefile import ExeFile
from .pefile.headers import DosHeader, CoffHeader, PeOptionalHeader64
from .pefile.headers import ImageSectionHeader, PeHeader, DataDirectoryHeader
from .pefile.headers import ImportDirectoryTable


def write_dos_stub(f):
    """ Write dos stub to file. This stub prints to stdout:
        'this program cannot be run in dos mode'
    """
    code = bytearray([
        0x0e,              # push cs
        0x1f,              # pop ds
        0xba, 0xe, 0x0,    # mov dx, message
        0xb4, 0x09,        # mov ah, 09
        0xcd, 0x21,        # int 0x21
        0xb8, 0x01, 0x4c,  # mov ax, 0x4c01
        0xcd, 0x21,        # int 0x21
    ])

    # TODO: it is nice to have this l33t-code here, but it would also be
    # awesome to invoke the ppci machinery here!
    # asm_src = """
    # push cs
    # pop ds
    # mov dx, message
    # mov ah, 9
    # int 0x21
    # mov ax, 0x4c01
    # int 0x21
    # """
    # from ..api import asm
    # asm(asm_src)
    message = 'This program can certainly not be run in DOS :-)'
    code += message.encode('ascii')
    code += bytes([0xd, 0xd, 0xa, ord('$')])
    f.write(code)


def roundup(value, multiple):
    remaining = value % multiple
    if remaining:
        return value - remaining + multiple
    else:
        return value


def align(f, alignment, padding_value=0):
    """ Pad with 0 bytes until certain alignment is met """
    x = f.tell() % alignment
    if x > 0:
        pad_count = alignment - x
        padding = bytes([0] * pad_count)
        f.write(padding)


def read_exe(f):
    """ Process an exe file """
    dos_header = DosHeader.deserialize(f)
    print(dos_header)
    print('Dos header:')
    dos_header.print()
    print()
    if dos_header.e_lfanew:
        f.seek(dos_header.e_lfanew)
        sig = f.read(4)
        print(sig)
        assert sig == b'PE\x00\x00'
        coff_header = CoffHeader.deserialize(f)
        print('### Coff header:')
        coff_header.print()
        print()
        pe_optional_header = PeOptionalHeader64.deserialize(f)
        print('### Optional header:')
        pe_optional_header.print()
        print()

        print('### Data directory headers:')
        data_directories = []
        for i in range(16):
            ddh = DataDirectoryHeader.deserialize(f)
            data_directories.append(ddh)
            print('directory {}'.format(i))
            ddh.print()
        print()

        print('### Section headers:')
        section_headers = []
        for i in range(coff_header.e_number_of_sections):
            ish = ImageSectionHeader.deserialize(f)
            section_headers.append(ish)
            print('Section {} {}'.format(i, ish.e_name))
            ish.print()
            print()

        print()
        print(f.tell())

        # Load sections:
        section_map = {}
        for ish in section_headers:
            f.seek(ish.e_pointer_to_raw_data)
            data = f.read(ish.e_size_of_raw_data)
            section_map[ish.e_virtual_address] = data

        # Analyze data directories:
        for i, ddh in enumerate(data_directories):
            if i == 1 and ddh.e_size > 0:
                # Import table
                f2 = io.BytesIO(section_map[ddh.e_virtual_address])
                # f.seek(ddh.e_virtual_address)
                # d = f.read(20)
                import_tables = []
                while True:
                    idt = ImportDirectoryTable.deserialize(f2)
                    if idt.is_null():
                        break
                    import_tables.append(idt)

                for idt in import_tables:
                    f2.seek(idt.e_name_rva - ddh.e_virtual_address)
                    dll_name = f2.read(20)  # TODO: 0 terminated?
                    print(dll_name)
                    f2.seek(idt.e_import_table_rva)
                    # while True:
                    #    Import
                    idt.print()
                    print()


class ExeWriter:
    def create_import_table(self, imports, import_rva=0x0):
        """ Create import table from a dictionary of lists.

        An import table is:
        - a null terminated list of dll files to import
        - N times a null terminated list of functions to import
        - a list of strings
        - A list of function pointers which must be filled by the loader.
        """

        # TODO: We might as well return a relocateable object!
        obj = ObjectFile(self.arch)
        import_section = obj.get_section('import', create=True)
        f = io.BytesIO()
        dll_names = sorted(imports.keys())

        # First fill in ascii values of imported values:
        size_of_dir = 20 * (len(dll_names) + 1)
        size_of_imports = sum(8 * (len(imports[n]) + 1) for n in imports)
        size_of_headers = size_of_dir + 2 * size_of_imports

        # Create names and ordinal tables:
        f.seek(size_of_headers)
        names = {}
        ordinals = {}
        for dll_name in dll_names:
            names[dll_name] = import_rva + f.tell()
            f.write(self.padded_encode(dll_name))
            for symbol_name in imports[dll_name]:
                ordinals[symbol_name] = import_rva + f.tell()
                f.write(bytes([0, 0]))
                f.write(self.padded_encode(symbol_name))

        # Create directory:
        idts = []
        for dll_name in dll_names:
            idt = ImportDirectoryTable()
            idt.e_name_rva = names[dll_name]
            idts.append(idt)

        # End with a null entry:
        sentinel = ImportDirectoryTable()
        idts.append(sentinel)

        f.seek(size_of_dir)
        # Create function import table:
        for dll_name, idt in zip(dll_names, idts):
            idt.e_import_table_rva = f.tell() + import_rva
            for symbol_name in imports[dll_name]:
                f.write(struct.pack('<Q', ordinals[symbol_name]))

            # Trailing sentinel:
            f.write(struct.pack('<Q', 0))

        # TODO: use address map to fixup imported calls.
        address_map = {}
        obj.add_symbol('_iat_begin', f.tell(), 'import')

        # Create thunk table:
        for dll_name, idt in zip(dll_names, idts):
            idt.e_import_address_table_rva = f.tell() + import_rva
            for symbol_name in imports[dll_name]:
                obj.add_symbol(
                    'imp_{}'.format(symbol_name), f.tell(), 'import')
                address_map[symbol_name] = f.tell() + import_rva
                f.write(struct.pack('<Q', ordinals[symbol_name]))

            # Trailing sentinel:
            # TODO: does the thunk table need a null terminator at the end?
            f.write(struct.pack('<Q', 0))
        obj.add_symbol('_iat_end', f.tell(), 'import')
        assert f.tell() == size_of_headers

        # Write out the import directory:
        f.seek(0)
        for idt in idts:
            f.write(idt.serialize())
        assert f.tell() == size_of_dir
        data = f.getvalue()
        import_section.add_data(data)
        return obj

    @staticmethod
    def padded_encode(txt):
        data = txt.encode('ascii') + bytes([0])
        if len(data) % 2 == 1:
            return data + bytes([0])
        else:
            return data

    def write(self, obj, f, entry='_main'):
        """ Write object to exe file """
        imports = {
            'KERNEL32.dll': [
                'ExitProcess',
                'Sleep',
                'GetStdHandle',
                'WriteFile',
            ],
        }
        self.arch = obj.arch
        import_obj = self.create_import_table(imports)

        e = ExeFile()

        # Link object at right position:
        base_address = 0x00400000
        l = layout.Layout()
        m = layout.Memory('code')
        m.size = 0x100000
        m.location = base_address + 0x1000
        l.add_memory(m)
        m.add_input(layout.Section('code'))
        m.add_input(layout.Align(4096))
        m.add_input(layout.Section('data'))
        m.add_input(layout.Align(4096))
        m.add_input(layout.Section('import'))
        obj = linker.link([obj, import_obj], layout=l)

        dos_header = DosHeader()
        dos_header.write(f)
        write_dos_stub(f)
        align(f, 8)
        pe_header_address = f.tell()
        assert pe_header_address % 8 == 0
        dos_header.e_lfanew = pe_header_address   # Link to new PE header:

        # Re-create import table at proper address:
        import_section = obj.get_section('import')
        import_rva = import_section.address - base_address
        import_obj2 = self.create_import_table(imports, import_rva=import_rva)
        idata = import_obj2.get_section('import').data

        e.pe_header.write(f)

        # Generate the headers:
        coff_header = CoffHeader()
        pe_optional_header = PeOptionalHeader64()
        data_directory = []
        for i in range(16):
            d = DataDirectoryHeader()
            if i == 1:
                import_section = obj.get_section('import')
                if idata:
                    d.e_virtual_address = \
                        import_section.address - base_address
                    d.e_size = len(idata)
            elif i == 12:
                d.e_virtual_address = \
                    obj.get_symbol_value('_iat_begin') - base_address
                d.e_size = \
                    obj.get_symbol_value('_iat_end') - base_address \
                    - d.e_virtual_address

            data_directory.append(d)

        # Write coff header:
        machine_types = {
            'i386': CoffHeader.IMAGE_FILE_MACHINE_I386,
            'x86_64': CoffHeader.IMAGE_FILE_MACHINE_AMD64,
            'riscv': CoffHeader.IMAGE_FILE_MACHINE_RISCV32,
        }
        coff_header.e_machine = machine_types[obj.arch.name]
        coff_header.e_time_date_stamp = int(time.time())
        coff_header.e_size_of_optional_header = \
            pe_optional_header.size + sum(d.size for d in data_directory)
        # This file is an image
        coff_header.e_characteristics = \
            CoffHeader.IMAGE_FILE_RELOCS_STRIPPED | \
            CoffHeader.IMAGE_FILE_EXECUTABLE_IMAGE | \
            CoffHeader.IMAGE_FILE_LINE_NUMS_STRIPPED | \
            CoffHeader.IMAGE_FILE_LARGE_ADDRESS_AWARE
        coff_header_location = f.tell()
        coff_header.write(f)

        # Get sections:
        code_section = obj.get_section('code')
        code_bytes = code_section.data

        data_section = obj.get_section('data')
        data_bytes = data_section.data

        # Fill pe optional header:
        pe_optional_header.e_signature = 0x20b  # pe32+
        pe_optional_header.e_major_linker_version = __version_info__[0]
        pe_optional_header.e_minor_linker_version = __version_info__[1]
        pe_optional_header.e_size_of_code = len(code_bytes)
        pe_optional_header.e_size_of_initialized_data = len(data_bytes)
        pe_optional_header.e_size_of_uninitialized_data = 0
        pe_optional_header.e_address_of_entry_point = \
            obj.get_symbol_value(entry) - base_address
        pe_optional_header.e_base_of_code = code_section.address - base_address
        pe_optional_header.e_image_base = base_address
        pe_optional_header.e_section_alignment = 0x1000  # 4096
        pe_optional_header.e_file_alignment = 512
        pe_optional_header.e_major_os_version = 4
        pe_optional_header.e_minor_os_version = 0
        pe_optional_header.e_major_subsystem_version = 5
        pe_optional_header.e_minor_subsystem_version = 2
        pe_optional_header.e_subsystem = \
            PeOptionalHeader64.IMAGE_SUBSYSTEM_WINDOWS_CUI
        pe_optional_header.e_size_of_stack_reserve = 0x200000
        pe_optional_header.e_size_of_stack_commit = 0x1000
        pe_optional_header.e_size_of_heap_reserve = 0x100000
        pe_optional_header.e_size_of_heap_commit = 0x1000

        pe_optional_header.e_number_of_rva_and_sizes = 16
        pe_optional_header.write(f)

        # Write data directory:
        for d in data_directory:
            d.write(f)

        # Determine amount of functions
        coff_header.e_number_of_sections = 3

        coff_section_headers = []
        section_headers_location = f.tell()

        # Write text section header:
        code_section_header = ImageSectionHeader()
        code_section_header.e_name = '.text'
        code_section_header.e_virtual_address = \
            code_section.address - base_address
        code_section_header.e_characteristics = \
            ImageSectionHeader.IMAGE_SCN_MEM_EXECUTE | \
            ImageSectionHeader.IMAGE_SCN_MEM_READ | \
            ImageSectionHeader.IMAGE_SCN_CNT_CODE
        code_section_header.write(f)
        coff_section_headers.append(code_section_header)

        # Write data section header:
        data_section_header = ImageSectionHeader()
        data_section_header.e_name = '.data'
        data_section_header.e_virtual_address = \
            data_section.address - base_address
        data_section_header.e_characteristics = \
            ImageSectionHeader.IMAGE_SCN_MEM_WRITE | \
            ImageSectionHeader.IMAGE_SCN_MEM_READ | \
            ImageSectionHeader.IMAGE_SCN_CNT_INITIALIZED_DATA
        data_section_header.write(f)
        coff_section_headers.append(data_section_header)

        # Write import section header:
        import_section_header = ImageSectionHeader()
        import_section_header.e_name = '.idata'
        data_section_header.e_virtual_address = \
            import_section.address - base_address
        import_section_header.e_characteristics = \
            ImageSectionHeader.IMAGE_SCN_MEM_WRITE | \
            ImageSectionHeader.IMAGE_SCN_MEM_READ | \
            ImageSectionHeader.IMAGE_SCN_CNT_INITIALIZED_DATA
        import_section_header.write(f)
        coff_section_headers.append(import_section_header)

        # Update header sizes:
        header_size = roundup(f.tell(), pe_optional_header.e_file_alignment)
        pe_optional_header.e_size_of_headers = header_size

        # Fill image size:
        last_address = import_section.address + import_section.size
        image_size = roundup(last_address - base_address, 4096)
        pe_optional_header.e_size_of_image = image_size

        # Write code contents:
        align(f, 512)
        code_section_header.e_virtual_size = code_section.size
        code_section_header.e_virtual_address = \
            code_section.address - base_address
        code_section_header.e_pointer_to_raw_data = f.tell()
        f.write(code_bytes)
        align(f, 512)
        code_section_header.e_size_of_raw_data = \
            f.tell() - code_section_header.e_pointer_to_raw_data

        # Write data contents:
        align(f, 512)
        data_section_header.e_pointer_to_raw_data = f.tell()
        data_section_header.e_virtual_size = data_section.size
        data_section_header.e_virtual_address = \
            data_section.address - base_address
        f.write(data_bytes)
        align(f, 512)
        data_section_header.e_size_of_raw_data = \
            f.tell() - data_section_header.e_pointer_to_raw_data

        # Write .idata contents:
        align(f, 512)
        import_section_header.e_pointer_to_raw_data = f.tell()
        import_section_header.e_virtual_size = len(idata)
        import_section_header.e_virtual_address = \
            import_section.address - base_address
        f.write(idata)
        align(f, 512)
        import_section_header.e_size_of_raw_data = \
            f.tell() - import_section_header.e_pointer_to_raw_data

        # Write dos header again:
        f.seek(0)
        dos_header.write(f)

        # Write coff header again:
        f.seek(coff_header_location)
        coff_header.write(f)
        pe_optional_header.write(f)

        # Rewrite section headers:
        f.seek(section_headers_location)
        for section_header in coff_section_headers:
            section_header.write(f)
