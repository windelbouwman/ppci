"""
Tests for the Program base class. Subclases should be tested in the tests
for the corresponding languages.
"""

import unittest

from ppci.programs import Program, get_program_classes, get_targets
from ppci import programs

main_classes = programs.SourceCodeProgram, programs.IntermediateProgram, programs.MachineProgram


class MyTest1Program(Program):
    
    def to_mytest2(self):
        return self._new('mytest2', [1, 2, 3])


class MyTest2Program(Program):
    
    def _get_report(self, html):
        return '<b>test</b> program' if html else 'test program' 
    
    def to_mytest1(self):
        return self._new('mytest1', [4, 5, 6])

    def to_nonexistent(self):
        return self._new('nonexistent', [4, 5, 6])
    
    def to_python(self):
        return self._new('python', ['pass'])


class ProgramTestCase(unittest.TestCase):
    
    def get_public_program_classes(self):
        for name in dir(programs):
            ob = getattr(programs, name)
            if isinstance(ob, type) and issubclass(ob, Program):
                if ob is not Program and ob not in main_classes:
                    yield ob
    
    def test_namespace1(self):
        """ Test that all public program classes are either sourcecode, ir or machinecode."""
        for cls in self.get_public_program_classes():
            assert issubclass(cls, main_classes), ob
    
    def test_namespace2(self):
        """ Test that at least all public classes are known by Program itself."""
        classes_that_program_knows = get_program_classes().values()
        for cls in self.get_public_program_classes():
            self.assertIn(cls, classes_that_program_knows)
    
    def test_compiler_methods(self):
        
        p1 = MyTest1Program()
        p2 = p1.to_mytest2()
        p3 = p2.to_mytest1()
        p4 = p2.to_python()
        
        self.assertIsInstance(p2, MyTest2Program)
        self.assertIsInstance(p3, MyTest1Program)
        self.assertIsInstance(p4, programs.PythonProgram)
        
        self.assertEqual(p1.items, ())
        self.assertEqual(p2.items, (1, 2, 3))
        self.assertEqual(p3.items, (4, 5, 6))

        with self.assertRaises(KeyError):
            p2.to_nonexistent()
    
    def test_chain_and_previous(self):
        
        p1 = MyTest1Program()
        p2 = p1.to_mytest2().to_python().to_wasm().to_ir()
        
        self.assertEqual(p2.chain, ('mytest1', 'mytest2', 'python', 'wasm', 'ir'))
        self.assertIs(p2.source, p1)
        self.assertEqual(p2.previous().language, 'wasm')
        self.assertEqual(p2.previous(1).language, 'wasm')
        self.assertEqual(p2.previous(3).language, 'mytest2')
        self.assertIs(p2.previous('python'), p2.previous(2))
        self.assertIs(p2.previous('mytest1'), p2.source)
    
    def test_get_targets(self):
        
        # get_targers works on classes
        self.assertEqual(get_targets(MyTest1Program), set(['mytest2']))
        self.assertEqual(get_targets(MyTest2Program), set(['mytest1', 'python']))  # not nonexistent
        
        # and on instances
        p1 = MyTest1Program()
        p2 = MyTest2Program()
        self.assertEqual(get_targets(p1), set(['mytest2']))
        self.assertEqual(get_targets(p2), set(['mytest1', 'python']))  # not nonexistent
        
        # and on strings
        self.assertEqual(get_targets('mytest1'), set(['mytest2']))
        self.assertEqual(get_targets('mytest2'), set(['mytest1', 'python']))  # not nonexistent
    
    def test_reporting(self):
        p1 = MyTest1Program()
        p2 = p1.to_mytest2()
        
        with self.assertRaises(NotImplementedError):
            p1.get_report()
        
        self.assertEqual(p2.get_report(), 'test program')
        self.assertEqual(p2.get_report(False), 'test program')
        self.assertEqual(p2.get_report(True), '<b>test</b> program')
    
    def test_mcp(self):
        return  # this needs networkx, so wont work on CI right now, plus its rather experimental
        p1 = MyTest1Program()
        p2 = p1.to('x86')
        self.assertIsInstance(p2, programs.X86Program)


if __name__ == '__main__':
    unittest.main(verbosity=1)
