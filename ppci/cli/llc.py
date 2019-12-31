""" LLVM static compiler. """


import argparse
from .base import base_parser, march_parser, LogSetup
from .base import get_arch_from_args
from .compile_base import compile_parser, do_compile
from .. import api


parser = argparse.ArgumentParser(
    description=__doc__, parents=[base_parser, march_parser, compile_parser]
)
parser.add_argument("source", help="source file", type=argparse.FileType("r"))


def llc(args=None):
    """ Compile llvm ir code into machine code """
    args = parser.parse_args(args)
    with LogSetup(args) as log_setup:
        march = get_arch_from_args(args)
        ir_module = api.llvm_to_ir(args.source)
        do_compile([ir_module], march, log_setup.reporter, log_setup.args)


if __name__ == "__main__":
    llc()
