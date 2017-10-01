""" Optimizer """


import argparse
from .base import base_parser, LogSetup
from .. import api, irutils


parser = argparse.ArgumentParser(
    description=__doc__, parents=[base_parser])
parser.add_argument(
    '-O', help='Optimization level', default=2, type=int)
parser.add_argument(
    'input', help='input file', type=argparse.FileType('r'))
parser.add_argument(
    'output', help='output file', type=argparse.FileType('w'))


def opt(args=None):
    """ Optimize a single IR-file """
    args = parser.parse_args(args)
    module = irutils.Reader().read(args.input)
    with LogSetup(args):
        api.optimize(module, level=args.O)
    irutils.Writer(file=args.output).write(module)


if __name__ == '__main__':
    opt()
