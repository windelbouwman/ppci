""" Linker.

Use the linker to combine several object files and a memory layout
to produce another resulting object file with images.
"""

import argparse
from .base import base_parser, out_parser, LogSetup
from .. import api


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=__doc__,
    parents=[base_parser, out_parser],
)
parser.add_argument(
    "obj", type=argparse.FileType("r"), nargs="+", help="the object to link"
)
parser.add_argument(
    "--library",
    help="Add library to use when searching for symbols.",
    type=argparse.FileType("r"),
    action='append',
    default=[],
    metavar="library-filename",
)
parser.add_argument(
    "--layout",
    "-L",
    help="memory layout",
    default=None,
    type=argparse.FileType("r"),
    metavar="layout-file",
)
parser.add_argument(
    "-g", help="retain debug information", action="store_true", default=False
)


def link(args=None):
    """ Run linker from command line """
    args = parser.parse_args(args)
    with LogSetup(args):
        print(args.library)
        obj = api.link(args.obj, layout=args.layout, debug=args.g)
        with open(args.output, "w") as output:
            obj.save(output)


if __name__ == "__main__":
    link()
