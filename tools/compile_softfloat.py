
import os
from ppci.cli.cc import cc

home = os.environ['HOME']
riscv32_lcc_path = os.path.join(home, 'GIT', 'riscv32_lcc')
filename = os.path.join(
    riscv32_lcc_path, 'lcc', 'bin', 'libs', 'softfloat', 'softfloat.c')

# cc([filename, '-S', '-v', '-m', 'riscv'])
cc([
    filename, '-S', '-v',
    '-m', 'x86_64',
    # '-m', 'msp430',
    '--html-report', 'softfloat_x86.html'])
# cc([filename, '-S', '-v', '-m', 'msp430', '--html-report', 'softfloat.html'])
# cc([filename, '--ast', '-v'])
# cc([filename, '--ir', '-v'])
