import io
import unittest

from sample_helpers import add_samples, build

from util import has_iverilog, run_picorv32
from util import do_long_tests, do_iverilog, make_filename
from ppci.binutils.objectfile import merge_memories


@unittest.skipUnless(do_long_tests('riscv'), 'skipping slow tests')
@add_samples('simple', 'medium', '8bit', '32bit')
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
            base_filename, src, bsp_c3, startercode, self.march,
            self.opt_level, io.StringIO(self.arch_mmap),
            lang=lang, bin_format='bin', elf_format='elf', code_image='flash')

        flash = obj.get_image('flash')
        data = obj.get_image('ram')
        rom = merge_memories(flash, data, 'rom')
        rom_data = rom.data
        filewordsize = 0x8000
        datawordlen = len(rom_data) // 4

        mem_file = base_filename + '.mem'
        with open(mem_file, 'w') as f:
            for i in range(filewordsize):
                if (i < datawordlen):
                    w = rom_data[4 * i:4 * i + 4]
                    print(
                        '%02x%02x%02x%02x' % (w[3], w[2], w[1], w[0]),
                        file=f)
                else:
                    print('00000000', file=f)
        f.close()

        if has_iverilog() and do_iverilog():
            res = run_picorv32(mem_file)
            self.assertEqual(expected_output, res)


class TestSamplesOnRiscvC(TestSamplesOnRiscv):
    march = "riscv:rvc"
    
if __name__ == '__main__':
    unittest.main()  
