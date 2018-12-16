from sys import argv
import os
from glob import glob
from ppci.api import asm, cc, link, objcopy, get_arch
from ppci.binutils.objectfile import merge_memories
from ppci.lang.c import COptions
from ppci.utils.reporting import HtmlReportGenerator

def get_sources(folder, extension):
    resfiles = []
    resdirs = []
    for x in os.walk(folder):    
        for y in glob(os.path.join(x[0], extension)):
            resfiles.append(y)
        resdirs.append(x[0])
    return((resdirs, resfiles))


with open('report.html', 'w') as f:
    arch = get_arch('riscv')
    o1 = asm("start.s", arch)
    o2 = asm("nosportasm.s", arch)
    reporter = HtmlReportGenerator(f)
    path = os.path.join('.','csrc',argv[1])
    dirs, srcs = get_sources(path, '*.c')
    #srcs += [os.path.join('.','csrc','bsp.c')] + [os.path.join('.','csrc','lib.c')]
    dirs += [os.path.join('.','csrc')]
    obj = []
    coptions = COptions()
    for dir in dirs:
        coptions.add_include_path(dir)
    for src in srcs:
        with open(src) as f:
            obj.append(cc(f, "riscv", coptions=coptions, debug=True, reporter=reporter))
    obj = link([o1,o2] + obj, "firmware.mmap", use_runtime=True, reporter=reporter, debug=True)

    with open("firmware.oj", "w") as of:
        obj.save(of)

    objcopy(obj, "flash", "elf", "firmware.elf")
    objcopy(obj, "flash", "bin", "code.bin")
    objcopy(obj, "ram", "bin", "data.bin")
    size = 0x8000
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
