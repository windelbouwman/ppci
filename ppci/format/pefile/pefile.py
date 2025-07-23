from .headers import PeHeader


class PeFile:
    """Pe (exe) file"""

    def __init__(self):
        self.pe_header = PeHeader()


class ExeFile(PeFile):
    pass
