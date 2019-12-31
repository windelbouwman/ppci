""" Amiga hunk format.

See also:

https://github.com/cnvogelg/amitools/tree/master/amitools/binfmt/hunk

"""


from .reader import read_hunk
from .writer import write_hunk


__all__ = ["read_hunk", "write_hunk"]
