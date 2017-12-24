"""
The Program classes provide a high level interface for working with PPCI.
Each class represents one language / code representation. They have a
common API to get reporting, compile into other program representations,
and export to e.g. textual or binary representations.
"""

from .base import (
    get_program_classes, Program,
    SourceCodeProgram, IntermediateProgram, MachineProgram)
from .graph import (
    get_targets, get_program_graph, get_program_classes_by_group,
    get_program_classes_html)

# Import program classes into this namespace. We could let the Program meta
# class inject all classes into the namespace, but maybe we do not want
# every class to appear here, e.g. classes defined by users.

from .c3_program import C3Program
from .python_program import PythonProgram

from .ir_program import IrProgram
from .wasm_program import WasmProgram

from .x86_64_program import X86Program
from .arm_program import ArmProgram

__all__ = [
    'C3Program', 'PythonProgram',
    'IrProgram', 'WasmProgram',
    'X86Program', 'ArmProgram']
