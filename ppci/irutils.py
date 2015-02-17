
"""
    Some utilities for ir-code.
"""
import logging
import re
from . import ir
from .domtree import CfgInfo


def dumpgv(m, outf):
    print('digraph G ', file=outf)
    print('{', file=outf)
    for f in m.Functions:
        print('{} [label="{}" shape=box3d]'.format(id(f), f), file=outf)
        for bb in f.Blocks:
            contents = str(bb) + '\n'
            contents += '\n'.join([str(i) for i in bb.Instructions])
            print('{0} [shape=note label="{1}"];'
                  .format(id(bb), contents), file=outf)
            for successor in bb.Successors:
                print('"{}" -> "{}"'.format(id(bb), id(successor)), file=outf)

        print('"{}" -> "{}" [label="entry"]'
              .format(id(f), id(f.entry)), file=outf)
    print('}', file=outf)


class Writer:
    """ Write ir-code to file """
    def __init__(self, extra_indent=''):
        self.extra_indent = extra_indent

    def print(self, txt):
        print(txt, file=self.f)

    def write(self, module, f):
        """ Write ir-code to file f """
        assert type(module) is ir.Module
        self.f = f
        self.print('{}{}'.format(self.extra_indent, module))
        for v in module.Variables:
            self.print('{}{}'.format(self.extra_indent, v))
        for function in module.Functions:
            self.write_function(function)

    def write_function(self, fn):
        args = ','.join('i32 ' + str(a) for a in fn.arguments)
        self.print('{}function i32 {}({})'
                   .format(self.extra_indent, fn.name, args))
        for block in fn.blocks:
            self.print('{} {}'.format(self.extra_indent, block))
            for ins in block:
                self.print('{}  {}'.format(self.extra_indent, ins))


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
            ('SKIP2', r'  '),
            ('SKIP1', r' '),
            ('OTHER', r'[\.,=:;\-+*\[\]/\(\)]|>|<|{|}|&|\^|\|')
            ]
        tok_re = '|'.join('(?P<%s>%s)' % pair for pair in tok_spec)
        gettok = re.compile(tok_re).match

        def tokenize():
            for line in lines:
                if not line:
                    continue  # Skip empty lines
                mo = gettok(line)
                first = True
                while mo:
                    typ = mo.lastgroup
                    val = mo.group(typ)
                    if typ == 'ID':
                        if val in ['function', 'module']:
                            typ = val
                        yield (typ, val)
                    elif typ == 'OTHER':
                        typ = val
                        yield (typ, val)
                    elif typ in ['SKIP1', 'SKIP2']:
                        if first:
                            yield (typ, val)
                    elif typ == 'NUMBER':
                        yield (typ, int(val))
                    else:
                        raise NotImplementedError(str(typ))
                    first = False
                    pos = mo.end()
                    mo = gettok(line, pos)
                if len(line) != pos:
                    raise IrParseException('Lex fault')
                yield ('eol', 'eol')
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
    def Peak(self):
        return self.token[0]

    @property
    def PeakVal(self):
        return self.token[1]

    def Consume(self, typ, val=None):
        if self.Peak == typ:
            if val is not None:
                assert self.PeakVal == val
            return self.next_token()
        else:
            raise IrParseException('Expected "{}" got "{}"'
                                   .format(typ, self.Peak))

    def parse_module(self):
        """ Entry for recursive descent parser """
        self.Consume('module')
        name = self.Consume('ID')[1]
        module = ir.Module(name)
        self.Consume('eol')
        while self.Peak != 'eof':
            if self.Peak == 'function':
                module.add_function(self.parse_function())
            else:
                raise IrParseException('Expected function got {}'
                                       .format(self.Peak))
        return module

    def parse_function(self):
        self.Consume('function')
        self.parse_type()

        # Setup maps:
        self.val_map = {}
        self.block_map = {}
        self.resolve_worklist = []

        name = self.Consume('ID')[1]
        function = ir.Function(name)
        self.Consume('(')
        while self.Peak != ')':
            ty = self.parse_type()
            name = self.Consume('ID')[1]
            ty = self.find_type(ty)
            param = ir.Parameter(name, ty)
            function.add_parameter(param)
            self.add_val(param)
            if self.Peak != ',':
                break
            else:
                self.Consume(',')
        self.Consume(')')
        self.Consume('eol')
        while self.Peak == 'SKIP1':
            block = self.parse_block()
            function.add_block(block)
            self.block_map[block.name] = block

        for ins, blocks in self.resolve_worklist:
            for b in blocks:
                b2 = self.find_block(b.name)
                ins.change_target(b, b2)
        return function

    def parse_type(self):
        return self.Consume('ID')[1]

    def parse_block(self):
        self.Consume('SKIP1')
        name = self.Consume('ID')[1]
        block = ir.Block(name)
        self.Consume(':')
        self.Consume('eol')
        while self.Peak == 'SKIP2':
            ins = self.parse_statement()
            block.add_instruction(ins)
        return block

    def add_val(self, v):
        self.val_map[v.name] = v

    def find_val(self, name):
        return self.val_map[name]

    def find_type(self, name):
        ty_map = {'i32': ir.i32}
        return ty_map[name]

    def find_block(self, name):
        return self.block_map[name]

    def parse_assignment(self):
        ty = self.Consume('ID')[1]
        name = self.Consume('ID')[1]
        self.Consume('=')
        if self.Peak == 'ID':
            a = self.Consume('ID')[1]
            if self.Peak in ['+', '-']:
                # Go for binop
                op = self.Consume(self.Peak)[1]
                b = self.Consume('ID')[1]
                a = self.find_val(a)
                ty = self.find_type(ty)
                b = self.find_val(b)
                ins = ir.Binop(a, op, b, name, ty)
            else:
                raise Exception()
        elif self.Peak == 'NUMBER':
            cn = self.Consume('NUMBER')[1]
            ty = self.find_type(ty)
            ins = ir.Const(cn, name, ty)
        else:
            raise Exception()
        return ins

    def parse_cjmp(self):
        self.Consume('ID', 'cjmp')
        a = self.Consume('ID')[1]
        op = self.Consume(self.Peak)[0]
        b = self.Consume('ID')[1]
        L1 = self.Consume('ID')[1]
        L2 = self.Consume('ID')[1]
        L1 = ir.Block(L1)
        L2 = ir.Block(L2)
        a = self.find_val(a)
        b = self.find_val(b)
        ins = ir.CJump(a, op, b, L1, L2)
        self.resolve_worklist.append((ins, (L1, L2)))
        return ins

    def parse_jmp(self):
        self.Consume('ID', 'jmp')
        L1 = self.Consume('ID')[1]
        L1 = ir.Block(L1)
        ins = ir.Jump(L1)
        self.resolve_worklist.append((ins, (L1,)))
        return ins

    def parse_return(self):
        self.Consume('ID', 'return')
        val = self.find_val(self.Consume('ID')[1])
        # TODO: what to do with return value?
        ins = ir.Terminator()
        return ins

    def parse_statement(self):
        self.Consume('SKIP2')
        if self.Peak == 'ID' and self.PeakVal == 'jmp':
            ins = self.parse_jmp()
        elif self.Peak == 'ID' and self.PeakVal == 'cjmp':
            ins = self.parse_cjmp()
        elif self.Peak == 'ID' and self.PeakVal == 'return':
            ins = self.parse_return()
        elif self.Peak == 'ID' and self.PeakVal == 'store':
            raise Exception()
        else:
            ins = self.parse_assignment()
            self.add_val(ins)
        self.Consume('eol')
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
        self.prepare()
        self.block = None
        self.m = None
        self.function = None

    def prepare(self):
        self.newBlock2 = NamedClassGenerator('block', ir.Block).gen
        self.block = None
        self.m = None
        self.function = None
        self.loc = None

    # Helpers:
    def setModule(self, m):
        self.m = m

    def new_function(self, name):
        f = ir.Function(name)
        self.m.add_function(f)
        return f

    def newBlock(self):
        """ Create a new block and add it to the current function """
        assert self.function is not None
        block = self.newBlock2()
        self.function.add_block(block)
        return block

    def setFunction(self, f):
        self.function = f
        self.block = f.entry if f else None

    def setBlock(self, block):
        self.block = block

    def setLoc(self, l):
        self.loc = l

    def emit(self, i):
        """ Append an instruction to the current block """
        assert isinstance(i, ir.Instruction), str(i)
        i.debugLoc = self.loc
        if self.block is None:
            raise Exception('No basic block')
        self.block.add_instruction(i)
        return i


class Verifier:
    """ Checks an ir module for correctness """
    def __init__(self):
        self.logger = logging.getLogger('verifier')

    def verify(self, module):
        """ Verifies a module for some sanity """
        self.logger.debug('Verifying {} ({})'.format(module, module.stats()))
        assert isinstance(module, ir.Module)
        for function in module.Functions:
            self.verify_function(function)

    def verify_function(self, function):
        """ Verify all blocks in the function """
        self.name_map = {}
        for block in function.blocks:
            self.verify_block_termination(block)

        # Verify predecessor and successor:
        for block in function.blocks:
            preds = set(b for b in function.blocks if block in b.Successors)
            assert preds == set(block.predecessors)

        # Now we can build a dominator tree
        function.cfg_info = CfgInfo(function)
        for block in function:
            assert block.function == function
            self.verify_block(block)

    def verify_block_termination(self, block):
        """ Verify that the block is terminated correctly """
        assert not block.empty
        assert block.last_instruction.IsTerminator
        for i in block.Instructions[:-1]:
            assert not isinstance(i, ir.LastStatement)

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
            assert value.dominates(instruction), \
                "{} does not dominate {}".format(value, instruction)
