
"""
    Some utilities for ir-code.
"""
import re
from . import ir

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
    def __init__(self, extra_indent=''):
        self.extra_indent = extra_indent

    def write(self, ir, f):
        """ Write ir-code to file f """
        print('{}{}'.format(self.extra_indent, ir), file=f)
        for v in ir.Variables:
            print('{}{}'.format(self.extra_indent, v), file=f)
        for function in ir.Functions:
            self.write_function(function, f)

    def write_function(self, fn, f):
        args = ','.join('i32 ' + str(a) for a in fn.arguments)
        print('{}function i32 {}({})'.format(self.extra_indent, fn.name, args), file=f)
        for bb in fn.Blocks:
            print('{} {}'.format(self.extra_indent, bb), file=f)
            for ins in bb.Instructions:
                print('{}  {}'.format(self.extra_indent, ins), file=f)


class IrParseException(Exception):
    pass


class Reader:
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

    def next_token(self):
        t = self.token
        if t[0] != 'eof':
            self.token = self.tokens.__next__()
        return t

    @property
    def Peak(self):
        return self.token[0]

    def Consume(self, typ):
        if self.Peak == typ:
            return self.next_token()
        else:
            raise IrParseException('Expected "{}" got "{}"'.format(typ, self.Peak))

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
                raise IrParseException('Expected function got {}'.format(self.Peak))
        return module

    def parse_function(self):
        self.Consume('function')
        self.parse_type()
        name = self.Consume('ID')[1]
        function = ir.Function(name)
        self.Consume('(')
        while self.Peak != ')':
            self.parse_type()
            self.Consume('ID')
            if self.Peak != ',':
                break
            else:
                self.Consume(',')
        self.Consume(')')
        self.Consume('eol')
        while self.Peak == 'SKIP1':
            function.add_block(self.parse_block())
        return function

    def parse_type(self):
        self.Consume('ID')

    def parse_block(self):
        self.Consume('SKIP1')
        name = self.Consume('ID')[1]
        block = ir.Block(name)
        self.Consume(':')
        self.Consume('eol')
        while self.Peak == 'SKIP2':
            self.parse_statement()
        return block

    def parse_statement(self):
        self.Consume('SKIP2')
        while self.Peak != 'eol':
            # raise NotImplementedError()
            self.next_token()
        self.Consume('eol')


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


class Builder:
    """ Base class for ir code generators """
    def __init__(self):
        self.prepare()

    def prepare(self):
        self.newBlock2 = NamedClassGenerator('block', ir.Block).gen
        self.bb = None
        self.m = None
        self.fn = None
        self.loc = None
        self.i = 0

    # Helpers:
    def setModule(self, m):
        self.m = m

    def new_function(self, name):
        f = ir.Function(name)
        self.m.add_function(f)
        return f

    def newBlock(self):
        assert self.fn
        b = self.newBlock2()
        b.function = self.fn
        return b

    def setFunction(self, f):
        self.fn = f
        self.bb = f.entry if f else None

    def setBlock(self, b):
        self.bb = b

    def setLoc(self, l):
        self.loc = l

    def unique_name(self, pfx):
        self.i += 1
        return pfx + str(self.i)

    def emit(self, i):
        assert isinstance(i, ir.Instruction), str(i)
        # TODO: unique names?
        if isinstance(i, ir.Value):
            i.name = self.unique_name(i.name)
        i.debugLoc = self.loc
        if not self.bb:
            raise Exception('No basic block')
        self.bb.addInstruction(i)
        return i


class Verifier:
    """ Checks an ir module for correctness """
    def verify(self, module):
        """ Verifies a module for some sanity """
        assert isinstance(module, ir.Module)
        for f in module.Functions:
            self.verify_function(f)

    def verify_function(self, function):
        for b in function.Blocks:
            self.verify_block_termination(b)

        # Now we can build a dominator tree
        for b in function.Blocks:
            self.verify_block(b)

    def verify_block_termination(self, block):
        assert not block.Empty
        assert block.LastInstruction.IsTerminator
        for i in block.Instructions[:-1]:
            assert not isinstance(i, ir.LastStatement)

    def verify_block(self, block):
        for instruction in block.Instructions:
            self.verify_instruction(instruction)

    def verify_instruction(self, instruction):
        pass
