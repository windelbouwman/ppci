
import os
from ppci.commands import cc

home = os.environ['HOME']
riscv32_lcc_path = os.path.join(home, 'GIT', 'riscv32_lcc')
filename = os.path.join(
    riscv32_lcc_path, 'lcc', 'bin', 'libs', 'softfloat', 'softfloat.c')

cc([filename, '-S', '-v', '-m', 'riscv'])
# cc([filename, '--ast', '-v'])
# cc([filename, '--ir', '-v'])
