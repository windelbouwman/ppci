import os
import argparse

from ppci.api import asm, c3c, link, objcopy, get_arch
from ppci.binutils.objectfile import merge_memories
from ppci.utils.reporting import HtmlReportGenerator

parser = argparse.ArgumentParser()
parser.add_argument('example', help='example name from the c3src directory')
parser.add_argument(
    '--debug', action='store_true', default=False,
    help='Enable debug code')
args = parser.parse_args()

with open("report.html", 'w') as f, HtmlReportGenerator(f) as reporter:
    arch = get_arch('riscv')
    if args.debug:
        obj1 = asm("startdbg.s", arch)
    else:
        obj1 = asm("start.s", arch)

    c3_sources = [
        os.path.join("c3src", "bsp.c3"), os.path.join("c3src", 'io.c3'),
        os.path.join("c3src", args.example, "main.c3")
        ]
    if args.debug:
        c3_sources.append(os.path.join('c3src', 'gdbstub.c3'))
        c3_sources.append(os.path.join('c3src', 'irq.c3'))

    obj2 = c3c(
        c3_sources,
        [], "riscv", reporter=reporter, debug=True,
        opt_level=2)
    obj = link(
        [obj1, obj2], "firmware.mmap", use_runtime=False,
        reporter=reporter, debug=True)

    with open("firmware.oj", "w") as of:
        obj.save(of)

    objcopy(obj, "flash", "bin", "code.bin")
    objcopy(obj, "ram", "bin", "data.bin")
    objcopy(obj, "flash", "elf", "firmware.elf")
    size = 0x2000
    cimg = obj.get_image('flash')
    dimg = obj.get_image('ram')
    img = merge_memories(cimg, dimg, 'img')
    imgdata = img.data

with open("firmware.hex", "w") as f:
    for i in range(size):
        if i < len(imgdata) // 4:
            w = imgdata[4 * i: 4 * i + 4]
            print("%02x%02x%02x%02x" % (w[3], w[2], w[1], w[0]), file=f)
        else:
            print("00000000", file=f)
