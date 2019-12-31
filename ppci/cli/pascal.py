""" Pascal compiler.

Compile pascal programs.
"""


import argparse
import platform
from .base import base_parser, march_parser
from .compile_base import compile_parser, do_compile
from .base import LogSetup, get_arch_from_args
from .. import api
from ..common import CompilerError, get_file


parser = argparse.ArgumentParser(
    description=__doc__, parents=[base_parser, march_parser, compile_parser]
)
parser.add_argument("sources", metavar="source", help="source file", nargs="+")


def pascal(args=None):
    """ Pascal compiler """
    args = parser.parse_args(args)
    with LogSetup(args) as log_setup:
        # Compile sources:
        march = get_arch_from_args(args)
        sources = [get_file(fn) for fn in args.sources]
        if args.output:
            # Write object file to disk:
            ir_modules = api.pascal_to_ir(sources, march)
            do_compile(ir_modules, march, log_setup.reporter, log_setup.args)
        else:
            obj = api.pascal(sources, march, reporter=log_setup.reporter)
            from .runtime import create_linux_exe

            my_system = platform.system()
            if my_system == "Linux":
                entry_function_name = "hello1_hello1_main"
                create_linux_exe(entry_function_name, "w00t", obj)
            else:
                raise CompilerError("System %s not supported" % my_system)


if __name__ == "__main__":
    pascal()
