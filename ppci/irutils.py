
"""
    Some utilities for ir-code.
"""
import logging
import re
from . import ir
from .domtree import CfgInfo
from .common import IrFormError


IR_FORMAT_INDENT = 2


class Writer:
    """ Write ir-code to file """
    def __init__(self, extra_indent=''):
        self.extra_indent = extra_indent

    def print(self, level, txt):
        indent = self.extra_indent + ' ' * (level * IR_FORMAT_INDENT)
        print(indent + txt, file=self.f)

    def write(self, module, f):
        """ Write ir-code to file f """
        assert type(module) is ir.Module
        Verifier().verify(module)
        self.f = f
        self.print(0, '{};'.format(module))
        for v in module.variables:
            self.print(0, '')
            self.print(0, str(v))
        for function in module.functions:
            self.print(0, '')
            self.write_function(function)

    def write_function(self, fn):
        self.print(0, '{} {{'.format(fn))
        for block in fn.blocks:
            self.print(1, '{} {{'.format(block))
            for ins in block:
                self.print(2, '{};'.format(ins))
            self.print(1, '}')
        self.print(0, '}')


class IrParseException(Exception):
    pass


class Reader:
    """ Read IR-code from file """
    def __init__(self):
        pass

    def read(self, f):
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
        self.resolve_worklist = []

        self.consume('(')
        while self.peak != ')':
            ty = self.parse_type()
            name = self.consume('ID')[1]
            param = ir.Parameter(name, ty)
            function.add_parameter(param)
            self.add_val(param)
            if self.peak != ',':
                break
            else:
                self.consume(',')
        self.consume(')')
        self.consume('{')
        while self.peak != '}':
            block = self.parse_block(function)
            if function.entry is None:
                function.entry = block
            self.block_map[block.name] = block
        self.consume('}')

        for ins, blocks in self.resolve_worklist:
            for b in blocks:
                b2 = self.find_block(b.name)
                ins.change_target(b, b2)
        return function

    def parse_type(self):
        type_map = {t.name: t for t in ir.all_types}
        type_name = self.consume('ID')[1]
        return type_map[type_name]

    def parse_block(self, function):
        name = self.consume('ID')[1]
        block = ir.Block(name)
        function.add_block(block)
        self.consume(':')
        self.consume('{')
        while self.peak != '}':
            ins = self.parse_statement()
            block.add_instruction(ins)
        self.consume('}')
        return block

    def add_val(self, v):
        self.val_map[v.name] = v

    def find_val(self, name):
        return self.val_map[name]

    def find_block(self, name):
        return self.block_map[name]

    def parse_assignment(self):
        ty = self.parse_type()
        name = self.consume('ID')[1]
        self.consume('=')
        if self.peak == 'ID':
            a = self.consume('ID')[1]
            if self.peak in ['+', '-']:
                # Go for binop
                op = self.consume(self.peak)[1]
                b = self.consume('ID')[1]
                a = self.find_val(a)
                b = self.find_val(b)
                ins = ir.Binop(a, op, b, name, ty)
            else:
                raise Exception()
        elif self.peak == 'NUMBER':
            cn = self.consume('NUMBER')[1]
            ins = ir.Const(cn, name, ty)
        else:
            raise Exception()
        return ins

    def parse_cjmp(self):
        self.consume('cjmp')
        a = self.consume('ID')[1]
        op = self.consume(self.peak)[0]
        b = self.consume('ID')[1]
        self.consume('?')
        L1 = self.consume('ID')[1]
        L1 = ir.Block(L1)
        self.consume(':')
        L2 = self.consume('ID')[1]
        L2 = ir.Block(L2)
        a = self.find_val(a)
        b = self.find_val(b)
        ins = ir.CJump(a, op, b, L1, L2)
        self.resolve_worklist.append((ins, (L1, L2)))
        return ins

    def parse_jmp(self):
        self.consume('jmp')
        L1 = self.consume('ID')[1]
        L1 = ir.Block(L1)
        ins = ir.Jump(L1)
        self.resolve_worklist.append((ins, (L1,)))
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
            self.add_val(ins)
        self.consume(';')
        return ins


# Constructing IR:

class NamedClassGenerator:
    def __init__(self, prefix, cls):
        self.prefix = prefix
        self.cls = cls

        def NumGen():
            a = 0
            while True:
                yield a
                a = a + 1
        self.nums = NumGen()

    def gen(self, prefix=None):
        if not prefix:
            prefix = self.prefix
        return self.cls('{0}{1}'.format(prefix, self.nums.__next__()))


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
        self.prepare()

    def prepare(self):
        self.newBlock2 = NamedClassGenerator('block', ir.Block).gen
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

    def new_block(self):
        """ Create a new block and add it to the current function """
        assert self.function is not None
        block = self.newBlock2()
        self.function.add_block(block)
        return block

    def set_function(self, f):
        self.function = f
        self.block = f.entry if f else None

    def set_block(self, block):
        self.block = block

    def emit(self, instruction):
        """ Append an instruction to the current block """
        assert isinstance(instruction, ir.Instruction), str(instruction)
        if self.block is None:
            raise Exception('No basic block')
        self.block.add_instruction(instruction)
        return instruction


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
                assert block.last_instruction.result.ty is function.return_ty
            if isinstance(block.last_instruction, ir.Exit):
                assert isinstance(function, ir.Procedure)

        # Verify the entry is in this function and is the first block:
        assert function.entry is function.blocks[0]
        assert isinstance(function.entry, ir.Block)

        # Verify all blocks are reachable:
        reachable_blocks = function.calc_reachable_blocks()
        for block in function:
            assert block in reachable_blocks

        # Verify predecessor and successor:
        for block in function:
            preds = set(b for b in function if block in b.successors)
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
        for block in function:
            assert block.function is function
            self.verify_block(block)

    def verify_block_termination(self, block):
        """ Verify that the block is terminated correctly """
        assert not block.is_empty
        assert block.last_instruction.is_terminator
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

        # Check that binop operands are of same type:
        if isinstance(instruction, ir.Binop):
            assert instruction.ty is instruction.a.ty
            assert instruction.ty is instruction.b.ty
        elif isinstance(instruction, ir.Load):
            assert instruction.address.ty is ir.ptr
        elif isinstance(instruction, ir.Store):
            assert instruction.address.ty is ir.ptr
        elif isinstance(instruction, ir.Phi):
            for inp_val in instruction.inputs.values():
                assert instruction.ty is inp_val.ty
        elif isinstance(instruction, ir.CJump):
            assert instruction.a.ty is instruction.b.ty

        # Verify that all uses are defined before this instruction.
        for value in instruction.uses:
            assert self.instruction_dominates(value, instruction), \
                "{} does not dominate {}".format(value, instruction)
            # Check that a value is not undefined:
            if isinstance(value, ir.Undefined):
                raise IrFormError('{} is used'.format(value))

    def instruction_dominates(self, one, another):
        """ Checks if one instruction dominates another instruction """
        if isinstance(one, (ir.Parameter, ir.Variable)):
            # TODO: hack, parameters and globals dominate all other
            # instructions..
            return True

        # All other instructions must have a containing block:
        assert one.block is not None, '{} has no block'.format(one)
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

    def block_dominates(self, one, another):
        """ Check if this block dominates other block """
        assert one in one.function
        return self.cfg_info.strictly_dominates(one, another)
