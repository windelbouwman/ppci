""" A callgraph is a graph of functions which call eachother.

"""

from .digraph import DiGraph, DiNode
from .. import ir


class CallGraph(DiGraph):
    pass


def mod_to_call_graph(ir_module) -> CallGraph:
    """ Create a call graph for an ir-module """
    cg = CallGraph()

    # Create call graph nodes:
    node_map = {}
    for routine in ir_module.functions:
        node_map[routine] = DiNode(cg)
    for routine in ir_module.externals:
        if isinstance(routine, ir.ExternalSubRoutine):
            node_map[routine] = DiNode(cg)

    # Add call graph edges:
    for routine in ir_module.functions:
        n1 = node_map[routine]
        for instruction in routine.get_instructions():
            if isinstance(instruction, (ir.FunctionCall, ir.ProcedureCall)):
                routine2 = instruction.callee
                n2 = node_map[routine2]
                cg.add_edge(n1, n2)

    return cg
