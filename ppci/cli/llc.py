""" LLVM static compiler. """


import argparse
from .base import base_parser, march_parser, out_parser, LogSetup
from .base import get_arch_from_args
from .. import api


parser = argparse.ArgumentParser(
    description=__doc__,
    parents=[base_parser, march_parser, out_parser])
parser.add_argument(
    'source', help='source file', type=argparse.FileType('r'))


def llc(args=None):
    """ Compile llvm ir code into machine code """
    args = parser.parse_args(args)
    with LogSetup(args):
        march = get_arch_from_args(args)
        src = args.source
        obj = api.llc(src, march)

        # Write object file to disk:
        obj.save(args.output)
        args.output.close()


if __name__ == '__main__':
    llc()
