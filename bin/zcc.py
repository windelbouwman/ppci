#!/usr/bin/env python

"""
    Simple wrapper for the build command for commandline usage.
"""

import sys
from ppci import commands


if __name__ == '__main__':
    parser = commands.make_parser()
    arguments = parser.parse_args()
    if not arguments.command:
        parser.print_usage()
        sys.exit(1)
    sys.exit(commands.main(arguments))
