""" Objdump utility to display the contents of object files. """


import argparse
import io
from .base import base_parser, LogSetup
from .. import api
from ..binutils.objectfile import ObjectFile, print_object


parser = argparse.ArgumentParser(
    description=__doc__, parents=[base_parser])
parser.add_argument(
    'obj', help='object file', type=argparse.FileType('r'))
parser.add_argument(
    '-d', '--disassemble', help='Disassemble contents', action='store_true',
    default=False)


def objdump(args=None):
    """ Dump info of an object file """
    args = parser.parse_args(args)
    with LogSetup(args):
        obj = ObjectFile.load(args.obj)
        args.obj.close()
        print_object(obj)
        if args.disassemble:
            for section in obj.sections:
                print(section.name)
                f = io.BytesIO(section.data)
                api.disasm(f, obj.arch)


if __name__ == '__main__':
    objdump()
