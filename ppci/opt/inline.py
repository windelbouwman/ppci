from .. import ir


def inline_function(call: ir.ProcedureCall, function: ir.SubRoutine):
    """ Replace the call instruction with the function implementation """
    dst_function = call.function
    for block in function:
        block_copy = block.copy
        dst_function.add_block(block_copy)

    for value, parameter in zip(call.arguments, function.arguments):
        block
