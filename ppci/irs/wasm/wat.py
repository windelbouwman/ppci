""" Web assembly text format utilities """

from .components import ExportSection, TypeSection, FunctionSection
from .components import CodeSection, ImportSection, TableSection
from .components import MemorySection, StartSection, ElementSection
from .components import DataSection, Module
from ._opcodes import STORE_OPS, LOAD_OPS

MEM_OPS = LOAD_OPS | STORE_OPS


def wasm_to_wat(module: Module, f):
    """ Translate a wasm module into textual format.

    Args:
        module (ppci.irs.wasm.Module): A wasm-module
        f: The file to write to
    """
    WatGenerator(f).generate(module)


class WatGenerator:
    """ Wasm text format generator """
    def __init__(self, f):
        self.f = f
        self.module = None
        self.indentation = 2
        self.block_nr = 0

    def generate(self, module: Module):
        """ Write the given module in wasm text (wat) format """
        self.print('(module')
        self.module = module
        exports = []
        functions = []
        function_defs = []
        # TODO: use S-expressions so that we can create S-expressions and
        # render those expressions as text!
        current_idx = 0
        for section in module.sections:
            if section.id == TypeSection.id:
                for idx, t in enumerate(section.functionsigs):
                    self.print(
                        '  (type (;{};) (func'.format(idx),
                        newline=True)
                    self.write_type(t)
                    self.print('))', newline=False)
            elif section.id == ImportSection.id:
                for idx, imp in enumerate(section.imports):
                    self.print(
                        '  (import "{}" "{}" (func (;{};) (type {})))'.format(
                            imp.modname, imp.fieldname, idx, imp.type_id),
                        newline=True)
                current_idx = idx
            elif section.id == TableSection.id:
                pass
            elif section.id == MemorySection.id:
                pass
            elif section.id == StartSection.id:
                pass
            elif section.id == ElementSection.id:
                print(section)
            elif section.id == DataSection.id:
                print(section)
            elif section.id == FunctionSection.id:
                functions.extend(section.indices)
            elif section.id == ExportSection.id:
                exports.extend(section.exports)
            elif section.id == CodeSection.id:
                function_defs.extend(section.functiondefs)
            else:
                raise NotImplementedError('Section {}'.format(section.id))

        # Printout functions:
        for idx, func in enumerate(
                zip(functions, function_defs),
                start=current_idx+1):
            function_typ, function_def = func
            self.print(
                '  (func (;{};) (type {})'.format(idx, function_typ),
                newline=True)
            typ = module.get_type(function_typ)
            self.write_type(typ)

            if function_def.locals:
                local_types = ' '.join(function_def.locals)
                self.print('    (local {})'.format(local_types), newline=True)

            self.block_nr = 0
            for i in function_def.instructions:
                self.write_instruction(i)
            self.print(')')

        # Print tables:
        if module.has_section(TableSection):
            table_section = module.get_section(TableSection)
            for idx, table in enumerate(table_section):
                self.print(
                    '  (table (;{};) {} {} {})'.format(
                        idx, table.minimum, table.maximum, table.typ),
                    newline=True)

        # Print memory:
        if module.has_section(MemorySection):
            memory_section = module.get_section(MemorySection)
            for idx, memory in enumerate(memory_section):
                self.print(
                    '  (memory (;{};) {})'.format(
                        idx, memory[0]),
                    newline=True)

        # Printout exports:
        for export in exports:
            self.print(
                '  (export "{}" ({} {}))'.format(
                    export.name, export.kind, export.index),
                newline=True)

        # Print start point:
        if module.has_section(StartSection):
            start_section = module.get_section(StartSection)
            self.print(
                '  (start {})'.format(start_section.index),
                newline=True)

        # Print elements:
        if module.has_section(ElementSection):
            element_section = module.get_section(ElementSection)
            for element in element_section:
                indexes = ' '.join(map(str, element.indexes))
                self.print(
                    '  (elem (i32.const {}) {})'.format(
                        element.offset, indexes),
                    newline=True)

        if module.has_section(DataSection):
            data_section = module.get_section(DataSection)
            for chunk in data_section:
                _, offset, data = chunk
                data = self.data_as_string(data)
                self.print(
                    '  (data (i32.const {}) "{}")'.format(offset, data),
                    newline=True)
        self.print(')')
        self.print(newline=True)

    @staticmethod
    def data_as_string(data: bytes):
        """ Encode data as a string """
        def mkchar(v):
            """ Encode a single byte as its ascii printable char (or not) """
            if v >= 0x20 and v < 0x7f and v != 0x22 and v != 0x5c:
                return chr(v)
            else:
                return '\\{:02x}'.format(v)
        return ''.join(mkchar(b) for b in data)

    def write_type(self, t):
        """ Print function type """
        if t.params:
            params = 'param ' + ' '.join(t.params)
            print(' ({})'.format(params), end='', file=self.f)
        if t.returns:
            returns = 'result ' + ' '.join(t.returns)
            print(' ({})'.format(returns), end='', file=self.f)

    def write_instruction(self, instruction):
        """ Print a single instruction """
        if instruction.opcode in MEM_OPS:
            text = str(instruction.opcode)
            alignment, offset = instruction.args
            if offset:
                text += ' offset={}'.format(offset)

            natural_alignments = {
                'f64.store': 3,
                'f32.store': 2,
                'i64.store': 3,
                'i64.store8': 0,
                'i64.store16': 1,
                'i64.store32': 2,
                'i32.store': 2,
                'i32.store8': 0,
                'i32.store16': 1,

                'f64.load': 3,
                'f32.load': 2,
                'i64.load': 3,
                'i64.load8_u': 0,
                'i64.load8_s': 0,
                'i64.load16_u': 1,
                'i64.load16_s': 1,
                'i64.load32_u': 2,
                'i64.load32_s': 2,
                'i32.load': 2,
                'i32.load8_u': 0,
                'i32.load8_s': 0,
                'i32.load16_u': 1,
                'i32.load16_s': 1,
            }
            default_alignment = natural_alignments[instruction.opcode]
            if alignment != default_alignment:
                text += ' align={}'.format(1 << alignment)
        elif instruction.opcode in ['block', 'loop']:
            self.block_nr += 1
            text = '{}  ;; label = @{}'.format(
                instruction.opcode,
                self.block_nr)
        elif instruction.opcode in ['br', 'br_if']:
            text = '{} {} (;@{};)'.format(
                instruction.opcode, instruction.args[0],
                self.block_nr - instruction.args[0])
        elif instruction.opcode == 'br_table':
            targets = ' '.join(
                '{} (;@{};)'.format(a, self.block_nr - a)
                for a in instruction.args[0])
            text = 'br_table {}'.format(targets)
        elif instruction.opcode in ['call_indirect']:
            text = '{} {}'.format(instruction.opcode, instruction.args[0])
        elif instruction.opcode in ['current_memory', 'grow_memory']:
            text = str(instruction.opcode)
        elif instruction.opcode in ['f64.const', 'f32.const']:
            text = '{} {} (;={};)'.format(
                instruction.opcode,
                float.hex(instruction.args[0]),
                instruction.args[0])
        else:
            if instruction.args:
                args = ' '.join(map(str, instruction.args))
                text = '{} {}'.format(instruction.opcode, args)
            else:
                text = str(instruction.opcode)

        if instruction.opcode in ['end']:
            self.indentation -= 1
            self.block_nr -= 1

        # Print the instruction
        indent = '  ' * self.indentation
        self.print('{}{}'.format(indent, text), newline=True)

        if instruction.opcode in ['block', 'loop']:
            self.indentation += 1

    def print(self, *args, newline=False):
        """ Print helper """
        if newline:
            print(file=self.f)
        print(*args, end='', file=self.f)
