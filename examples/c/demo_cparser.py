#!/usr/bin/python

""" A demo showing the usage of the preprocessor and the parser """

import argparse
from ppci.common import CompilerError
from ppci.lang.c import create_ast, CAstPrinter, CPrinter
from ppci.api import get_current_arch


if __name__ == '__main__':
    # Argument handling:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('source', help='C source file')
    args = arg_parser.parse_args()
    filename = args.source

    print("============= [ {} ] ===============".format(args.source))
    with open(args.source, 'r') as f:
        for row, line in enumerate(f, 1):
            print(row, ':', line.rstrip())
    print("====================================")

    # Parsing:
    arch_info = get_current_arch().info

    try:
        with open(filename, 'r') as f:
            ast = create_ast(f, arch_info, filename=filename)
    except CompilerError as ex:
        ex.print()
        raise
    else:
        print("=== Re-rendered source==============")
        CPrinter().print(ast)
        print("====================================")

        print("================ AST ===============")
        CAstPrinter().print(ast)
        print("====================================")
