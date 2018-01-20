from sys import argv

from ppci.api import asm, cc, link, objcopy, get_arch
from ppci.binutils.objectfile import merge_memories
from ppci.lang.c import COptions
from ppci.utils.reporting import HtmlReportGenerator

with open('report.html', 'w') as f:
    arch = get_arch('riscv')
    o1 = asm("startdbg.s", arch)
    reporter = HtmlReportGenerator(f)
    srcs = ["./csrc/bsp.c", "./csrc/lib.c", "./csrc/gdbstub.c", "./csrc/" + argv[1] + "/main.c"]
    obj = []
    coptions = COptions()
    coptions.add_include_path('./csrc')
    for src in srcs:
        with open(src) as f:
            obj.append(cc(f, "riscv", coptions=coptions, debug=True, reporter=reporter))
    obj = link([o1] + obj, "firmware.mmap", use_runtime=True, reporter=reporter, debug=True)

    with open("firmware.oj", "w") as of:
        obj.save(of)

    objcopy(obj, "flash", "elf", "firmware.elf")
    objcopy(obj, "flash", "bin", "code.bin")
    objcopy(obj, "ram", "bin", "data.bin")
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
