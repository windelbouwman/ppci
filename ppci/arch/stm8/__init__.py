""" Stm8 support.

STM8 is an 8-bit processor, see also:

http://www.st.com/stm8

Implementation
~~~~~~~~~~~~~~

Since there are so few registers, one possible approach is to emulate
registers in the first 16 or 32 bytes of ram. We can then use these ram
locations as 'registers' and do register allocation and instruction
selection using these 'registers'. This way, we treat the stm8 as a risc
machine with many registers, while in reality it is not.


Calling conventions
~~~~~~~~~~~~~~~~~~~

There is not really a standard calling convention for the stm8 processor.

Since the stm8 has only few registers, a calling convention must place
most arguments on stack.

"""

from .arch import Stm8Arch

__all__ = ['Stm8Arch']
