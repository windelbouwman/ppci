""" Disassembler utility. """


import argparse
from .base import base_parser, march_parser, get_arch_from_args, LogSetup
from .. import api


parser = argparse.ArgumentParser(
    description=__doc__, parents=[base_parser, march_parser])
parser.add_argument(
    'binfile', type=argparse.FileType('rb'),
    help='the source file to assemble')


def disasm(args=None):
    """ Run asm from command line """
    args = parser.parse_args(args)
    with LogSetup(args):
        # Assemble source:
        march = get_arch_from_args(args)
        api.disasm(args.binfile, march)


if __name__ == '__main__':
    disasm()
