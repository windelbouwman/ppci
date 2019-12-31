""" C3 compiler.

Use this compiler to produce object files from c3 sources and c3
includes. C3 includes have the same format as c3 source files, but do not
result in any code.
"""


import argparse
from .base import base_parser, march_parser
from .compile_base import compile_parser, do_compile
from .base import LogSetup, get_arch_from_args
from .. import api


parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[base_parser, march_parser, compile_parser],
)
parser.add_argument(
    "-i",
    "--include",
    action="append",
    metavar="include",
    help="include file",
    default=[],
)
parser.add_argument("sources", metavar="source", help="source file", nargs="+")


def c3c(args=None):
    """ Run c3 compile task """
    args = parser.parse_args(args)
    with LogSetup(args) as log_setup:
        # Compile sources:
        march = get_arch_from_args(args)

        ir_module = api.c3_to_ir(
            args.sources, args.include, march, reporter=log_setup.reporter
        )

        do_compile([ir_module], march, log_setup.reporter, log_setup.args)


if __name__ == "__main__":
    c3c()
