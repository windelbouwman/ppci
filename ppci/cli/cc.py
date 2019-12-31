""" C compiler.

Use this compiler to compile C source code to machine code for different
computer architectures.
"""


import argparse
from .base import base_parser, march_parser
from .compile_base import compile_parser, do_compile
from .base import LogSetup, get_arch_from_args
from .. import api
from ..lang.c import create_ast, CAstPrinter
from ..lang.c.options import COptions, coptions_parser


parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[base_parser, march_parser, compile_parser, coptions_parser],
)
parser.add_argument(
    "-E", action="store_true", default=False, help="Stop after preprocessing"
)
parser.add_argument(
    "-M",
    action="store_true",
    default=False,
    help="Instead of preprocessing, emit a makefile rule with dependencies",
)
parser.add_argument(
    "--ast",
    action="store_true",
    default=False,
    help="Stop parsing and output the C abstract syntax tree (ast)",
)
parser.add_argument(
    "-c", action="store_true", default=False, help="Compile, but do not link"
)
parser.add_argument(
    "sources",
    metavar="source",
    help="source file",
    nargs="+",
    type=argparse.FileType("r"),
)


def cc(args=None):
    """ Run c compile task """
    args = parser.parse_args(args)
    with LogSetup(args) as log_setup:
        # Compile sources:
        march = get_arch_from_args(args)
        coptions = COptions()
        coptions.process_args(args)

        if args.E:  # Only pre process
            with open(args.output, "w") as output:
                for src in args.sources:
                    api.preprocess(src, output, coptions)
        elif args.M:  # Emit a makefile dep line.
            dependencies = []
            for filename in dependencies:
                print(filename)
        elif args.ast:
            with open(args.output, "w") as output:
                printer = CAstPrinter(file=output)
                for src in args.sources:
                    # Stop after ast generation:
                    filename = src.name if hasattr(src, "name") else None
                    ast = create_ast(
                        src, march.info, filename=filename, coptions=coptions
                    )
                    printer.print(ast)
        else:
            ir_modules = []
            for src in args.sources:
                # Compile and optimize in any case:
                ir_module = api.c_to_ir(
                    src, march, coptions=coptions, reporter=log_setup.reporter
                )
                ir_modules.append(ir_module)

            do_compile(ir_modules, march, log_setup.reporter, log_setup.args)


if __name__ == "__main__":
    cc()
