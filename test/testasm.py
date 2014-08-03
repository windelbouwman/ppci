#!/usr/bin/env python

import subprocess
import io
import unittest
from ppci import CompilerError
from ppci.assembler import AsmLexer
from ppci.objectfile import ObjectFile
from ppci.outstream import BinaryOutputStream
from ppci.target.basetarget import Label
from ppci.buildfunctions import link
from ppci.layout import Layout


def gnu_assemble(source, as_args=[], prefix='arm-none-eabi-'):
    """ Helper function to feed source through gnu assembling tools """
    prefix = 'arm-none-eabi-'
    gas = '{}as'.format(prefix)
    objdump = prefix + 'objdump'
    print('assembling...')
    p_as = subprocess.Popen([gas] + as_args, stdin=subprocess.PIPE)
    p_as.communicate(input=source.encode('ascii'))
    if p_as.returncode != 0:
        raise Exception('{}'.format(p_as.returncode))

    p_objdump = subprocess.Popen([objdump, '-d'], stdout=subprocess.PIPE)
    output = p_objdump.communicate()[0].decode('ascii')
    if p_objdump.returncode != 0:
        raise Exception('{}'.format(p_objdump.returncode))
    print(output)

    p_objdump = subprocess.Popen([objdump, '-s', '-j', '.text'],
                                 stdout=subprocess.PIPE)
    output = p_objdump.communicate()[0].decode('ascii')
    if p_objdump.returncode != 0:
        raise Exception('{}'.format(p_objdump.returncode))
    print(output)
    return output


class AssemblerLexingCase(unittest.TestCase):
    """ Tests the assemblers lexer """

    def setUp(self):
        self.lexer = AsmLexer([])

    def do(self, asmline, toks):
        output = []
        self.lexer.feed(asmline)
        while 'EOF' not in output:
            output.append(self.lexer.next_token().typ)
        self.assertSequenceEqual(toks, output)

    def testLex0(self):
        """ Check if the lexer is OK """
        asmline = 'mov rax, rbx '
        toks = ['ID', 'ID', ',', 'ID', 'EOF']
        self.do(asmline, toks)

    def testLex1(self):
        """ Test if lexer correctly maps some tokens """
        asmline = 'lab1: mov rax, rbx '
        toks = ['ID', ':', 'ID', 'ID', ',', 'ID', 'EOF']
        self.do(asmline, toks)

    def testLex2(self):
        """ Test if lexer correctly maps some tokens """
        asmline = 'mov 3.13 0xC 13'
        toks = ['ID', 'REAL', 'val5', 'val5', 'EOF']
        self.do(asmline, toks)

    def testLex3(self):
        """ Test if lexer fails on a token that is invalid """
        asmline = '0z4: mov rax, rbx $ '
        with self.assertRaises(CompilerError):
            self.do(asmline, [])


class OustreamTestCase(unittest.TestCase):
    def test1(self):
        obj = ObjectFile()
        o = BinaryOutputStream(obj)
        o.select_section('.text')
        o.emit(Label('a'))
        self.assertSequenceEqual(bytes(), obj.get_section('.text').data)


class AsmTestCaseBase(unittest.TestCase):
    """ Base testcase for assembly """
    def setUp(self):
        self.source = io.StringIO()
        self.as_args = []
        self.obj = ObjectFile()
        self.ostream = BinaryOutputStream(self.obj)
        self.ostream.select_section('code')

    def feed(self, line):
        self.assembler.assemble(line, self.ostream)
        print(line, file=self.source)

    def check(self, hexstr, layout=Layout()):
        self.assembler.flush()
        self.obj = link([self.obj], layout, self.target)
        data = bytes(self.obj.get_section('code').data)
        if hexstr is None:
            gnu_assemble(self.source.getvalue(), as_args=self.as_args)
        else:
            self.assertSequenceEqual(bytes.fromhex(hexstr), data)


if __name__ == '__main__':
    unittest.main()
