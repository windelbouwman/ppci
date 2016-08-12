#!/usr/bin/env python

import io
import unittest
from ppci.common import CompilerError, DiagnosticsManager
from ppci.binutils.assembler import AsmLexer, BaseAssembler
from ppci.binutils.objectfile import ObjectFile
from ppci.binutils.outstream import BinaryOutputStream
from ppci.arch.arch import Label
from ppci.api import link, get_arch
from ppci.binutils.layout import Layout
from util import gnu_assemble


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

    def test_lex_0(self):
        """ Check if the lexer is OK """
        asmline = 'mov rax, rbx '
        toks = ['ID', 'ID', ',', 'ID', 'EOF']
        self.do(asmline, toks)

    def test_lex_0b(self):
        """ Check if the lexer is OK """
        asmline = 'mov.y rax, rbx '
        toks = ['ID', '.', 'ID', 'ID', ',', 'ID', 'EOF']
        self.do(asmline, toks)

    def test_lex_1(self):
        """ Test if lexer correctly maps some tokens """
        asmline = 'lab1: mov rax, rbx '
        toks = ['ID', ':', 'ID', 'ID', ',', 'ID', 'EOF']
        self.do(asmline, toks)

    def test_lex_2(self):
        """ Test if lexer correctly maps some tokens """
        asmline = 'mov 3.13 0xC 13'
        toks = ['ID', 'REAL', 'NUMBER', 'NUMBER', 'EOF']
        self.do(asmline, toks)

    def test_invalid_token(self):
        """ Test if lexer fails on a token that is invalid """
        asmline = '0z4: mov rax, rbx $ '
        with self.assertRaises(CompilerError):
            self.do(asmline, [])


class OustreamTestCase(unittest.TestCase):
    def test_normal_use(self):
        arch = get_arch('example')
        obj = ObjectFile(arch)
        o = BinaryOutputStream(obj)
        o.select_section('.text')
        o.emit(Label('a'))
        self.assertSequenceEqual(bytes(), obj.get_section('.text').data)


class AssemblerTestCase(unittest.TestCase):
    def test_parse_failure(self):
        """ Check the error reporting of the assembler """
        arch = get_arch('example')
        obj = ObjectFile(arch)
        ostream = BinaryOutputStream(obj)
        ostream.select_section('code')
        diag = DiagnosticsManager()
        assembler = BaseAssembler()
        with self.assertRaises(CompilerError):
            assembler.assemble('abc def', ostream, diag)


class AsmTestCaseBase(unittest.TestCase):
    """ Base testcase for assembly """
    def setUp(self):
        self.source = io.StringIO()
        self.as_args = []
        arch = get_arch(self.march)
        self.obj = ObjectFile(arch)
        self.ostream = BinaryOutputStream(self.obj)
        self.ostream.select_section('code')
        self.diag = DiagnosticsManager()

        # Prep assembler!
        self.assembler = arch.assembler
        self.assembler.prepare()

    def feed(self, line):
        self.assembler.assemble(line, self.ostream, self.diag)
        print(line, file=self.source)

    def check(self, hexstr, layout=Layout()):
        self.assembler.flush()
        self.obj = link([self.obj], layout)
        data = bytes(self.obj.get_section('code').data)
        if hexstr is None:
            gnu_assemble(self.source.getvalue(), as_args=self.as_args)
            self.fail('Implement this test-case')
        else:
            self.assertSequenceEqual(bytes.fromhex(hexstr), data)


if __name__ == '__main__':
    unittest.main()
