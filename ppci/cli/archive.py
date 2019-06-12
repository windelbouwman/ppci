""" Archive manager.

Create or update an archive. Or extract object files from the archive.
"""

import argparse
from .base import base_parser, LogSetup
from .. import api
from ..binutils.objectfile import get_object
from ..binutils.archive import get_archive


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=__doc__,
    parents=[base_parser],
)
subparsers = parser.add_subparsers(dest="command", required=True)
create_parser = subparsers.add_parser("create", help="create new archive")
create_parser.add_argument(
    "archive", type=argparse.FileType("w"), help="Archive filename."
)
create_parser.add_argument(
    "obj", type=argparse.FileType("r"), nargs="*", help="the object to link"
)
display_parser = subparsers.add_parser(
    "display", help="display contents of an archive."
)
display_parser.add_argument(
    "archive", type=argparse.FileType("r"), help="Archive filename."
)


def archive(args=None):
    """ Run archive from command line """
    args = parser.parse_args(args)
    with LogSetup(args):
        if args.command == "create":
            objects = [get_object(obj) for obj in args.obj]
            lib = api.archive(objects)
            lib.save(args.archive)
        elif args.command == "display":
            lib = get_archive(args.archive)
            for obj in lib:
                print(obj)
                for symbol in obj.symbols:
                    print("  ", symbol)
        else:  # pragma: no cover
            raise NotImplementedError(args.command)


if __name__ == "__main__":
    archive()
