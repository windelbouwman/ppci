

class AsmPrinter:
    """ Subclass this class to create render assembly code correctly """
    def print_instruction(self, instruction):
        return str(instruction)
