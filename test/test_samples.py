import unittest
import io
import logging
import re
import string
import os
import platform
import subprocess
from tempfile import mkstemp
from util import run_qemu, has_qemu, qemu, relpath, run_python, source_files
from util import has_iverilog, run_msp430, run_picorv32
from util import has_avr_emulator, run_avr
from util import do_long_tests
from ppci.api import asm, c3c, link, objcopy, bfcompile
from ppci.api import c3toir, bf2ir, ir_to_python, optimize
from ppci.utils.reporting import HtmlReportGenerator, complete_report
from ppci.binutils.objectfile import merge_memories


def make_filename(s):
    """ Remove all invalid characters from a string for a valid filename.
        And create a directory if none present.
    """
    output_dir = relpath('listings')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    valid_chars = string.ascii_letters + string.digits
    basename = ''.join(c for c in s if c in valid_chars)
    return os.path.join(output_dir, basename)


def enable_report_logger(filename):
    logging.getLogger().setLevel(logging.DEBUG)
    fh = logging.StreamHandler(filename)
    logging.getLogger().addHandler(fh)


def only_bf(txt):
    """ Strip a string from all characters, except brainfuck chars """
    return re.sub('[^\.,<>\+-\]\[]', '', txt)


def create_test_function(source, output):
    """ Create a test function for a source file """
    with open(source) as f:
        snippet = f.read()
    with open(output) as f:
        res = f.read()

    def tst_func(slf):
        slf.do(snippet, res)
    return tst_func


def add_samples(*folders):
    """ Create a decorator function that adds tests in the given folders """
    def deco(cls):
        for folder in folders:
            for source in source_files(
                    relpath('samples', folder), ('.c3', '.bf')):
                output = os.path.splitext(source)[0] + '.out'
                tf = create_test_function(source, output)
                basename = os.path.basename(source)
                func_name = 'test_' + os.path.splitext(basename)[0]
                assert not hasattr(cls, func_name)
                setattr(cls, func_name, tf)
        return cls
    return deco


@add_samples('32bit')
class I32Samples:
    """ 32-bit samples """
    def test_bug1(self):
        """ Strange bug was found here """
        snippet = """
         module main;
         var int x;
         function void main()
         {
            var int i = 0;
            if (x != i)
            {
            }
         }
        """
        res = ""
        self.do(snippet, res)

    def test_bug2(self):
        """ Test pointer arithmatic """
        snippet = """
         module main;
         var int* x;
         function void main()
         {
            var int i;
            x = 10;
            x += 15;
            i = cast<int>(x);
         }
        """
        res = ""
        self.do(snippet, res)
    @unittest.skip('too large codesize')
    def test_brain_fuck_hello_world(self):
        """ Test brainfuck hello world program """
        hello_world = """++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>
        .>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++."""
        self.do(hello_world, "Hello World!\n", lang='bf')

    @unittest.skip('too slow test')
    def test_brain_fuck_quine(self):
        """ A quine is a program that outputs itself! """
        quine = """>>+>>+++++>>++>>+++>>+>>++++++>>++>>++>>++>>+++++>>+>>++++>>
        +>>+++>>+>>+>>++>>++>>+>>+>>+>>+++>>+>>++++++>>+++++++++++++
        +++++++++++++++++++++++++++++++++++++++++++++++++>>+>>++>>++
        +++++>>+++++++++++++++++++>>++++>>+>>++>>+>>+++++>>+>>++++>>
        +>>+++>>+>>+++++++>>+>>++>>+>>++++++>>+>>+++>>+>>+++++>>+>>+
        +++>>+>>++++++>>+>>+++>>+>>+++++>>+>>++++>>+>>++>>+>>+>>+>>+
        ++>>+>>++++++>>+++>>++>>+>>++++++>>++>>+++>>+>>+++++>>+>>+++
        +>>+>>+++>>+>>+>>+>>++>>+>>+++++>>+>>+++>>+>>++++>>+>>++++++
        >>+>>++>>+>>+++++>>+>>++>>+>>++++++>>++>>+++>>+>>+++++>>+>>+
        +>>+++++++++++++++++++++++++++++++++++++++++++++++++>>+>>+>>
        +++>>+>>++++>>+>>++++++>>+++>>+++>>+>>++++++>>++++>>++>>+>>+
        ++++>>+>>++++>>+>>+++>>+>>+>>+>>++>>+>>+++++>>+>>+++>>+>>+++
        +>>+>>++++++>>+>>++>>+>>+++++>>+>>++>>+>>++++++>>++>>+++>>+>
        >+++++>>+>>++>>+++++++++++++++++++++++++++++++++++++++++++++
        ++++++++++++++++++++++>>+>>+>>+++>>+>>++++>>+>>++++++>>+++++
        >>++>>+>>++++++>>++++>>+++>>+>>+++++>>+>>++++>>+>>+++>>+>>+>
        >+>>++>>+>>+++++>>+>>+++>>+>>++++>>+>>++++++>>+>>++>>+>>++++
        +>>+>>++>>+>>++++++>>++>>+++>>+>>+++++>>+>>++>>+++++++++++++
        +++++++++++++++++++++++++++++++++++++++++++++++++++>>+>>+>>+
        ++>>+>>++++>>+>>++++++>>+++>>+++>>+>>++++++>>++++>>++>>+>>++
        +++>>+>>++++>>+>>+++>>+>>+>>+>>++>>+>>+++++>>+>>+++>>+>>++++
        >>+>>++++++>>+>>++>>+>>+++++>>+>>++>>+>>++++++>>++>>+++>>+>>
        +++++>>+>>++>>++++++++++++++++++++++++++++++++++++++++++++++
        ++>>+>>+>>+++>>+>>++++>>+>>++++++>>+++++>>++>>+>>++++++>>+++
        +>>+++>>+>>+++++>>+>>++++>>+>>+++>>+>>+>>+>>++>>+>>+++++>>+>
        >+++>>+>>++++>>+>>++++++>>+>>++>>+>>+++++>>+>>++>>+>>++++++>
        >++>>+++>>+>>+++++>>+>>++>>+++++++++++++++++++++++++++++++++
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        >>+>>+>>+++>>+>>++++>>+>>++++++>>+++>>+++>>+>>++++++>>++++>>
        ++>>+>>+++++>>+>>++++>>+>>+++>>+>>+>>+>>++>>+>>+++++>>+>>+++
        >>+>>++++>>+>>++++++>>+>>++>>+>>+++++>>+>>++>>+>>++++++>>++>
        >+++>>+>>+++++>>+>>++>>+++++++++++++++++++++++++++++++++++++
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++>>+
        >>+>>+++>>+>>++++>>+>>++++++>>+++++>>++>>+>>++++++>>++++>>++
        +>>+>>+++++>>+>>++++>>+>>+++>>+>>+>>+>>++>>+>>+++++>>+>>+++>
        >+>>++++>>+>>++++++>>+>>++>>+>>+++++>>+>>++>>+>>++++++>>++>>
        +++>>+>>+++++>>+>>++>>++++++++++++++++++++++++++++++++++++++
        ++++++++>>+>>+>>+++>>+>>++++>>+>>++++++>>+++>>+++>>+>>++++++
        >>++>>++>>++>>+++++>>+>>++++>>++>>++>>+>>+++++++>>++>>+++>>+
        >>++++++>>++++>>++>>+>>++++++[<<]>>[[-<+>>+<]+++++++++++++++
        +++++++++++++++++++++++++++++++++++++++++++++++..-----------
        -------->[-<.>]<[-]<[->+<]>>>]<<[-<+>[<-]>[>]<<[>+++++++++++
        ++++++++++++++++++++++++++++++++++++++<-]<<<]>>>>[-<+>[<-]>[
        >]<<[>++++++++++++++++++++++++++++++++++++++++++++++++++++++
        +++++++++++++<-]>>>>>]<<<<[-<+>[<-]>[>]<<[>+++++++++++++++++
        +++++++++++++++++++++++++++++++++++++++++++++++<-]<<<]>>>>[-
        <+>[<-]>[>]<<[>+++++++++++++++++++++++++++++++++++++++++++++
        +++<-]>>>>>]<<<<[-<+>[<-]>[>]<<[>+++++++++++++++++++++++++++
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        ++++++<-]<<<]>>>>[-<+>[<-]>[>]<<[>++++++++++++++++++++++++++
        ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        ++++++++<-]>>>>>]<<<<[-<+>[<-]>[>]<<[>++++++++++++++++++++++
        ++++++++++++++++++++++++<-]<<<]>>[[->>.<<]>>>>]"""
        self.do(quine, only_bf(quine), lang='bf')


def build(
        base_filename, src, bsp_c3, crt0_asm, march, opt_level, mmap,
        lang='c3', bin_format=None, elf_format=None, code_image='code'):
    """ Construct object file from source snippet """
    list_filename = base_filename + '.html'

    report_generator = HtmlReportGenerator(open(list_filename, 'w'))

    with complete_report(report_generator) as reporter:
        o1 = asm(crt0_asm, march)
        if lang == 'c3':
            srcs = [
                relpath('..', 'librt', 'io.c3'),
                bsp_c3,
                io.StringIO(src)]
            o2 = c3c(
                srcs, [], march, opt_level=opt_level,
                reporter=reporter, debug=True)
            objs = [o1, o2]
        elif lang == 'bf':
            o3 = bfcompile(src, march, reporter=reporter)
            o2 = c3c(
                [bsp_c3], [], march, reporter=reporter)
            objs = [o1, o2, o3]
        else:
            raise NotImplementedError('language not implemented')
        obj = link(
            objs, layout=mmap,
            use_runtime=True, reporter=reporter, debug=True)

    # Save object:
    obj_file = base_filename + '.oj'
    with open(obj_file, 'w') as f:
        obj.save(f)

    if elf_format:
        elf_filename = base_filename + '.' + elf_format
        objcopy(obj, code_image, elf_format, elf_filename)

    # Export code image to some format:
    if bin_format:
        sample_filename = base_filename + '.' + bin_format
        objcopy(obj, code_image, bin_format, sample_filename)

    return obj


class BuildMixin:
    opt_level = 0

    def build(self, src, lang='c3', bin_format=None,
    elf_format=None, code_image='code'):
        """ Construct object file from source snippet """
        base_filename = make_filename(self.id())

        startercode = io.StringIO(self.startercode)
        if hasattr(self, 'bsp_c3_src'):
            bsp_c3 = io.StringIO(getattr(self, 'bsp_c3_src'))
        else:
            bsp_c3 = self.bsp_c3

        obj = build(
            base_filename, src, bsp_c3, startercode, self.march, self.opt_level,
            io.StringIO(self.arch_mmap), lang=lang, bin_format=bin_format,
            elf_format=elf_format, code_image=code_image)

        return obj, base_filename


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
@add_samples('simple', 'medium', '8bit')
class TestSamplesOnVexpress(unittest.TestCase, I32Samples, BuildMixin):
    maxDiff = None
    march = "arm"
    startercode = """
    section reset
    mov sp, 0xF0000   ; setup stack pointer
    ; copy initial data
    ldr r1, =__data_load_start
    ldr r2, =__data_start
    ldr r3, =__data_end
    __copy_loop:
    ldrb  r0, [r1, 0]
    strb r0, [r2, 0]
    add r1, r1, 1
    add r2, r2, 1
    cmp r2, r3
    blt __copy_loop


    BL main_main      ; Branch to sample start
    BL bsp_exit       ; do exit stuff
    local_loop:
    B local_loop
    """
    arch_mmap = """
    MEMORY code LOCATION=0x10000 SIZE=0x10000 {
        SECTION(reset)
        SECTION(code)
        DEFINESYMBOL(__data_load_start)
        SECTIONDATA(data)
    }
    MEMORY ram LOCATION=0x20000 SIZE=0xA0000 {
        DEFINESYMBOL(__data_start)
        SECTION(data)
        DEFINESYMBOL(__data_end)
    }
    """
    bsp_c3 = relpath('..', 'examples', 'realview-pb-a8', 'arch.c3')

    def do(self, src, expected_output, lang="c3"):
        # Construct binary file from snippet:
        obj, base_filename = self.build(src, lang, bin_format='bin')
        sample_filename = base_filename + '.bin'

        # Run bin file in emulator:
        if has_qemu():
            res = run_qemu(sample_filename, machine='realview-pb-a8')
            self.assertEqual(expected_output, res)


class TestSamplesOnVexpressO2(TestSamplesOnVexpress):
    opt_level = 2


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
@add_samples('simple', 'medium', '8bit')
class TestSamplesOnRiscv(unittest.TestCase, I32Samples, BuildMixin):
    opt_level = 2
    maxDiff = None
    march = "riscv"
    startercode = """
    LUI sp, 0xF000        ; setup stack pointer
    JAL ra, main_main    ; Branch to sample start LR
    JAL ra, bsp_exit     ; do exit stuff LR
    SBREAK
    """
    arch_mmap = """
    MEMORY flash LOCATION=0x0000 SIZE=0x2000 {
         SECTION(code)
    }
    MEMORY ram LOCATION=0x2000 SIZE=0x2000 {
        SECTION(data)
    }
    """

    bsp_c3_src = """
    module bsp;
    type struct {
    int DR; // 0x0
    int SR; // 0x4
    int ACK; //0x8
    } uart_t;

    var uart_t* UART0;
    public function void putc(byte c)
    {
    var int *UART0DR;
    UART0DR = cast<int*>(0x20000000);
     *UART0DR=c;
     }

    function void exit()
    {
    }
    """

    def do(self, src, expected_output, lang="c3"):
        # Construct binary file from snippet:
        obj, base_filename = self.build(src, lang, bin_format='bin',
        elf_format='elf', code_image='flash')

        flash = obj.get_image('flash')
        data = obj.get_image('ram')
        rom = merge_memories(flash, data, 'rom')
        rom_data = rom.data
        filewordsize = 0x4000
        datawordlen = len(rom_data) // 4

        mem_file = base_filename + '.mem'
        with open(mem_file, 'w') as f:
            for i in range(filewordsize):
                if(i<datawordlen):
                    w = rom_data[4*i:4*i+4]
                    print('%02x%02x%02x%02x' % (w[3], w[2], w[1], w[0]), file=f)
                else:
                    print('00000000', file=f)
        f.close()

        if has_iverilog():
            res = run_picorv32(mem_file)
            self.assertEqual(expected_output, res)

class TestSamplesOnRiscvC(TestSamplesOnRiscv):
    march = "riscv:rvc"


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
@add_samples('simple', 'medium', '8bit')
class TestSamplesOnCortexM3O2(unittest.TestCase, I32Samples, BuildMixin):
    """ The lm3s811 has 64 k memory """

    opt_level = 2
    march = "arm:thumb"
    startercode = """
    section reset
    dd 0x2000f000
    dd 0x00000009

    ; copy initial data
    ldr r1, __data_load_start_value
    ldr r2, __data_start_value
    ldr r3, __data_end_value
    __copy_loop:
    ldrb  r0, [r1, 0]
    strb r0, [r2, 0]
    add r1, r1, 1
    add r2, r2, 1
    cmp r2, r3
    blt __copy_loop

    BL main_main     ; Branch to sample start
    BL bsp_exit      ; do exit stuff
    local_loop:
    B local_loop

    __data_load_start_value:
    dcd =__data_load_start
    __data_start_value:
    dcd =__data_start
    __data_end_value:
    dcd =__data_end
    """
    arch_mmap = """
    MEMORY code LOCATION=0x0 SIZE=0x10000 {
        SECTION(reset)
        ALIGN(4)
        SECTION(code)
        DEFINESYMBOL(__data_load_start)
        SECTIONDATA(data)
    }
    MEMORY ram LOCATION=0x20000000 SIZE=0xA000 {
        DEFINESYMBOL(__data_start)
        SECTION(data)
        DEFINESYMBOL(__data_end)
    }
    """
    bsp_c3 = relpath('..', 'examples', 'lm3s6965evb', 'bare', 'arch.c3')

    def do(self, src, expected_output, lang="c3"):
        # Construct binary file from snippet:
        obj, base_filename = self.build(src, lang, bin_format='bin')
        sample_filename = base_filename + '.bin'

        # Run bin file in emulator:
        if has_qemu():
            res = run_qemu(sample_filename, machine='lm3s6965evb')
            # lm3s811evb
            self.assertEqual(expected_output, res)


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
@add_samples('simple', 'medium', '8bit', 'fp', 'double')
class TestSamplesOnPython(unittest.TestCase, I32Samples):
    opt_level = 0

    def do(self, src, expected_output, lang='c3'):
        base_filename = make_filename(self.id())
        sample_filename = base_filename + '.py'
        list_filename = base_filename + '.html'

        report_generator = HtmlReportGenerator(open(list_filename, 'w'))
        bsp = io.StringIO("""
           module bsp;
           public function void putc(byte c);
           // var int global_tick; """)
        with complete_report(report_generator) as reporter:
            if lang == 'c3':
                ir_modules, debug_info = c3toir([
                    relpath('..', 'librt', 'io.c3'), bsp,
                    io.StringIO(src)], [], "arm", reporter=reporter)
            elif lang == 'bf':
                ir_modules = [bf2ir(src, 'arm')]

            for ir_module in ir_modules:
                optimize(ir_module, level=self.opt_level, reporter=reporter)

            with open(sample_filename, 'w') as f:
                ir_to_python(ir_modules, f, reporter=reporter)

                # Add glue:
                print('', file=f)
                print('def bsp_putc(c):', file=f)
                print('    print(chr(c), end="")', file=f)
                print('main_main()', file=f)

        res = run_python(sample_filename)
        self.assertEqual(expected_output, res)


class TestSamplesOnPythonO2(TestSamplesOnPython):
    opt_level = 2


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
@add_samples('simple', '8bit')
class TestSamplesOnMsp430O2(unittest.TestCase, BuildMixin):
    opt_level = 2
    march = "msp430"
    startercode = """
      section reset_vector
        dw 0 ; 0
        dw 0 ; 1
        dw 0 ; 2
        dw 0 ; 3
        dw 0 ; 4
        dw 0 ; 5
        dw 0 ; 6
        dw 0 ; 7
        dw 0 ; 8
        dw 0 ; 9
        dw 0 ; 10
        dw 0 ; 11
        dw 0 ; 12
        dw 0 ; 13
        dw 0 ; 14
        dw reset_handler ; 15 = reset

      section code
        reset_handler:
          mov.w #0x980, sp       ; setup stack pointer
          call #__init
          call #main_main        ; Enter main
          call #bsp_exit         ; Call exit cleaning
        end_inf_loop:
          jmp end_inf_loop

        bsp_putc:
          mov.b r12, 0x67(r2)  ; write to uart0 tx buf
          ret

        __init:
          mov.w #__data_load_start, r11
          mov.w #__data_start, r12
          mov.w #__data_end, r13
          cmp.w r12, r13
          jz __init_done
       __init_loop:
          mov.b @r11+, 0(r12)
          add.w #1, r12
          cmp.w r12, r13
          jne __init_loop
        __init_done:
          ret
    """
    arch_mmap = """
        MEMORY flash LOCATION=0xf000 SIZE=0xfe0 {
            SECTION(code)
            DEFINESYMBOL(__data_load_start)
            SECTIONDATA(data)
        }
        MEMORY vector16 LOCATION=0xffe0 SIZE=0x20 { SECTION(reset_vector) }
        MEMORY ram LOCATION=0x200 SIZE=0x800 {
            DEFINESYMBOL(__data_start)
            SECTION(data)
            DEFINESYMBOL(__data_end)
        }
    """
    bsp_c3 = relpath('..', 'examples', 'msp430', 'bsp.c3')

    def do(self, src, expected_output, lang='c3'):
        obj, base_filename = self.build(src, lang)
        # TODO
        flash = obj.get_image('flash')
        ivect = obj.get_image('vector16')
        rom = merge_memories(flash, ivect, 'rom')
        rom_data = rom.data
        assert len(rom_data) % 2 == 0

        with open(base_filename + '.bin', 'wb') as f:
            f.write(rom_data)

        mem_file = base_filename + '.mem'
        with open(mem_file, 'w') as f:
            for i in range(len(rom_data) // 2):
                w = rom_data[2*i:2*i+2]
                print('%02x%02x' % (w[1], w[0]), file=f)
        if has_iverilog():
            res = run_msp430(mem_file)
            self.assertEqual(expected_output, res)


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
@add_samples('8bit', 'simple')
class TestSamplesOnAvr(unittest.TestCase):
    march = "avr"
    opt_level = 0

    def do(self, src, expected_output, lang='c3'):
        base_filename = make_filename(self.id())
        bsp_c3 = relpath('..', 'examples', 'avr', 'bsp.c3')
        crt0 = relpath('..', 'examples', 'avr', 'glue.asm')
        mmap = relpath('..', 'examples', 'avr', 'avr.mmap')
        build(
            base_filename, src, bsp_c3, crt0, self.march, self.opt_level,
            mmap, lang=lang, bin_format='hex', code_image='flash')
        hexfile = base_filename + '.hex'
        print(hexfile)
        if has_avr_emulator():
            res = run_avr(hexfile)
            self.assertEqual(expected_output, res)


# Avr Only works with optimization enabled...
class TestSamplesOnAvrO2(TestSamplesOnAvr):
    opt_level = 2


@unittest.skip('TODO')
@add_samples('8bit')
class TestSamplesOnStm8(unittest.TestCase):
    march = "stm8"
    opt_level = 0

    def do(self, src, expected_output, lang='c3'):
        base_filename = make_filename(self.id())
        bsp_c3 = relpath('..', 'examples', 'stm8', 'bsp.c3')
        crt0 = relpath('..', 'examples', 'stm8', 'start.asm')
        mmap = relpath('..', 'examples', 'avr', 'avr.mmap')
        build(
            base_filename, src, bsp_c3, crt0, self.march, self.opt_level,
            mmap, lang=lang, bin_format='hex', code_image='flash')


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
@add_samples('simple')
class TestSamplesOnXtensa(unittest.TestCase):
    march = "xtensa"
    opt_level = 0

    def do(self, src, expected_output, lang='c3'):
        base_filename = make_filename(self.id())
        bsp_c3 = relpath('..', 'examples', 'xtensa', 'bsp.c3')
        crt0 = relpath('..', 'examples', 'xtensa', 'glue.asm')
        mmap = relpath('..', 'examples', 'xtensa', 'layout.mmp')
        build(
            base_filename, src, bsp_c3, crt0, self.march, self.opt_level,
            mmap, lang=lang, bin_format='bin', code_image='flash')
        binfile = base_filename + '.bin'
        img_filename = base_filename + '.img'
        self.make_image(binfile, img_filename)
        if has_qemu():
            output = qemu([
                'qemu-system-xtensa', '-nographic',
                '-M', 'lx60', '-m', '16',
                '-pflash', img_filename])
            self.assertEqual(expected_output, output)

    def make_image(self, bin_filename, image_filename, imagemb=4):
        with open(bin_filename, 'rb') as f:
            hello_bin = f.read()

        flash_size = imagemb * 1024 * 1024

        with open(image_filename, 'wb') as f:
            f.write(hello_bin)
            padding = flash_size - len(hello_bin)
            f.write(bytes(padding))


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
@add_samples('simple', 'medium', '8bit', 'fp', 'double')
class TestSamplesOnX86Linux(unittest.TestCase, BuildMixin):
    march = "x86_64"
    startercode = """
    section reset

    start:
        call main_main
        call bsp_exit

    bsp_putc:
            mov [0x20000000], rdi ; store char passed in rdi

            mov rax, 1 ; 1=sys_write
            mov rdi, 1 ; file descriptor
            mov rsi, char_to_print ; char* buf
            mov rdx, 1 ; count
            syscall
            ret

    bsp_exit:
            mov rax, 60
            mov rdi, 0
            syscall
            ret

    section data
        char_to_print:
        dd 0
        dd 0
    """
    arch_mmap = """
    MEMORY code LOCATION=0x40000 SIZE=0x10000 {
        SECTION(reset)
        ALIGN(4)
        SECTION(code)
    }
    MEMORY ram LOCATION=0x20000000 SIZE=0xA000 {
        SECTION(data)
    }
    """
    bsp_c3_src = """
    module bsp;
    public function void putc(byte c);
    // function void exit();
    """

    def do(self, src, expected_output, lang='c3'):
        obj, base_filename = self.build(src, lang, bin_format='elf')
        exe = base_filename + '.elf'

        if has_linux():
            if hasattr(subprocess, 'TimeoutExpired'):
                res = subprocess.check_output(exe, timeout=10)
            else:
                res = subprocess.check_output(exe)
            res = res.decode('ascii')
            self.assertEqual(expected_output, res)


class TestSamplesOnX86LinuxO2(TestSamplesOnX86Linux):
    opt_level = 2


def has_linux():
    return platform.machine() == 'x86_64' and platform.system() == 'Linux'


@unittest.skipIf(not has_linux(), 'no 64 bit linux found')
class LinuxTests(unittest.TestCase):
    """ Run tests against the linux syscall api """
    def test_exit42(self):
        """
            ; exit with code 42:
            ; syscall 60 = exit, rax is first argument, rdi second
        """
        src = io.StringIO("""
            section code
            mov rax, 60
            mov rdi, 42
            syscall
            """)
        mmap = """
        MEMORY code LOCATION=0x40000 SIZE=0x10000 {
            SECTION(code)
        }
        """
        obj = asm(src, 'x86_64')
        handle, exe = mkstemp()
        os.close(handle)
        obj2 = link([obj], layout=io.StringIO(mmap))
        objcopy(obj2, 'prog', 'elf', exe)
        if hasattr(subprocess, 'TimeoutExpired'):
            returncode = subprocess.call(exe, timeout=10)
        else:
            returncode = subprocess.call(exe)
        self.assertEqual(42, returncode)


if __name__ == '__main__':
    with open('sample_report.log', 'w') as report_file:
        enable_report_logger(report_file)
        unittest.main()
