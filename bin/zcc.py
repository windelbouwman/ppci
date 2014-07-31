#!/usr/bin/env python

"""
    Simple wrapper for the build command for commandline usage.
"""

import sys
from ppci import commands


if __name__ == '__main__':
    parser = commands.make_parser()
    arguments = parser.parse_args()
    sys.exit(commands.main(arguments))
