#!/usr/bin/python

""" A demo showing the usage of the preprocessor and the parser """

import argparse
import io
from ppci.common import CompilerError
from ppci.lang.c import CPreProcessor, CParser, COptions, Printer
from ppci.lang.c.preprocessor import prepare_for_parsing


if __name__ == '__main__':
    # Argument handling:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('source', help='C source file')
    args = arg_parser.parse_args()
    filename = args.source

    # Parsing:
    coptions = COptions()
    preprocessor = CPreProcessor(coptions)
    parser = CParser(coptions)

    try:
        with open(filename, 'r') as f:
            tokens = preprocessor.process(f, filename)
            tokens = prepare_for_parsing(tokens)
            ast = parser.parse(tokens)
    except CompilerError as ex:
        ex.print()
        raise
    else:
        Printer().print(ast)
