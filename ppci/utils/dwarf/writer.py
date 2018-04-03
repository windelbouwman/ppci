
# from .line import AdvanceLin

def emit_dwarf(debug_info, obj):
    """ Store debug information in dwarf format into the given object file """
    line_number_program = LineNumberProgram()
    data = line_number_program.encode()
    obj.add_section('debug_line', data)


class DwarfWriter:
    pass
