#!/usr/bin/env python

import sys
import argparse
import logging

from ppci.buildfunctions import c3toir
import ppci.buildtasks  # Include not used, but it registers build tasks.
import ppci
from zcc import logLevel


def make_parser():
    parser = argparse.ArgumentParser(description='c3 Compiler')

    parser.add_argument('--log', help='Log level (INFO,DEBUG,[WARN])',
                        type=logLevel, default='INFO')

    parser.add_argument('--target', help='target machine', default="arm")
    parser.add_argument('-o', '--output', help='target machine',
        type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-i', '--include', action='append',
        help='include file', default=[])
    parser.add_argument('sources', metavar='source',
        help='source file', nargs='+')
    return parser


def main(args):
    # Configure some logging:
    logging.getLogger().setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(ppci.logformat))
    ch.setLevel(args.log)
    logging.getLogger().addHandler(ch)

    res = c3toir(args.sources, args.include, args.target)
    writer = ppci.irutils.Writer()
    for ir_module in res:
        writer.write(ir_module, args.output)

    logging.getLogger().removeHandler(ch)
    return res


if __name__ == '__main__':
    parser = make_parser()
    arguments = parser.parse_args()
    sys.exit(main(arguments))
