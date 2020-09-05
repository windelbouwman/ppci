""" Takes a web assembly module and turns it into riscv code """
import logging
from ppci.api import asm, c3c, link, get_arch, wasmcompile
from ppci.binutils.objectfile import merge_memories
from ppci.utils.reporting import html_reporter


logging.basicConfig(level=logging.INFO)
arch = get_arch('riscv')
obj1 = asm("start.s", arch)

with html_reporter('report.html') as reporter:
    srcs = ['../src/wasm_fac/main.c3', '../../librt/io.c3', 'c3src/bsp.c3']
    obj2 = c3c(srcs, [], arch, reporter=reporter)
    with open('../src/wasm_fac/fact.wasm', 'rb') as f2:
        obj3 = wasmcompile(f2, arch)

    obj = link(
        [obj1, obj2, obj3], "firmware.mmap", use_runtime=True,
        reporter=reporter, debug=True)

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
