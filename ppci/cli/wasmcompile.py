""" Static web assembly compiler.

This command line tool takes web assembly to native code.
"""


import argparse
from .base import base_parser, march_parser, out_parser, compile_parser
from .base import LogSetup, get_arch_from_args
from .. import api
from ..binutils.outstream import TextOutputStream
from ..wasm import read_wasm, wasm_to_ir


parser = argparse.ArgumentParser(
    description=__doc__,
    parents=[base_parser, march_parser, out_parser, compile_parser])
parser.add_argument(
    'wasm', metavar='wasm file', type=argparse.FileType('rb'),
    help='wasm file to compile')


def wasmcompile(args=None):
    """ Compile wasm to native code """
    args = parser.parse_args(args)
    with LogSetup(args) as log_setup:
        march = get_arch_from_args(args)
        wasm_module = read_wasm(args.wasm)
        ir_module = wasm_to_ir(
            wasm_module,
            march.info.get_type_info('ptr'),
            reporter=log_setup.reporter)

        # Optimize:
        api.optimize(ir_module, level=args.O, reporter=log_setup.reporter)

        if args.S:
            stream = TextOutputStream(
                printer=march.asm_printer, f=args.output)
            api.ir_to_stream(
                ir_module, march, stream, reporter=log_setup.reporter)
        else:
            obj = api.ir_to_object(
                [ir_module], march,
                reporter=log_setup.reporter)

            # Write object file to disk:
            obj.save(args.output)
        args.output.close()


if __name__ == '__main__':
    wasmcompile()
