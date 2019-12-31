""" Compile python code statically """


import argparse
from .base import base_parser, march_parser
from .compile_base import compile_parser, do_compile
from .base import LogSetup, get_arch_from_args
from .. import api


parser = argparse.ArgumentParser(
    description=__doc__, parents=[base_parser, march_parser, compile_parser]
)
parser.add_argument(
    "sources",
    metavar="source",
    help="source file",
    nargs="+",
    type=argparse.FileType("r"),
)


def pycompile(args=None):
    """ Compile python code statically """
    args = parser.parse_args(args)
    with LogSetup(args) as log_setup:
        march = get_arch_from_args(args)

        ir_modules = []
        for source in args.sources:
            ir_module = api.python_to_ir(source)
            ir_modules.append(ir_module)

        do_compile(ir_modules, march, log_setup.reporter, log_setup.args)


if __name__ == "__main__":
    pycompile()
