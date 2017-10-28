"""
For a good list of op codes, checkout:

http://ref.x86asm.net/coder64.html

For an online assembler, checkout:

https://defuse.ca/online-x86-assembler.htm

Linux
~~~~~

For a good list of linux system calls, refer:

http://blog.rchapman.org/post/36801038863/linux-system-call-table-for-x86-64

.. autoclass:: ppci.arch.x86_64.X86_64Arch

"""


from .arch import X86_64Arch

__all__ = ['X86_64Arch']
