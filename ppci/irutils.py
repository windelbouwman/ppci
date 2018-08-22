
"""
    Some utilities for ir-code.
"""
import logging
import re
from collections import defaultdict
from . import ir
from .graph.domtree import CfgInfo
from .common import IrFormError


IR_FORMAT_INDENT = 2


def print_module(module, file=None, verify=True):
    """ Print an ir-module as text """
    Writer(file=file).write(module, verify=verify)


class Writer:
    """ Write ir-code to file """
    def __init__(self, file=None, extra_indent=''):
        self.extra_indent = extra_indent
        self.file = file

    def print(self, level, txt):
        indent = self.extra_indent + ' ' * (level * IR_FORMAT_INDENT)
        print(indent + txt, file=self.file)

    def write(self, module: ir.Module, verify=True):
        """ Write ir-code to file f """
        assert isinstance(module, ir.Module)
        if verify:
            verify_module(module)
        self.print(0, '{};'.format(module))

        for e in module.externals:
            self.print(0, '')
            self.print(0, '{};'.format(e))

        for variable in module.variables:
            self.print(0, '')
            self.print(0, str(variable))

        for function in module.functions:
            self.print(0, '')
            self.write_function(function)

    def write_function(self, function):
        self.print(0, '{} {{'.format(function))
        for block in function.blocks:
            self.print(1, '{} {{'.format(block))
            for ins in block:
                self.print(2, '{};'.format(ins))
            self.print(1, '}')
            self.print(0, '')
        self.print(0, '}')


class IrParseException(Exception):
    pass


def read_module(f) -> ir.Module:
    """ Read an ir-module from file.

    Args:
        f: A file like object ready to be read in text modus.

    Returns:
        The loaded ir-module.
    """
    return Reader().read(f)


class Reader:
    """ Read IR-code from file """
    def __init__(self):
        pass

    def read(self, f) -> ir.Module:
        """ Read ir code from file f """
        # Read lines from the file:
        lines = [line.rstrip() for line in f]

        # Create a regular expression for the lexing part:
        tok_spec = [
            ('NUMBER', r'\d+'),
            ('ID', r'[A-Za-z][A-Za-z\d_]*'),
            ('SKIP', r'\s+'),
            ('OTHER', r'[\.,=:;\-\?+*\[\]/\(\)]|>|<|{|}|&|\^|\|')
            ]
        tok_re = '|'.join('(?P<%s>%s)' % pair for pair in tok_spec)
        gettok = re.compile(tok_re).match
        keywords = [
            'function', 'module', 'procedure',
            'store', 'load',
            'cast',
            'jmp', 'cjmp',
            'exit', 'return'
            ]

        def tokenize():
            for line in lines:
                if not line:
                    continue  # Skip empty lines
                mo = gettok(line)
                while mo:
                    typ = mo.lastgroup
                    val = mo.group(typ)
                    if typ == 'ID':
                        if val in keywords:
                            typ = val
                        yield (typ, val)
                    elif typ == 'OTHER':
                        typ = val
                        yield (typ, val)
                    elif typ == 'SKIP':
                        pass
                    elif typ == 'NUMBER':
                        yield (typ, int(val))
                    else:
                        raise NotImplementedError(str(typ))
                    pos = mo.end()
                    mo = gettok(line, pos)
                if len(line) != pos:
                    raise IrParseException('Lex fault')
            yield ('eof', 'eof')
        self.tokens = tokenize()
        self.token = self.tokens.__next__()

        try:
            module = self.parse_module()
            return module
        except IrParseException as e:
            print(e)
            raise Exception(str(e))

    def next_token(self):
        t = self.token
        if t[0] != 'eof':
            self.token = self.tokens.__next__()
        return t

    @property
    def peak(self):
        return self.token[0]

    def consume(self, typ):
        if self.peak == typ:
            return self.next_token()
        else:
            raise IrParseException('Expected "{}" got "{}"'
                                   .format(typ, self.peak))

    def parse_module(self):
        """ Entry for recursive descent parser """
        self.consume('module')
        name = self.consume('ID')[1]
        module = ir.Module(name)
        self.consume(';')
        while self.peak != 'eof':
            if self.peak in ['function', 'procedure']:
                module.add_function(self.parse_function())
            else:
                raise IrParseException('Expected function got {}'
                                       .format(self.peak))
        return module

    def parse_function(self):
        """ Parse a function or procedure """
        if self.peak == 'function':
            self.consume('function')
            return_type = self.parse_type()
            name = self.consume('ID')[1]
            function = ir.Function(name, return_type)
        else:
            self.consume('procedure')
            name = self.consume('ID')[1]
            function = ir.Procedure(name)

        # Setup maps:
        self.val_map = {}
        self.block_map = {}

        self.consume('(')
        while self.peak != ')':
            ty = self.parse_type()
            name = self.consume('ID')[1]
            param = ir.Parameter(name, ty)
            function.add_parameter(param)
            self.define_value(param)
            if self.peak != ',':
                break
            else:
                self.consume(',')
        self.consume(')')
        self.consume('{')
        while self.peak != '}':
            block = self.parse_block(function)
            self.block_map[block.name] = block
        self.consume('}')

        return function

    def parse_type(self):
        """ Parse a single type """
        type_map = {t.name: t for t in ir.all_types}
        type_name = self.consume('ID')[1]
        return type_map[type_name]

    def _get_block(self, name):
        """ Get or create the given block """
        if name not in self.block_map:
            self.block_map[name] = ir.Block(name)
        return self.block_map[name]

    def parse_block(self, function):
        """ Read a single block from file """
        name = self.consume('ID')[1]
        block = self._get_block(name)
        function.add_block(block)
        if function.entry is None:
            function.entry = block
        self.consume(':')
        self.consume('{')
        while self.peak != '}':
            ins = self.parse_statement()
            block.add_instruction(ins)
        self.consume('}')
        return block

    def define_value(self, v):
        """ Define a value """
        if v.name in self.val_map:
            # Now what? Double declaration?
            old_value = self.val_map[v.name]
            assert isinstance(old_value, ir.Undefined)
            old_value.replace_by(v)
        self.val_map[v.name] = v

    def find_val(self, name, ty=ir.i32):
        if name not in self.val_map:
            self.val_map[name] = ir.Undefined(name, ty)
        return self.val_map[name]

    def find_block(self, name):
        return self.block_map[name]

    def parse_assignment(self):
        """ Parse an instruction with shape 'ty' 'name' '=' ... """
        ty = self.parse_type()
        name = self.consume('ID')[1]
        self.consume('=')
        if self.peak == 'ID':
            a = self.consume('ID')[1]
            if a == 'phi':
                ins = ir.Phi(name, ty)
                b1 = self._get_block(self.consume('ID')[1])
                self.consume(':')
                v1 = self.find_val(self.consume('ID')[1])
                ins.set_incoming(b1, v1)
                while self.peak == ',':
                    self.consume(',')
                    b1 = self._get_block(self.consume('ID')[1])
                    self.consume(':')
                    v1 = self.find_val(self.consume('ID')[1])
                    ins.set_incoming(b1, v1)
            else:
                if self.peak in ['+', '-']:
                    # Go for binop
                    op = self.consume(self.peak)[1]
                    b = self.consume('ID')[1]
                    a = self.find_val(a)
                    b = self.find_val(b)
                    ins = ir.Binop(a, op, b, name, ty)
                else:
                    raise NotImplementedError(self.peak)
        elif self.peak == 'NUMBER':
            cn = self.consume('NUMBER')[1]
            ins = ir.Const(cn, name, ty)
        else:  # pragma: no cover
            raise NotImplementedError(self.peak)
        return ins

    def parse_cjmp(self):
        self.consume('cjmp')
        a = self.consume('ID')[1]
        op = self.consume(self.peak)[0]
        b = self.consume('ID')[1]
        self.consume('?')
        L1 = self.consume('ID')[1]
        L1 = self._get_block(L1)
        self.consume(':')
        L2 = self.consume('ID')[1]
        L2 = self._get_block(L2)
        a = self.find_val(a)
        b = self.find_val(b)
        ins = ir.CJump(a, op, b, L1, L2)
        return ins

    def parse_jmp(self):
        self.consume('jmp')
        L1 = self.consume('ID')[1]
        L1 = self._get_block(L1)
        ins = ir.Jump(L1)
        return ins

    def parse_return(self):
        self.consume('return')
        v = self.find_val(self.consume('ID')[1])
        ins = ir.Return(v)
        return ins

    def parse_statement(self):
        """ Parse a single instruction line """
        if self.peak == 'jmp':
            ins = self.parse_jmp()
        elif self.peak == 'cjmp':
            ins = self.parse_cjmp()
        elif self.peak == 'return':
            ins = self.parse_return()
        elif self.peak == 'store':
            raise Exception()
        elif self.peak == 'exit':
            self.consume('exit')
            ins = ir.Exit()
        else:
            ins = self.parse_assignment()
            self.define_value(ins)
        self.consume(';')
        return ins


# Constructing IR:

def split_block(block, pos=None, newname='splitblock'):
    """ Split a basic block into two which are connected """
    if pos is None:
        pos = int(len(block) / 2)
    rest = block.instructions[pos:]
    block2 = ir.Block(newname)
    block.function.add_block(block2)
    for instruction in rest:
        block.remove_instruction(instruction)
        block2.add_instruction(instruction)

    # Add a jump to the original block:
    block.add_instruction(ir.Jump(block2))
    return block, block2


class Builder:
    """ Base class for ir code generators """
    def __init__(self):
        self.block = None
        self.module = None
        self.function = None
        self.block_number = 0
        self.prepare()

    def prepare(self):
        self.block = None
        self.module = None
        self.function = None

    # Helpers:
    def set_module(self, module):
        self.module = module

    def new_function(self, name, return_ty):
        assert self.module is not None
        f = ir.Function(name, return_ty)
        self.module.add_function(f)
        return f

    def new_procedure(self, name):
        assert self.module is not None
        f = ir.Procedure(name)
        self.module.add_function(f)
        return f

    def new_block(self, name=None):
        """ Create a new block and add it to the current function """
        assert self.function is not None
        if name is None:
            name = '{}_block{}'.format(self.function.name, self.block_number)
            self.block_number += 1
        block = ir.Block(name)
        self.function.add_block(block)
        return block

    def set_function(self, f):
        self.function = f
        self.block = f.entry if f else None
        self.block_number = 0

    def set_block(self, block):
        self.block = block

    def emit(self, instruction: ir.Instruction) -> ir.Instruction:
        """ Append an instruction to the current block """
        assert isinstance(instruction, ir.Instruction), str(instruction)
        assert self.block is not None
        self.block.add_instruction(instruction)
        return instruction


def verify_module(module: ir.Module):
    """ Check if the module is properly constructed """
    Verifier().verify(module)


class Verifier:
    """ Checks an ir module for correctness """
    logger = logging.getLogger('verifier')

    def __init__(self):
        self.name_map = {}

    def verify(self, module):
        """ Verifies a module for some sanity """
        self.logger.debug('Verifying %s', module)
        assert isinstance(module, ir.Module)
        for function in module.functions:
            self.verify_function(function)

    def verify_function(self, function):
        """ Verify all blocks in the function """
        self.name_map = {}
        for block in function:
            assert block.name not in self.name_map
            self.name_map[block.name] = block
            self.verify_block_termination(block)
            if isinstance(block.last_instruction, ir.Return):
                assert isinstance(function, ir.Function)
                if block.last_instruction.result.ty is not function.return_ty:
                    raise IrFormError(
                        'Last instruction returns {}, while function {}'
                        'returns {}'.format(
                            block.last_instruction.result.ty,
                            function,
                            function.return_ty))
            if isinstance(block.last_instruction, ir.Exit):
                assert isinstance(function, ir.Procedure)

        # Verify the entry is in this function and is the first block:
        assert function.entry is function.blocks[0]
        assert isinstance(function.entry, ir.Block)

        # Verify all blocks are reachable:
        reachable_blocks = function.calc_reachable_blocks()
        for block in function:
            assert block in reachable_blocks

        # Determine predecessors from sucessors:
        predecessor_map = defaultdict(set)
        for block in function:
            for block2 in block.successors:
                predecessor_map[block2].add(block)

        # Verify predecessor and successor:
        for block in function:
            preds = predecessor_map[block]
            assert preds == set(block.predecessors)

        # Check that phi's have inputs for each predecessor:
        for block in function:
            for phi in block.phis:
                for predecessor in block.predecessors:
                    used_value = phi.get_value(predecessor)
                    # Check that phi 'use' info is good:
                    assert used_value in phi.uses

        # Now we can build a dominator tree
        self.cfg_info = CfgInfo(function)
        if len(self.cfg_info.cfg) > 2000:
            self.logger.error('Skipping verify of more than 2000 cfg nodes')
            return

        for block in function:
            assert block.function is function
            self.verify_block(block)

    def verify_block_termination(self, block):
        """ Verify that the block is terminated correctly """
        if block.is_empty:
            raise ValueError('Block is empty: {}'.format(block))
        if not block.last_instruction.is_terminator:
            raise ValueError(
                'The last instruction of {} is not a terminator instruction'
                .format(block))
        assert all(not i.is_terminator for i in block.instructions[:-1])
        assert all(isinstance(p, ir.Block) for p in block.predecessors)

    def verify_block(self, block):
        """ Verify block for correctness """
        for instruction in block:
            self.verify_instruction(instruction, block)

    def verify_instruction(self, instruction, block):
        """ Verify that instruction belongs to block and that all uses
            are preceeded by defs """

        # Check that instruction is contained in block:
        assert instruction.block == block
        assert instruction in block.instructions

        # Check if value has unique name string:
        if isinstance(instruction, ir.Value):
            assert instruction.name not in self.name_map
            self.name_map[instruction.name] = instruction

        if isinstance(instruction, ir.Binop):
            # Check that binop operands are of same type:
            if instruction.ty is not instruction.a.ty:
                raise TypeError(
                    "Binary operand a's type ({}) is not {}".format(
                        instruction.a.ty, instruction.ty))
            if instruction.ty is not instruction.b.ty:
                raise TypeError(
                    "Binary operand b's type({}) is not {}".format(
                        instruction.b.ty, instruction.ty))
        elif isinstance(instruction, ir.Load):
            if instruction.address.ty is not ir.ptr:
                raise TypeError(
                    'Load instruction requires ptr type, not {}'.format(
                        instruction.address.ty))
        elif isinstance(instruction, ir.Store):
            if instruction.address.ty is not ir.ptr:
                raise TypeError(
                    'Store instruction requires ptr type, not {}'.format(
                        instruction.address.ty))
        elif isinstance(instruction, ir.Phi):
            for inp_val in instruction.inputs.values():
                assert instruction.ty is inp_val.ty
        elif isinstance(instruction, ir.CJump):
            if instruction.a.ty is not instruction.b.ty:
                raise IrFormError('Type {} is not {} in {}'.format(
                    instruction.a.ty, instruction.b.ty, instruction))
        elif isinstance(instruction, (ir.FunctionCall, ir.ProcedureCall)):
            if isinstance(
                    instruction.callee,
                    (ir.SubRoutine, ir.ExternalSubRoutine)):
                self.verify_subroutine_call(instruction)

        # Verify that all uses are defined before this instruction.
        for value in instruction.uses:
            assert self.instruction_dominates(value, instruction), \
                "{} does not dominate {}".format(value, instruction)
            # Check that a value is not undefined:
            if isinstance(value, ir.Undefined):
                raise IrFormError('{} is used'.format(value))

    def verify_subroutine_call(self, instruction):
        """ Check some properties of a function call """
        # Check if we called function or procedure:
        callee = instruction.callee
        if isinstance(instruction, ir.FunctionCall):
            if not isinstance(callee, (ir.Function, ir.ExternalFunction)):
                raise IrFormError('{} expected a function, but got: {}'.format(
                    instruction, callee))

            # Check return type:
            if callee.return_ty is not instruction.ty:
                raise IrFormError('Function returns {}, expected {}'.format(
                    callee.return_ty, instruction.ty))
        else:
            if not isinstance(callee, (ir.Procedure, ir.ExternalProcedure)):
                raise IrFormError('{} expected a procedure, got: {}'.format(
                    instruction, callee))

        # Check arguments:
        passed_types = [a.ty for a in instruction.arguments]
        if isinstance(callee, ir.SubRoutine):
            arg_types = [a.ty for a in callee.arguments]
        else:
            arg_types = callee.argument_types
        name = instruction.callee.name

        # Check amount of arguments:
        if len(passed_types) != len(arg_types):
            raise IrFormError(
                '{} expects {} arguments, but called with {}'.format(
                    name, len(arg_types), len(passed_types)))

        for passed_type, arg_type in zip(passed_types, arg_types):
            if passed_type is not arg_type:
                raise IrFormError(
                    '{} expects {}, but got {}'.format(
                        name, arg_type, passed_type))

    def instruction_dominates(self, one, another):
        """ Checks if one instruction dominates another instruction """
        if isinstance(one, (ir.Parameter, ir.GlobalValue)):
            # TODO: hack, parameters and globals dominate all other
            # instructions..
            return True

        # All other instructions must have a containing block:
        if one.block is None:
            raise ValueError('{} has no block'.format(one))
        assert one in one.block.instructions

        # Phis are special case:
        if isinstance(another, ir.Phi):
            for block in another.inputs:
                if another.inputs[block] is one:
                    # This is the queried dominance branch
                    # Check if this instruction dominates the last
                    # instruction of this block
                    return self.instruction_dominates(
                        one, block.last_instruction)
            raise RuntimeError(
                'Cannot query dominance for this phi')  # pragma: no cover
        else:
            # For all other instructions follow these rules:
            if one.block is another.block:
                return one.position < another.position
            else:
                return self.block_dominates(one.block, another.block)

    def block_dominates(self, one: ir.Block, another: ir.Block):
        """ Check if this block dominates other block """
        assert one in one.function
        one_node = self.cfg_info.get_node(one)
        another_node = self.cfg_info.get_node(another)
        return self.cfg_info.cfg.strictly_dominates(one_node, another_node)
