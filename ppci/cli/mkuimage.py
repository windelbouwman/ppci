""" Uboot image creation utility.

Use this utility to create uboot bootable images.
"""


import argparse
from .base import base_parser, LogSetup
from ..format.uboot_image import write_uboot_image, OperatingSystem
from ..format.uboot_image import Architecture


parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[base_parser])
parser.add_argument(
    '--arch', choices=tuple(Architecture.__members__), required=True)
parser.add_argument(
    '--os', choices=tuple(OperatingSystem.__members__), required=True)
parser.add_argument(
    '--load_address', type=int, default=0,
    help='Address where the image must be loaded')
parser.add_argument(
    '--entry_point', type=int, default=0,
    help='Address where execution must start')
parser.add_argument('uimage', type=argparse.FileType('wb'))
parser.add_argument('binary', type=argparse.FileType('rb'))


def mkuimage(args=None):
    args = parser.parse_args(args)
    with LogSetup(args):
        os = OperatingSystem.__getattr__(args.os)
        arch = Architecture.__getattr__(args.arch)
        data = arch.uimage.read()
        write_uboot_image(
            args.uimage, data,
            load_address=args.load_address, entry_point=args.entry_point,
            os=os, arch=arch)


if __name__ == '__main__':
    mkuimage()
