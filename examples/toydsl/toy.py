from textx.metamodel import metamodel_from_file
from ppci import ir
from ppci.irutils import Verifier
from ppci import api


toy_mm = metamodel_from_file('toy.tx')


ir_module = ir.Module('toy')
ir_function = ir.Procedure('toy')
ir_module.add_function(ir_function)
ir_block = ir.Block('entry')
ir_function.entry = ir_block
ir_function.add_block(ir_block)


def handle_print(p):
    print('print!', p.var)


def handle_assignment(p):
    print('ass!', p.var, p.expr)


def handle_expression(expr):
    print('expr', expr)


def handle_sum(expr):
    print('sum', expr)


toy_mm.register_obj_processors({
    'PrintStatement': handle_print,
    'AssignmentStatement': handle_assignment,
    'Expression': handle_expression,
    'Sum': handle_sum,
    })

# Load the program:
program = toy_mm.model_from_file('example.tcf')

for statement in program.statements:
    print(statement)

ir_block.add_instruction(ir.Exit())

Verifier().verify(ir_module)
obj1 = api.ir_to_object([ir_module], 'x86_64')
obj = api.link([obj1])
print(obj)
with open('example.oj', 'w') as f:
    obj.save(f)
