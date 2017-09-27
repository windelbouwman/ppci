from sys import argv

from ppci.api import asm, c3c, link, objcopy, get_arch
from ppci.binutils.objectfile import merge_memories
from ppci.utils.reporting import HtmlReportGenerator

with open("report.html", 'w') as f:
    reporter = HtmlReportGenerator(f)
    arch = get_arch('riscv')
    o1 = asm("start.s", arch)
    o2 = c3c(["./c3src/bsp.c3", "./c3src/io.c3", "./c3src/" + argv[1] + "/main.c3"],
             [], "riscv", reporter=reporter, debug=True,
             opt_level=2)
    obj = link([o1, o2], "firmware.mmap", use_runtime=False, reporter=reporter, debug=True)

    of = open("firmware.tlf", "w")
    obj.save(of)
    of.close()

    objcopy(obj, "flash", "bin", "code.bin")
    objcopy(obj, "ram", "bin", "data.bin")
    objcopy(obj, "flash", "elf", "firmware.elf")
    size = 0x2000
    cimg = obj.get_image('flash')
    dimg = obj.get_image('ram')
    img = merge_memories(cimg, dimg, 'img')
    imgdata = img.data

    f = open("firmware.hex", "w")
    for i in range(size):
        if i < len(imgdata) // 4:
            w = imgdata[4 * i: 4 * i + 4]
            print("%02x%02x%02x%02x" % (w[3], w[2], w[1], w[0]), file=f)
        else:
            print("00000000", file=f)
    f.close()
