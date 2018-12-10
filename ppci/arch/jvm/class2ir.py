import logging
from .io import load_code
from ...irutils import Builder
from ... import ir


logger = logging.getLogger('jvm2ir')


def class_to_ir(class_file):
    """ Translate java class file into IR-code. """
    generator = Generator()
    generator.initialize()
    generator.gen_class(class_file)
    return generator.get_result()


class Generator:
    def __init__(self):
        self._builder = Builder()

    def initialize(self):
        module = ir.Module('java')
        self._builder.set_module(module)

    def emit(self, instr):
        return self._builder.emit(instr)

    def get_result(self):
        return self._builder.module

    def gen_class(self, class_file):
        logger.warning('java class file code generate is work in progress')
        for method in class_file.methods:
            method_name = class_file.get_name(method.name_index)
            logger.info('processing method %s', method_name)

            ir_func = self._builder.new_procedure(method_name)
            self._builder.set_function(ir_func)

            for attribute in method.attributes:
                attrib_name = class_file.get_name(attribute.name_index)
                if attrib_name == 'Code':
                    # Now we found bytecode.
                    code = load_code(attribute.data)
                    print(code)

                    first_block = self._builder.new_block()
                    self._builder.set_block(first_block)
                    ir_func.entry = first_block

                    self.local_variables = []
                    for index in range(code.max_locals):
                        var = self.emit(
                            ir.Const(0, 'z_{}'.format(index), ir.i32))
                        self.local_variables.append(var)

                    self.stack = []
                    for instruction in code.code:
                        self.gen_instr(instruction)
                else:
                    logger.warning('Unhandled attribute: %s', attrib_name)

            self.emit(ir.Exit())

    def gen_instr(self, instruction):
        """ Generate ir-code for a single instruction. """
        logger.debug('processing opcode 0x%X', instruction)
        opcode = instruction
        if instruction == 0x60:  # Add
            v1 = self.stack.pop()
            v2 = self.stack.pop()
            result = self.emit(ir.add(v1, v2, 'add', ir.i32))
            self.stack.append(result)
        elif instruction == 0x1a:
            v = self.local_variables[0]
            self.stack.append(v)
        elif instruction == 0x1b:
            v = self.local_variables[1]
            self.stack.append(v)
        elif instruction == 0x4:  # int 1
            value = self.emit(ir.Const(1, 'x', ir.i32))
            self.stack.append(value)
        else:
            logger.warning('todo: 0x%X', opcode)
            # raise NotImplementedError(str(hex(instruction)))
