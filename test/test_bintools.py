import unittest
import io

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from ppci.arch.arm.arm_instructions import ArmToken
from ppci.binutils.objectfile import ObjectFile, serialize, deserialize, Image
from ppci.binutils.outstream import DummyOutputStream, TextOutputStream
from ppci.binutils.outstream import binary_and_logging_stream
from ppci.tasks import TaskError
from ppci.api import link, get_arch
from ppci.binutils import layout
from ppci.utils.elffile import ElfFile
from ppci.arch.example import Mov, R0, R1, ExampleArch


class TokenTestCase(unittest.TestCase):
    def test_set_bits(self):
        at = ArmToken()
        at[2:4] = 0b11
        self.assertEqual(0xc, at.bit_value)

    def test_set_bits2(self):
        at = ArmToken()
        at[4:8] = 0b1100
        self.assertEqual(0xc0, at.bit_value)


class OutstreamTestCase(unittest.TestCase):
    def test_dummy_stream(self):
        stream = DummyOutputStream()
        stream.select_section('code')
        stream.emit(Mov(R1, R0))

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_text_stream(self, mock_stdout):
        """ Test output to stdout """
        stream = TextOutputStream()
        stream.select_section('code')
        stream.emit(Mov(R1, R0))

    def test_binary_and_logstream(self):
        arch = ExampleArch()
        object1 = ObjectFile(arch)
        stream = binary_and_logging_stream(object1)
        stream.select_section('code')
        stream.emit(Mov(R1, R0))


class LinkerTestCase(unittest.TestCase):
    """ Test the behavior of the linker """
    def test_undefined_reference(self):
        arch = get_arch('arm')
        object1 = ObjectFile(arch)
        object1.get_section('.text', create=True)
        object1.gen_relocation('rel8', 'undef', offset=0, section='.text')
        object2 = ObjectFile(arch)
        with self.assertRaises(TaskError):
            link([object1, object2])

    def test_duplicate_symbol(self):
        arch = get_arch('arm')
        object1 = ObjectFile(arch)
        object1.get_section('.text', create=True)
        object1.add_symbol('a', 0, '.text')
        object2 = ObjectFile(arch)
        object2.get_section('.text', create=True)
        object2.add_symbol('a', 0, '.text')
        with self.assertRaises(TaskError):
            link([object1, object2])

    def test_rel8_relocation(self):
        arch = get_arch('arm')
        object1 = ObjectFile(arch)
        object1.get_section('.text', create=True).add_data(bytes([0]*100))
        object1.gen_relocation('rel8', 'a', offset=0, section='.text')
        object2 = ObjectFile(arch)
        object2.get_section('.text', create=True).add_data(bytes([0]*100))
        object2.add_symbol('a', 24, '.text')
        link([object1, object2])

    def test_symbol_values(self):
        """ Check if values are correctly resolved """
        arch = get_arch('arm')
        object1 = ObjectFile(arch)
        object1.get_section('.text', create=True).add_data(bytes([0]*108))
        object1.add_symbol('b', 24, '.text')
        object2 = ObjectFile(arch)
        object2.get_section('.text', create=True).add_data(bytes([0]*100))
        object2.add_symbol('a', 2, '.text')
        layout1 = layout.Layout()
        flash_mem = layout.Memory('flash')
        flash_mem.location = 0x0
        flash_mem.size = 0x1000
        flash_mem.add_input(layout.SymbolDefinition('code_start'))
        flash_mem.add_input(layout.Section('.text'))
        flash_mem.add_input(layout.SymbolDefinition('code_end'))
        layout1.add_memory(flash_mem)
        object3 = link([object1, object2], layout1)
        self.assertEqual(110, object3.get_symbol_value('a'))
        self.assertEqual(24, object3.get_symbol_value('b'))
        self.assertEqual(208, object3.get_section('.text').size)
        self.assertEqual(0, object3.get_symbol_value('code_start'))
        self.assertEqual(208, object3.get_symbol_value('code_end'))

    def test_memory_layout(self):
        spec = """
            MEMORY flash LOCATION=0x08000000 SIZE=0x3000 {
              DEFINESYMBOL(codestart)
              SECTION(code)
              DEFINESYMBOL(codeend)
            }
            MEMORY flash LOCATION=0x20000000 SIZE=0x3000 {
              SECTION(data)
            }
        """
        memory_layout = layout.Layout.load(io.StringIO(spec))
        arch = ExampleArch()
        object1 = ObjectFile(arch)
        object1.get_section('code', create=True).add_data(bytes([0]*108))
        object1.add_symbol('b', 24, 'code')
        object2 = ObjectFile(arch)
        object2.get_section('code', create=True).add_data(bytes([0]*100))
        object2.get_section('data', create=True).add_data(bytes([0]*100))
        object2.add_symbol('a', 2, 'data')
        object2.add_symbol('c', 2, 'code')
        object3 = link([object1, object2], memory_layout)
        self.assertEqual(0x20000000+2, object3.get_symbol_value('a'))
        self.assertEqual(0x08000000+24, object3.get_symbol_value('b'))
        self.assertEqual(0x08000000+110, object3.get_symbol_value('c'))
        self.assertEqual(208, object3.get_section('code').size)
        self.assertEqual(100, object3.get_section('data').size)
        self.assertEqual(0x08000000, object3.get_symbol_value('codestart'))
        self.assertEqual(0x08000000+208, object3.get_symbol_value('codeend'))

    def test_code_exceeds_memory(self):
        """ Check the error that is given when code exceeds memory size """
        arch = ExampleArch()
        layout2 = layout.Layout()
        m = layout.Memory('flash')
        m.location = 0x0
        m.size = 0x10
        m.add_input(layout.Section('code'))
        layout2.add_memory(m)
        object1 = ObjectFile(arch)
        object1.get_section('code', create=True).add_data(bytes([0]*22))
        with self.assertRaisesRegex(TaskError, 'exceeds'):
            link([object1], layout2)


class ObjectFileTestCase(unittest.TestCase):
    def make_twins(self):
        """ Make two object files that have equal contents """
        arch = get_arch('arm')
        object1 = ObjectFile(arch)
        object2 = ObjectFile(arch)
        object2.get_section('code', create=True).add_data(bytes(range(55)))
        object1.get_section('code', create=True).add_data(bytes(range(55)))
        object1.gen_relocation('rel8', 'A', offset=0x2, section='code')
        object2.gen_relocation('rel8', 'A', offset=0x2, section='code')
        object1.add_symbol('A2', 0x90, 'code')
        object2.add_symbol('A2', 0x90, 'code')
        object1.add_symbol('A3', 0x90, 'code')
        object2.add_symbol('A3', 0x90, 'code')
        object1.add_image(Image('a', 0x0))
        object1.get_image('a').add_section(object1.get_section('code'))
        object2.add_image(Image('a', 0x0))
        object2.get_image('a').add_section(object2.get_section('code'))
        return object1, object2

    def test_equality(self):
        object1, object2 = self.make_twins()
        self.assertEqual(object1, object2)

    def test_save_and_load(self):
        object1, object2 = self.make_twins()
        f1 = io.StringIO()
        object1.save(f1)
        f2 = io.StringIO(f1.getvalue())
        object3 = ObjectFile.load(f2)
        self.assertEqual(object3, object1)

    def test_serialization(self):
        object1, object2 = self.make_twins()
        object3 = deserialize(serialize(object1))
        self.assertEqual(object3, object1)

    def test_overlapping_sections(self):
        """ Check that overlapping sections are detected """
        obj = ObjectFile(get_arch('msp430'))
        obj.get_section('s1', create=True).add_data(bytes(range(100)))
        obj.get_section('s2', create=True).add_data(bytes(range(100)))
        obj.add_image(Image('x', 0))
        obj.get_image('x').add_section(obj.get_section('s1'))
        obj.get_image('x').add_section(obj.get_section('s2'))
        with self.assertRaisesRegex(ValueError, 'overlap'):
            obj.get_image('x').data


class ElfFileTestCase(unittest.TestCase):
    def test_save_load(self):
        arch = ExampleArch()
        ef1 = ElfFile()
        f = io.BytesIO()
        ef1.save(f, ObjectFile(arch))
        f2 = io.BytesIO(f.getvalue())
        ElfFile.load(f2)


class LayoutFileTestCase(unittest.TestCase):
    def test_layout(self):
        spec = """
            MEMORY flash LOCATION=0x1000 SIZE=0x3000 {
              SECTION(code)
              ALIGN(4)
              DEFINESYMBOL(x)
            }
        """
        layout1 = layout.Layout.load(io.StringIO(spec))
        layout2 = layout.Layout()
        m = layout.Memory('flash')
        m.location = 0x1000
        m.size = 0x3000
        m.add_input(layout.Section('code'))
        m.add_input(layout.Align(4))
        m.add_input(layout.SymbolDefinition('x'))
        layout2.add_memory(m)
        self.assertEqual(layout2, layout1)
        self.assertEqual(str(layout1), str(layout2))


if __name__ == '__main__':
    unittest.main()
