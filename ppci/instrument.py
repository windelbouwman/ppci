
""" Functions to add instrumentation to IR code.
"""

import logging
from . import ir


def add_tracer(ir_module, trace_function_name='trace'):
    """ Instrument the given ir-module with a call tracer function """
    logger = logging.getLogger('instrument')
    trace_func = ir.ExternalProcedure(trace_function_name, [ir.ptr])
    ir_module.add_external(trace_func)
    logger.info('Add trace function to %s', ir_module)
    for function in ir_module.functions:
        # Create 0 terminated string of function name:
        name_literal = ir.LiteralData(function.name.encode('ascii') + bytes([0]), 'func_name')
        name_ptr = ir.AddressOf(name_literal, 'name_ptr')
        trace_call = ir.ProcedureCall(trace_func, [name_ptr])
        entry = function.entry
        entry.insert_instruction(trace_call)
        entry.insert_instruction(name_ptr)
        entry.insert_instruction(name_literal)

