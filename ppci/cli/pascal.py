""" Pascal compiler.

Compile pascal programs.
"""


import argparse
import platform
from .base import base_parser, march_parser, out_parser, compile_parser
from .base import LogSetup, get_arch_from_args
from .. import api
from ..common import CompilerError


parser = argparse.ArgumentParser(
    description=__doc__,
    parents=[base_parser, march_parser, out_parser, compile_parser])
parser.add_argument(
    'sources', metavar='source', help='source file', nargs='+')


def pascal(args=None):
    """ Pascal compiler """
    args = parser.parse_args(args)
    with LogSetup(args) as log_setup:
        # Compile sources:
        march = get_arch_from_args(args)
        obj = api.pascal(args.sources, march, reporter=log_setup.reporter)

        if args.output:
            # Write object file to disk:
            obj.save(args.output)
            args.output.close()
        else:
            from .runtime import create_linux_exe
            my_system = platform.system()
            if my_system == 'Linux':
                entry_function_name = 'hello1_hello1_main'
                create_linux_exe(entry_function_name, 'w00t', obj)
            else:
                raise CompilerError('System %s not supported' % my_system)


if __name__ == '__main__':
    pascal()
