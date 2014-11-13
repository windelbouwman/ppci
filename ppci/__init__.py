# File to make this directory a package.

import sys
import os

version = '0.0.3'

# Assert python version:
if sys.version_info.major != 3:
   print("Needs to be run in python version 3.x")
   sys.exit(1)

from .common import SourceLocation, SourceRange, Token
from .common import CompilerError, DiagnosticsManager

logformat='%(asctime)s|%(levelname)s|%(name)s|%(message)s'

def same_dir(full_path, filename):
    return os.path.join(os.path.dirname(os.path.abspath(full_path)), filename)


def make_num(txt):
    if txt.startswith('0x'):
        return int(txt[2:], 16)
    else:
        return int(txt)

