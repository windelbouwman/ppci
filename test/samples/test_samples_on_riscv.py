import io
import unittest

from sample_helpers import add_samples, build

from helper_util import has_iverilog, run_picorv32
from helper_util import do_long_tests, do_iverilog, make_filename
from ppci.binutils.objectfile import merge_memories
from helper_util import has_qemu, qemu


@unittest.skipUnless(do_long_tests("riscv"), "skipping slow tests")
@add_samples("simple", "medium", "8bit", "32bit")
class TestSamplesOnRiscv(unittest.TestCase):
    opt_level = 2
    maxDiff = None
    march = "riscv"
    startercode = """
    global main_main 
    global bsp_exit 
    LUI sp, 0x1F        ; setup stack pointer
    JAL ra, main_main    ; Branch to sample start LR
    JAL ra, bsp_exit     ; do exit stuff LR
    EBREAK
    """
    arch_mmap = """
    MEMORY flash LOCATION=0x0000 SIZE=0x4000 {
         SECTION(code)
    }
    MEMORY ram LOCATION=0x4000 SIZE=0x4000 {
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
        startercode = io.StringIO(self.startercode)
        base_filename = make_filename(self.id())
        bsp_c3 = io.StringIO(self.bsp_c3_src)

        obj = build(
            base_filename,
            src,
            bsp_c3,
            startercode,
            self.march,
            self.opt_level,
            io.StringIO(self.arch_mmap),
            lang=lang,
            bin_format="bin",
            elf_format="elf",
            code_image="flash",
        )

        flash = obj.get_image("flash")
        data = obj.get_image("ram")
        rom = merge_memories(flash, data, "rom")
        rom_data = rom.data
        filewordsize = 0x8000
        datawordlen = len(rom_data) // 4

        mem_file = base_filename + ".mem"
        with open(mem_file, "w") as f:
            for i in range(filewordsize):
                if i < datawordlen:
                    w = rom_data[4 * i : 4 * i + 4]
                    print(
                        "%02x%02x%02x%02x" % (w[3], w[2], w[1], w[0]), file=f
                    )
                else:
                    print("00000000", file=f)
        f.close()

        if has_iverilog() and do_iverilog():
            res = run_picorv32(mem_file)
            self.assertEqual(expected_output, res)


class TestSamplesOnRiscvC(TestSamplesOnRiscv):
    march = "riscv:rvc"


@unittest.skipUnless(do_long_tests("riscv"), "skipping slow tests")
@add_samples("simple")
class TestSamplesOnRiscvSiFiveU(unittest.TestCase):
    march = "riscv"
    opt_level = 0
    startercode = """
    global main_main 
    global bsp_exit 
    global _start
    
    section reset
    _start:
      ; Ensure only cpu 0 runs:
      csrr a0, mhartid
      xor a1, a1, a1
      bne a0, a1, limbo

      LUI sp, 0x80030      ; setup stack pointer to 0x80030000

      JAL ra, main_main    ; Branch to sample start LR
      JAL ra, bsp_exit     ; do exit stuff LR

    limbo:
      j limbo
    EBREAK
    """
    arch_mmap = """
    ENTRY(_start)

    MEMORY coderam LOCATION=0x80000000 SIZE=0x10000 {
        SECTION(reset)
        SECTION(code)
    }

    MEMORY dataram LOCATION=0x80010000 SIZE=0x10000 {
        SECTION(data)
    }
    """

    bsp_c3_src = """
    module bsp;

    public function void putc(byte c)
    {
        var int *UART0DR;
        UART0DR = cast<int*>(0x10010000);
        *UART0DR=c;
    }

    function void exit()
    {
        putc(4);
    }
    """

    def do(self, src, expected_output, lang="c3"):
        # Construct binary file from snippet:
        startercode = io.StringIO(self.startercode)
        base_filename = make_filename(self.id())
        bsp_c3 = io.StringIO(self.bsp_c3_src)

        build(
            base_filename,
            src,
            bsp_c3,
            startercode,
            self.march,
            self.opt_level,
            io.StringIO(self.arch_mmap),
            lang=lang,
            elf_format="elf",
        )

        base_filename = make_filename(self.id())

        elf_filename = base_filename + ".elf"

        if has_qemu():
            output = qemu(
                [
                    "qemu-system-riscv32",
                    "-nographic",
                    "-M",
                    "sifive_u",
                    "-bios",
                    elf_filename,
                ]
            )
            self.assertEqual(expected_output, output)


if __name__ == "__main__":
    unittest.main()
