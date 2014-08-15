#!/usr/bin/env python

"""

"""

import argparse
from ppci.gen_sled import sled_main


def make_argument_parser():
    # Parse arguments:
    parser = argparse.ArgumentParser(description='sled generator')
    parser.add_argument('source', type=argparse.FileType('r'),
                        help='the spec file')
    return parser


if __name__ == '__main__':
    args = make_argument_parser().parse_args()
    sled_main(args)
