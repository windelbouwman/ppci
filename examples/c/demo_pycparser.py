#!/usr/bin/python

"""A demo showing the usage of the preprocessor with pycparsing"""

import argparse
import io
from ppci.api import preprocess
from pycparser.c_parser import CParser


if __name__ == "__main__":
    # Argument handling:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("source", help="C source file")
    args = arg_parser.parse_args()
    filename = args.source

    # Preprocessing:
    f2 = io.StringIO()
    with open(filename, "r") as f:
        preprocess(f, f2)
    source = f2.getvalue()

    # Parsing:
    parser = CParser()
    ast = parser.parse(source, filename)
    ast.show()
