""" A compiler for ARM, X86, MSP430, xtensa and more implemented in
pure Python.

Example usage:

>>> from ppci.arch.x86_64 import instructions, registers
>>> pop = instructions.Pop(registers.rbx)
>>> pop.encode()
b'['

"""

import sys

# Define version here. Used in docs, and setup script:
__version_info__ = (0, 5, 8)
__version__ = '.'.join(map(str, __version_info__))

# Show detailed warning about python2:
python2_message = """
!!!!!!!!!!!!!!!!!!!!!!!!!!! PYTHON VERSION ERROR !!!!!!!!!!!!!!!!!!!!!!!!!!!

Dear python user, it appears you tried to use PPCI with a python
version below 3. PPCI requires python 3 or higher to function properly.

Please refer install python 3 via either your packagemanager or via www.python.org

!!!!!!!!!!!!!!!!!!!!!!!!!!! PYTHON VERSION ERROR !!!!!!!!!!!!!!!!!!!!!!!!!!!

"""

if sys.version_info.major < 3:
    print(python2_message)
    sys.exit(1)


# Assert python version:
assert sys.version_info.major == 3, "Needs to be run in python version 3.x"
