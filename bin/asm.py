#!/usr/bin/env python

import argparse
from ppci.target.target_list import targets
from ppci.buildfunctions import assemble

if __name__ == '__main__':
    # When run as main file, try to grab command line arguments:
    parser = argparse.ArgumentParser(description="Assembler")
    parser.add_argument('sourcefile', type=argparse.FileType('r'),
        help='the source file to assemble')
    args = parser.parse_args()
    obj = assemble(args.sourcefile, targets['arm'])
