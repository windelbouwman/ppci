
if False:
    import sys
    from IPython.core import ultratb
    sys.excepthook = ultratb.FormattedTB(mode='Verbose', call_pdb=1)

import argparse
import logging
import os
import sys
from ppci import api
from ppci.common import CompilerError
from ppci.utils.reporting import html_reporter
from ppci.lang.c.options import COptions, coptions_parser
from ppci.binutils.objectfile import merge_memories 

this_dir = os.path.abspath(os.path.dirname(__file__))
libc_includes = os.path.join(this_dir, '..', '..', 'librt', 'libc')

parser = argparse.ArgumentParser(parents=[coptions_parser])
parser.add_argument('-v', action='count', default=0)
args = parser.parse_args()

coptions = COptions.from_args(args)
coptions.add_include_path(libc_includes)
report_html = os.path.join(this_dir, 'compilation_report.html')
if args.v > 0:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

arch = api.get_arch('riscv')

with html_reporter(report_html) as reporter:
    def cc(filename):
        logging.info('Compiling %s', filename)
        with open(os.path.join(this_dir, filename)) as f:
            try:
                obj = api.cc(f, arch, reporter=reporter, coptions=coptions)
                logging.info('Compiled %s into %s bytes', filename, obj.byte_size)
            except CompilerError as e:
                print(e)
                e.print()
                obj = None
        return obj

    file_list = ['xprintf.c', 'loader.c', 'ff.c', 'sdmm.c']
    objs = [cc(f) for f in file_list]
    objs = [api.asm("start.s", arch)] + objs
    print(objs)
    obj = api.link(objs, "firmware.mmap", use_runtime=True, reporter=reporter, debug=True)
    of = open("firmware.tlf", "w")
    obj.save(of)
    of.close()
    api.objcopy(obj, "flash", "bin", "code.bin")
    api.objcopy(obj, "ram", "bin", "data.bin") 
    cimg = obj.get_image('flash')
    dimg = obj.get_image('ram')
    img = merge_memories(cimg, dimg, 'img')
    imgdata = img.data
    f = open("firmware.hex", "w")
    size = 0x8000
    for i in range(size):
        if i < len(imgdata) // 4:
            w = imgdata[4 * i: 4 * i + 4]
            print("%02x%02x%02x%02x" % (w[3], w[2], w[1], w[0]), file=f)
        else:
            print("00000000", file=f)
    f.close() 
