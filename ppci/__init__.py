"""
    File to make this directory a package.
"""

import sys

# Define version here. Used in docs, and setup script:
version = '0.0.4'

# Assert python version:
if sys.version_info.major != 3:
    print("Needs to be run in python version 3.x")
    sys.exit(1)
