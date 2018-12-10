import logging
from .io import load_code, parse_method_descriptor
from .io import BaseType
from ...binutils import debuginfo
from ...common import SourceLocation
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
        self.stack = None
        self.local_variables = None
        self.class_file = None

    def initialize(self):
        self.debug_db = debuginfo.DebugDb()
        module = ir.Module('java', debug_db=self.debug_db)
        self._builder.set_module(module)

    def emit(self, instr):
        return self._builder.emit(instr)

    def get_ir_type(self, typ):
        if isinstance(typ, BaseType):
            mp = {
                'B': ir.i8,
                'S': ir.i16,
                'I': ir.i32,
                'F': ir.f32,
                'D': ir.f64,
            }
            return mp[typ.typ]
        else:  # pragma: no cover
            raise NotImplementedError(str(typ))

    def get_debug_type(self, typ):
        if self.debug_db.contains(typ):
            return self.debug_db.get(typ)
        else:
            if isinstance(typ, BaseType):
                dbg_type_map = {
                    'F': debuginfo.DebugBaseType('float', 4, 1),
                    'D': debuginfo.DebugBaseType('double', 8, 1),
                    'I': debuginfo.DebugBaseType('int', 4, 1),
                    'J': debuginfo.DebugBaseType('long', 8, 1),
                    'V': debuginfo.DebugBaseType('void', 0, 1),
                }
                dbg_typ = dbg_type_map[typ.typ]
                self.debug_db.enter(typ, dbg_typ)
                return dbg_typ
            else:  # pragma: no cover
                raise NotImplementedError(str(typ))

    def get_result(self):
        return self._builder.module

    def gen_class(self, class_file):
        logger.warning('java class file code generate is work in progress')
        self.class_file = class_file
        for method in class_file.methods:
            self.gen_method(method)

    def gen_method(self, method):
        method_name = self.class_file.get_name(method.name_index)
        logger.info(
            'processing method %s access=%X',
            method_name, method.access_flags
        )

        descriptor = self.class_file.get_name(method.descriptor_index)
        logger.debug('Descriptor: %s', descriptor)
        signature = parse_method_descriptor(descriptor)

        # Construct valid function:
        if signature.return_type:
            ir_typ = self.get_ir_type(signature.return_type)
            ir_func = self._builder.new_function(method_name, ir_typ)
            dbg_return_type = self.get_debug_type(signature.return_type)
        else:
            ir_func = self._builder.new_procedure(method_name)
            dbg_return_type = debuginfo.DebugBaseType('void', 0, 1)
        self._builder.set_function(ir_func)

        # Start in entry block:
        first_block = self._builder.new_block()
        self._builder.set_block(first_block)
        ir_func.entry = first_block

        dbg_arg_types = []
        self.local_variables = []

        for index, parameter_type in enumerate(signature.parameter_types):
            ir_typ = self.get_ir_type(parameter_type)
            parameter_name = 'param{}'.format(index)
            ir_parameter = ir.Parameter(parameter_name, ir_typ)
            ir_func.add_parameter(ir_parameter)
            self.local_variables.append(ir_parameter)
            dbg_arg_types.append(debuginfo.DebugParameter(
                'arg{}'.format(index), self.get_debug_type(parameter_type)))

        # Enter correct debug info:
        db_function_info = debuginfo.DebugFunction(
            ir_func.name,
            SourceLocation('somefile.java', 1, 1, 1),
            dbg_return_type, dbg_arg_types)
        self.debug_db.enter(ir_func, db_function_info)

        for attribute in method.attributes:
            attrib_name = self.class_file.get_name(attribute.name_index)
            if attrib_name == 'Code':
                # Now we found bytecode.
                code = load_code(attribute.data)
                self.gen_code(code)
            else:
                logger.warning('Unhandled attribute: %s', attrib_name)

        if signature.return_type:
            value = self.stack.pop()
            self.emit(ir.Return(value))
        else:
            self.emit(ir.Exit())

    def gen_code(self, code):
        logger.debug(
            'Max stack=%s, max locals=%s',
            code.max_stack, code.max_locals)

        # print(code.attributes)
        for index in range(code.max_locals):
            var = self.emit(
                ir.Const(0, 'z_{}'.format(index), ir.i32))
            self.local_variables.append(var)

        self.stack = []
        for instruction in code.code:
            self.gen_instr(instruction)

    def gen_instr(self, instruction):
        """ Generate ir-code for a single instruction. """
        logger.debug('processing opcode 0x%X', instruction)
        opcode = instruction
        if instruction == 0x60:  # Add integer.
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
