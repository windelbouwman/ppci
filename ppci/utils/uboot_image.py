""" Uboot image file format """

import time
import zlib
import enum
from .header import Header


IH_MAGIC = 0x27051956


class Compression(enum.Enum):
    """ Compression types """
    NONE = 0
    GZIP = 1
    BZIP2 = 2
    LZMA = 3
    LZO = 4
    LZ4 = 5


class OperatingSystem(enum.Enum):
    """ Operating system """
    INVALID = 0
    OPENBSD = 1
    NETBSD = 2
    FREEBSD = 3
    BSD4_4 = 4
    LINUX = 5


class Architecture(enum.Enum):
    """ Computer architecture """
    INVALID = 0
    ALPHA = 1
    ARM = 2
    I386 = 3
    IA64 = 4
    MIPS = 5
    MIPS64 = 6
    PPC = 7
    S390 = 8
    SH = 9
    SPARC = 10
    SPARC64 = 11
    M68K = 12
    NIOS = 13
    MICROBLAZE = 14
    NIOS2 = 15
    BLACKFIN = 16
    AVR32 = 17
    ST200 = 18
    SANDBOX = 19
    NDS32 = 20
    OPENRISC = 21
    ARM64 = 22
    ARC = 23
    X86_64 = 24
    XTENSA = 25


class ApplicationType(enum.Enum):
    """ Application type """
    INVALID = 0
    STANDALONE = 1
    KERNEL = 2


class ImageHeader(Header):
    _byte_order = '>'
    _fields = (
        ('ih_magic', 'I'),  # image header magic number
        ('ih_hcrc', 'I'),  # image header crc
        ('ih_time', 'I'),  # image creation
        ('ih_size', 'I'),  # image data size
        ('ih_load', 'I'),  # data load address
        ('ih_ep', 'I'),  # entry point address
        ('ih_dcrc', 'I'),  # data crc
        ('ih_os', 'B'),  # operating system
        ('ih_arch', 'B'),  # cpu architecture
        ('ih_type', 'B'),  # image type
        ('ih_comp', 'B'),  # compression type
        ('ih_name', '32s'),  # image name
    )


def crc32(data):
    return zlib.crc32(data)


def write_uboot_image(
        f, data: bytes, image_name='foobar', load_address=0x100,
        entry_point=0x100, os=OperatingSystem.INVALID,
        arch=Architecture.OPENRISC):
    """ Write uboot image to file """
    header = ImageHeader()
    header.ih_magic = IH_MAGIC
    header.ih_hcrc = 0  # Will be patched later!
    header.ih_time = int(time.time())
    header.ih_size = len(data)
    header.ih_load = load_address
    header.ih_ep = entry_point
    header.ih_dcrc = crc32(data)
    header.id_os = os.value
    header.id_arch = arch.value
    header.ih_type = ApplicationType.KERNEL.value
    header.ih_comp = Compression.NONE.value
    header.ih_name = image_name.encode('ascii')

    # Update header crc:
    header.ih_hcrc = crc32(header.serialize())

    # Write data to file:
    header.write(f)
    f.write(data)
