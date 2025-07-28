import io
import unittest

from .sample_helpers import add_samples, build
from ..helper_util import has_qemu, qemu, relpath
from ..helper_util import do_long_tests, make_filename


@unittest.skipUnless(do_long_tests("arm"), "skipping slow tests")
@add_samples("simple", "medium", "8bit", "32bit")
class TestSamplesOnVexpress(unittest.TestCase):
    maxDiff = None
    opt_level = 0
    march = "arm"
    startercode = """
    section reset
    mov sp, 0xF0000   ; setup stack pointer
    ; copy initial data
    global __data_load_start
    global __data_start
    global __data_end
    ldr r1, =__data_load_start
    ldr r2, =__data_start
    ldr r3, =__data_end
    __copy_loop:
    ldrb  r0, [r1, #0]
    strb r0, [r2, #0]
    add r1, r1, 1
    add r2, r2, 1
    cmp r2, r3
    blt __copy_loop

    global main_main
    global bsp_exit
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

    def do(self, src, expected_output, lang="c3"):
        # Construct binary file from snippet:
        bsp_c3 = relpath("..", "examples", "realview-pb-a8", "arch.c3")
        startercode = io.StringIO(self.startercode)
        base_filename = make_filename(self.id())
        build(
            base_filename,
            src,
            bsp_c3,
            startercode,
            self.march,
            self.opt_level,
            io.StringIO(self.arch_mmap),
            lang=lang,
            bin_format="bin",
        )
        sample_filename = base_filename + ".bin"

        # Run bin file in emulator:
        if has_qemu():
            res = qemu(
                [
                    "qemu-system-arm",
                    "--machine",
                    "realview-pb-a8",
                    "-m",
                    "16M",
                    "-nographic",
                    "-kernel",
                    sample_filename,
                ]
            )
            self.assertEqual(expected_output, res)


class TestSamplesOnVexpressO2(TestSamplesOnVexpress):
    opt_level = 2


@unittest.skipUnless(do_long_tests("arm"), "skipping slow tests")
@add_samples("simple", "medium", "8bit", "32bit")
class TestSamplesOnCortexM3O2(unittest.TestCase):
    """The lm3s811 has 64 k memory"""

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

    global main_main
    global bsp_exit

    BL main_main     ; Branch to sample start
    BL bsp_exit      ; do exit stuff
    local_loop:
    B local_loop

    global __data_load_start
    global __data_start
    global __data_end

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

    def do(self, src, expected_output, lang="c3"):
        # Construct binary file from snippet:
        bsp_c3 = relpath("..", "examples", "lm3s6965evb", "bare", "arch.c3")
        startercode = io.StringIO(self.startercode)
        base_filename = make_filename(self.id())
        build(
            base_filename,
            src,
            bsp_c3,
            startercode,
            self.march,
            self.opt_level,
            io.StringIO(self.arch_mmap),
            lang=lang,
            bin_format="bin",
        )
        sample_filename = base_filename + ".bin"

        # Run bin file in emulator:
        if has_qemu():
            res = qemu(
                [
                    "qemu-system-arm",
                    "-M",
                    "lm3s6965evb",
                    "-m",
                    "16M",
                    "-nographic",
                    "-kernel",
                    sample_filename,
                ]
            )
            # lm3s811evb
            self.assertEqual(expected_output, res)
