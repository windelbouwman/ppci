""" Compile python code statically """


import argparse
from .base import base_parser, march_parser, out_parser, compile_parser
from .base import LogSetup, get_arch_from_args
from .. import api


parser = argparse.ArgumentParser(
    description=__doc__,
    parents=[base_parser, march_parser, out_parser, compile_parser])
parser.add_argument(
    'sources', metavar='source', help='source file', nargs='+',
    type=argparse.FileType('r'))


def pycompile(args=None):
    """ Compile python code statically """
    args = parser.parse_args(args)
    with LogSetup(args):
        march = get_arch_from_args(args)
        for source in args.sources:
            obj = api.pycompile(source, march)
            obj.save(args.output)


if __name__ == '__main__':
    pycompile()
