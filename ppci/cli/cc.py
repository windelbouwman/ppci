""" C compiler.

Use this compiler to compile C source code to machine code for different
computer architectures.
"""


import argparse
import logging
from .base import base_parser, march_parser, out_parser, compile_parser
from .base import LogSetup, get_arch_from_args
from .. import api, irutils
from ..binutils.outstream import TextOutputStream
from ..lang.c import create_ast, CAstPrinter
from ..lang.c.options import COptions, coptions_parser
from ..wasm import ir_to_wasm


parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[
        base_parser, march_parser, out_parser, compile_parser,
        coptions_parser])
parser.add_argument(
    '-E', action='store_true', default=False,
    help="Stop after preprocessing")
parser.add_argument(
    '--ast', action='store_true', default=False,
    help="Stop parsing and output the C abstract syntax tree (ast)")
parser.add_argument(
    '-c', action="store_true", default=False,
    help="Compile, but do not link")
parser.add_argument(
    'sources', metavar='source', help='source file', nargs='+',
    type=argparse.FileType('r'))


def cc(args=None):
    """ Run c compile task """
    args = parser.parse_args(args)
    with LogSetup(args) as log_setup:
        # Compile sources:
        march = get_arch_from_args(args)
        coptions = COptions()
        coptions.process_args(args)

        for src in args.sources:
            if args.E:  # Only pre process
                api.preprocess(src, args.output, coptions)
            elif args.ast:
                # Stop after ast generation:
                filename = src.name if hasattr(src, 'name') else None
                ast = create_ast(
                    src, march.info, filename=filename, coptions=coptions)
                printer = CAstPrinter(file=args.output)
                printer.print(ast)
            else:
                # Compile and optimize in any case:
                ir_module = api.c_to_ir(
                    src, march, coptions=coptions, reporter=log_setup.reporter)

                # Optimize:
                api.optimize(
                    ir_module, level=args.O, reporter=log_setup.reporter)

                if args.ir:  # Stop after ir code generation
                    irutils.print_module(ir_module, file=args.output)
                elif args.wasm:  # Output web-assembly code
                    wasm_module = ir_to_wasm(ir_module)
                    wasm_module.to_file(args.output)
                elif args.S:  # Output assembly code
                    stream = TextOutputStream(
                        printer=march.asm_printer, f=args.output)
                    api.ir_to_stream(
                        ir_module, march, stream, reporter=log_setup.reporter)
                elif args.c:  # Compile only
                    obj = api.ir_to_object(
                        [ir_module], march,
                        reporter=log_setup.reporter)

                    # Write object file to disk:
                    obj.save(args.output)
                else:
                    obj = api.ir_to_object(
                        [ir_module], march,
                        reporter=log_setup.reporter)

                    # TODO: link objects together?
                    logging.warning('TODO: Linking with stdlibs')
                    obj.save(args.output)
                    # raise NotImplementedError('Linking not implemented')

        # Close output file:
        args.output.close()


if __name__ == '__main__':
    cc()
