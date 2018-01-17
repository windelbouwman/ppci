from .headers import DosHeader, CoffHeader, PeOptionalHeader64
from .headers import ImageSectionHeader, PeHeader, DataDirectoryHeader
from .headers import ImportDirectoryTable


class PeFile:
    """ Pe (exe) file """
    def __init__(self):
        self.pe_header = PeHeader()


class ExeFile(PeFile):
    pass
