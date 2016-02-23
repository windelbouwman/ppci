"""
    Tool that randomly generates code and feeds it through the code generator.
"""

from ppci.api import ir_to_object, fix_target
from ppci import ir
from ppci.irutils import Builder


def go():
    builder = Builder()
    module = ir.Module('fuzz')
    builder.module = module
    function = builder.new_function('buzz')
    builder.set_function(function)
    first_block = builder.new_block()
    builder.emit(ir.Jump(first_block))
    builder.set_block(first_block)
    builder.emit(ir.Jump(function.epilog))

    arch = fix_target('arm')
    obj = ir_to_object([module], arch)
    print(obj)

go()
