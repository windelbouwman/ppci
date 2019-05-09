""" Java handling utility.
"""

import argparse
import sys
from .base import base_parser, march_parser, LogSetup, get_arch_from_args
from .compile_base import compile_parser, do_compile
from ..arch.jvm import read_class_file, class_to_ir, print_class_file
from ..arch.jvm import read_jar
from ..irutils import print_module


parser = argparse.ArgumentParser(description=__doc__, parents=[base_parser])
subparsers = parser.add_subparsers(
    title="commands", description="possible commands", dest="command"
)

java_compile_parser = subparsers.add_parser(
    "compile",
    help="Compile a java class file ahead of time.",
    parents=[compile_parser, march_parser],
)
java_compile_parser.add_argument(
    "class_file",
    metavar="java class file",
    type=argparse.FileType("rb"),
    help="class file to compile",
)

dis_parser = subparsers.add_parser(
    "javap", help="Disassemble (javap) a java class."
)
dis_parser.add_argument(
    "class_file",
    metavar="java class file",
    type=argparse.FileType("rb"),
    help="class file to inspect",
)

jar_parser = subparsers.add_parser("jar", help="Explore jar file.")
jar_parser.add_argument(
    "jarfile", metavar="java jar file", help="jar file to inspect"
)


def java(args=None):
    """ Java command line utility. """
    args = parser.parse_args(args)
    with LogSetup(args) as log_setup:
        if args.command == "compile":
            march = get_arch_from_args(args)
            class_file = read_class_file(args.class_file, verbose=True)
            args.class_file.close()
            ir_module = class_to_ir(class_file)
            print_module(ir_module, verify=False)
            ir_modules = [ir_module]
            do_compile(ir_modules, march, log_setup.reporter, log_setup.args)
        elif args.command == "javap":
            class_file = read_class_file(args.class_file)
            args.class_file.close()
            print_class_file(class_file)
        elif args.command == "jar":
            read_jar(args.jarfile)
        else:  # pragma: no cover
            parser.print_usage()
            sys.exit(1)


if __name__ == "__main__":
    java()
