""" This module contains shared code for backend options.

"""

import argparse
import logging
from .. import api, irutils
from ..binutils.outstream import TextOutputStream
from .base import out_parser
from ..wasm import ir_to_wasm
from ..irutils.instrument import add_tracer


compile_parser = argparse.ArgumentParser(add_help=False, parents=[out_parser])
compile_parser.add_argument(
    "-g", help="create debug information", action="store_true", default=False
)
compile_parser.add_argument(
    "-S",
    help="Do not assemble, but output assembly language",
    action="store_true",
    default=False,
)
compile_parser.add_argument(
    "--ir",
    help="Output ppci ir-code, do not generate code",
    action="store_true",
    default=False,
)
compile_parser.add_argument(
    "--wasm",
    help="Output WASM (WebAssembly)",
    action="store_true",
    default=False,
)
compile_parser.add_argument(
    "--pycode", help="Output python code", action="store_true", default=False
)
compile_parser.add_argument(
    "-O", help="optimize code", default="0", choices=api.OPT_LEVELS
)
compile_parser.add_argument(
    "--instrument-functions",
    help="Instrument given functions",
    action="store_true",
    default=False,
)


def do_compile(ir_modules, march, reporter, args):
    """ Handle the proper output action """

    # Optimize:
    for ir_module in ir_modules:
        api.optimize(ir_module, level=args.O, reporter=reporter)

    # Instrument:
    if args.instrument_functions:
        for ir_module in ir_modules:
            add_tracer(ir_module)

    # TODO: what to do with the -c option? Add it here?

    # Generate output of choice:
    if args.ir:  # Stop after ir code generation
        with open(args.output, "w") as output:
            for ir_module in ir_modules:
                irutils.Writer(file=output).write(ir_module)
    elif args.S:  # Output assembly code
        with open(args.output, "w") as output:
            stream = TextOutputStream(printer=march.asm_printer, f=output)
            for ir_module in ir_modules:
                api.ir_to_stream(ir_module, march, stream, reporter=reporter)
    elif args.wasm:  # Output web-assembly code
        assert len(ir_modules) == 1
        ir_module = ir_modules[0]
        wasm_module = ir_to_wasm(ir_module)
        with open(args.output, "wb") as output:
            wasm_module.to_file(output)
    elif args.pycode:  # Output python code
        with open(args.output, "w") as output:
            api.ir_to_python(ir_modules, output, reporter=reporter)
    else:  # Full object output
        obj = api.ir_to_object(
            ir_modules, march, reporter=reporter, debug=args.g
        )
        with open(args.output, "w") as output:
            obj.save(output)

        # TODO: link objects together?
        logging.warning("TODO: Linking with stdlibs")
