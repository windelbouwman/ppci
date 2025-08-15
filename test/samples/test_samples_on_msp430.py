import io
import unittest

from .sample_helpers import add_samples, build
from ..helper_util import relpath
from ..helper_util import has_iverilog, run_msp430
from ..helper_util import do_long_tests, do_iverilog, make_filename
from ppci.binutils.objectfile import merge_memories


@unittest.skipUnless(do_long_tests("msp430"), "skipping slow tests")
@add_samples("simple", "8bit")
class TestSamplesOnMsp430(unittest.TestCase):
    opt_level = 0
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
        global main_main
        global bsp_exit

        reset_handler:
          mov.w #0x980, sp       ; setup stack pointer
          call #__init
          call #main_main        ; Enter main
          call #bsp_exit         ; Call exit cleaning
        end_inf_loop:
          jmp end_inf_loop

        global bsp_putc
        bsp_putc:
          mov.b r12, 0x67(r2)  ; write to uart0 tx buf
          ret

        global __data_load_start
        global __data_start
        global __data_end

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

    def do(self, src, expected_output, lang="c3"):
        base_filename = make_filename(self.id())
        bsp_c3 = relpath("..", "examples", "msp430", "bsp.c3")
        startercode = io.StringIO(self.startercode)
        obj = build(
            base_filename,
            src,
            bsp_c3,
            startercode,
            "msp430",
            self.opt_level,
            io.StringIO(self.arch_mmap),
            lang=lang,
        )

        flash = obj.get_image("flash")
        ivect = obj.get_image("vector16")
        rom = merge_memories(flash, ivect, "rom")
        rom_data = rom.data
        assert len(rom_data) % 2 == 0

        with open(base_filename + ".bin", "wb") as f:
            f.write(rom_data)

        mem_file = base_filename + ".mem"
        with open(mem_file, "w") as f:
            for i in range(len(rom_data) // 2):
                w = rom_data[2 * i : 2 * i + 2]
                print(f"{w[1]:02x}{w[0]:02x}", file=f)
        if has_iverilog() and do_iverilog():
            res = run_msp430(mem_file)
            self.assertEqual(expected_output, res)


class TestSamplesOnMsp430O2(TestSamplesOnMsp430):
    opt_level = 2
