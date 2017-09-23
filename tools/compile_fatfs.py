
if False:
    import sys
    from IPython.core import ultratb
    sys.excepthook = ultratb.FormattedTB(mode='Verbose', call_pdb=1)

import argparse
import logging
import os
import sys
from ppci import api
from ppci.utils.reporting import HtmlReportGenerator

parser = argparse.ArgumentParser()
parser.add_argument('fatfs_path')
parser.add_argument('-v', action='count', default=0)
args = parser.parse_args()
fatfs_path = args.fatfs_path
report_html = os.path.join(fatfs_path, 'compilation_report.html')
if args.v > 0:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

arch = api.get_arch('riscv')

with open(report_html, 'w') as rf, HtmlReportGenerator(rf) as reporter:
    def cc(filename):
        logging.info('Compiling %s', filename)
        with open(os.path.join(fatfs_path, filename)) as f:
            obj = api.cc(f, arch, reporter=reporter)
        return obj

    file_list = ['loader.c', 'ff.c', 'sdmm.c']
    objs = [cc(f) for f in file_list]
    print(objs)
