
import os
from ppci.cli.cc import cc

home = os.environ['HOME']
riscv32_lcc_path = os.path.join(home, 'GIT', 'riscv32_lcc')
filename = os.path.join(
    riscv32_lcc_path, 'lcc', 'bin', 'libs', 'softfloat', 'softfloat.c')

# cc([filename, '-S', '-v', '-m', 'riscv'])
# march = 'riscv'
# march = 'arm'
# march = 'xtensa'
march = 'x86_64'
# march = 'msp430'
obj_filename = 'softfloat_{}.oj'.format(march)
cc([
    filename, '-S', '-v',
    '-m', march, '-o', obj_filename,
    '--html-report', 'softfloat_{}_report.html'.format(march)])
# cc([filename, '-S', '-v', '-m', 'msp430', '--html-report', 'softfloat_report.html'])
# cc([filename, '--ast', '-v'])
# cc([filename, '--ir', '-v'])
