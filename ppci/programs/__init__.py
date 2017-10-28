"""
The Program classes provide a high level interface for working with PPCI.
Each class represents one language / code representation. They have a
common API to get reporting, compile into other program representations,
and export to e.g. textual or binary representations.
"""

from .base import (get_program_classes, Program,
                   SourceCodeProgram, IntermediateProgram, MachineProgram)
from .graph import (get_targets, get_program_graph, get_program_classes_by_group,
                    get_program_classes_html)

# Import program classes into this namespace. We could let the Program meta
# class inject all classes into the namespace, but maybe we do not want
# every class to appear here, e.g. classes defined by users.

from ppci.lang.c3 import C3Program
from ppci.lang.python import PythonProgram

from ppci.irs.ir import IrProgram
from ppci.irs.wasm import WasmProgram

from ppci.arch.x86_64 import X86Program
from ppci.arch.arm import ArmProgram
