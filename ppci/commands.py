""" Contains the command line interface functions. """

# pylint: disable=C0103

import sys
import os
import platform
import argparse
import logging
import importlib
import io

from .pcc.yacc import transform
from .utils.hexfile import HexFile
from .binutils.objectfile import ObjectFile, print_object
from .tasks import TaskError
from . import __version__, api, irutils
from .common import logformat, CompilerError
from .arch.target_list import target_names, create_arch
from .binutils.dbg import Debugger
from .binutils.dbg_cli import DebugCli


version_text = 'ppci {} compiler on {} {}'.format(
    __version__, platform.python_implementation(), platform.python_version())


def log_level(s):
    """ Converts a string to a valid logging level """
    numeric_level = getattr(logging, s.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: {}'.format(s))
    return numeric_level


class OnceAction(argparse.Action):
    """ Use this action to enforce that an option is only given once """
    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest, None) is not None:
            raise argparse.ArgumentError(self, 'Cannot give multiple')
        setattr(namespace, self.dest, values)


base_parser = argparse.ArgumentParser(add_help=False)
base_parser.add_argument(
    '--log', help='Log level (info,debug,warn)', metavar='log-level',
    type=log_level, default='info')
base_parser.add_argument(
    '--report', metavar='report-file', action=OnceAction,
    help='Specify a file to write the compile report to',
    type=argparse.FileType('w'))
base_parser.add_argument(
    '--verbose', '-v', action='count', default=0,
    help='Increase verbosity of the output')
base_parser.add_argument(
    '--version', '-V', action='version', version=version_text,
    help='Display version and exit')


march_parser = argparse.ArgumentParser(add_help=False)
march_parser.add_argument(
    '--machine', '-m', help='target architecture', required=True,
    choices=target_names, action=OnceAction)
march_parser.add_argument(
    '--mtune', help='architecture option', default=[],
    metavar='option', action='append')


out_parser = argparse.ArgumentParser(add_help=False)
out_parser.add_argument(
    '--output', '-o', help='output file', metavar='output-file',
    type=argparse.FileType('w'), required=True, action=OnceAction)


def get_arch_from_args(args):
    """ Determine the intended machine target and select the proper options """
    options = tuple(args.mtune)
    return create_arch(args.machine, options=options)


class ColoredFormatter(logging.Formatter):
    """ Custom formatter that makes vt100 coloring to log messages """
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
    colors = {
        'INFO': WHITE,
        'WARNING': YELLOW,
        'ERROR': RED
    }

    def format(self, record):
        reset_seq = '\033[0m'
        color_seq = '\033[1;%dm'
        levelname = record.levelname
        msg = super().format(record)
        if levelname in self.colors:
            color = color_seq % (30 + self.colors[levelname])
            msg = color + msg + reset_seq
        return msg


build_description = """
Build utility. Use this to execute build files.
"""
build_parser = argparse.ArgumentParser(
    description=build_description, parents=[base_parser])
build_parser.add_argument(
    '-f', '--buildfile', metavar='build-file',
    help='use buildfile, otherwise build.xml is the default',
    default='build.xml')
build_parser.add_argument('targets', metavar='target', nargs='*')


def build(args=None):
    """ Run the build command from command line. Used by ppci-build.py """
    args = build_parser.parse_args(args)
    with LogSetup(args):
        api.construct(args.buildfile, args.targets)


c3c_description = """
C3 compiler. Use this compiler to produce object files from c3 sources and c3
includes. C3 includes have the same format as c3 source files, but do not
result in any code.
"""
c3c_parser = argparse.ArgumentParser(
    description=c3c_description,
    parents=[base_parser, march_parser, out_parser])
c3c_parser.add_argument(
    '-i', '--include', action='append', metavar='include',
    help='include file', default=[])
c3c_parser.add_argument(
    'sources', metavar='source', help='source file', nargs='+')
c3c_parser.add_argument(
    '-g', help='create debug information', action='store_true', default=False)
c3c_parser.add_argument(
    '-O', help='optimize code', default='0', choices=api.OPT_LEVELS)


def c3c(args=None):
    """ Run c3 compile task """
    args = c3c_parser.parse_args(args)
    with LogSetup(args):
        # Compile sources:
        march = get_arch_from_args(args)
        obj = api.c3c(args.sources, args.include, march, debug=args.g)

        # Write object file to disk:
        obj.save(args.output)
        args.output.close()


cc_description = """ C compiler. """
cc_parser = argparse.ArgumentParser(
    description=cc_description,
    parents=[base_parser, march_parser, out_parser])
cc_parser.add_argument(
    'sources', metavar='source', help='source file', nargs='+')


def cc(args=None):
    """ Run c compile task """
    args = cc_parser.parse_args(args)
    with LogSetup(args):
        # Compile sources:
        march = get_arch_from_args(args)
        for src in args.sources:
            obj = api.cc(src, march)

        # TODO: link objects together?

        # Write object file to disk:
        obj.save(args.output)
        args.output.close()


llc_description = """ LLVM static compiler. """
llc_parser = argparse.ArgumentParser(
    description=llc_description,
    parents=[base_parser, march_parser, out_parser])
llc_parser.add_argument(
    'source', help='source file', type=argparse.FileType('r'))


def llc(args=None):
    """ Compile llvm ir code into machine code """
    args = llc_parser.parse_args(args)
    with LogSetup(args):
        march = get_arch_from_args(args)
        src = args.source
        obj = api.llc(src, march)

        # Write object file to disk:
        obj.save(args.output)
        args.output.close()


asm_description = """ Assembler utility. """
asm_parser = argparse.ArgumentParser(
    description=asm_description,
    parents=[base_parser, march_parser, out_parser])
asm_parser.add_argument(
    '-g', '--debug', help='create debug information',
    action='store_true', default=False)
asm_parser.add_argument(
    'sourcefile', type=argparse.FileType('r'),
    help='the source file to assemble')


def asm(args=None):
    """ Run asm from command line """
    args = asm_parser.parse_args(args)
    with LogSetup(args):
        # Assemble source:
        march = get_arch_from_args(args)
        obj = api.asm(args.sourcefile, march, debug=args.debug)

        # Write object file to disk:
        obj.save(args.output)
        args.output.close()


disasm_description = """ Disassembler utility. """
disasm_parser = argparse.ArgumentParser(
    description=disasm_description, parents=[base_parser, march_parser])
disasm_parser.add_argument(
    'binfile', type=argparse.FileType('rb'),
    help='the source file to assemble')


def disasm(args=None):
    """ Run asm from command line """
    args = disasm_parser.parse_args(args)
    with LogSetup(args):
        # Assemble source:
        march = get_arch_from_args(args)
        api.disasm(args.binfile, march)


dbg_description = """
Debugger command line utility.
"""

dbg_parser = argparse.ArgumentParser(
    description=dbg_description, parents=(march_parser, base_parser))
dbg_parser.add_argument(
    '--driver',
    help='debug driver to use. Specify in the format: module:class',
    default='ppci.binutils.dbg:DummyDebugDriver')


def dbg(args=None):
    """ Run dbg from command line """
    args = dbg_parser.parse_args(args)
    with LogSetup(args):
        march = get_arch_from_args(args)
        driver_module_name, driver_class_name = args.driver.split(':')
        driver_module = importlib.import_module(driver_module_name)
        driver_class = getattr(driver_module, driver_class_name)
        driver = driver_class()
        debugger = Debugger(march, driver)
        cli = DebugCli(debugger)
        cli.cmdloop()


link_description = """
Linker. Use the linker to combine several object files and a memory layout
to produce another resulting object file with images.
"""
link_parser = argparse.ArgumentParser(
    description=link_description, parents=[base_parser, out_parser])
link_parser.add_argument(
    'obj', type=argparse.FileType('r'), nargs='+',
    help='the object to link')
link_parser.add_argument(
    '--layout', '-L', help='memory layout', default=None,
    type=argparse.FileType('r'), metavar='layout-file')
link_parser.add_argument(
    '-g', help='retain debug information', action='store_true', default=False)


def link(args=None):
    """ Run asm from command line """
    args = link_parser.parse_args(args)
    with LogSetup(args):
        obj = api.link(args.obj, layout=args.layout, debug=args.g)
        obj.save(args.output)
        args.output.close()


objdump_description = """
Objdump utility to display the contents of object files.
"""
objdump_parser = argparse.ArgumentParser(
    description=objdump_description, parents=[base_parser])
objdump_parser.add_argument(
    'obj', help='object file', type=argparse.FileType('r'))
objdump_parser.add_argument(
    '-d', '--disassemble', help='Disassemble contents', action='store_true',
    default=False)


def objdump(args=None):
    """ Dump info of an object file """
    args = objdump_parser.parse_args(args)
    with LogSetup(args):
        obj = ObjectFile.load(args.obj)
        args.obj.close()
        print_object(obj)
        if args.disassemble:
            for section in obj.sections:
                print(section.name)
                f = io.BytesIO(section.data)
                api.disasm(f, obj.arch)


objcopy_description = """
Objcopy utility to manipulate object files.
"""
objcopy_parser = argparse.ArgumentParser(
    description=objcopy_description, parents=[base_parser])
objcopy_parser.add_argument(
    'input', help='input file', type=argparse.FileType('r'))
objcopy_parser.add_argument(
    '--segment', '-S', help='segment to copy', required=True)
objcopy_parser.add_argument(
    'output', help='output file')
objcopy_parser.add_argument(
    '--output-format', '-O', help='output file format')


def objcopy(args=None):
    """ Copy from binary format 1 to binary format 2 """
    args = objcopy_parser.parse_args(args)
    with LogSetup(args):
        # Read object from file:
        obj = ObjectFile.load(args.input)
        args.input.close()
        api.objcopy(obj, args.segment, args.output_format, args.output)


opt_description = """ Optimizer """
opt_parser = argparse.ArgumentParser(
    description=opt_description, parents=[base_parser])
opt_parser.add_argument(
    '-O', help='Optimization level', default=2, type=int)
opt_parser.add_argument(
    'input', help='input file', type=argparse.FileType('r'))
opt_parser.add_argument(
    'output', help='output file', type=argparse.FileType('w'))


def opt(args=None):
    """ Optimize a single IR-file """
    args = opt_parser.parse_args(args)
    module = irutils.Reader().read(args.input)
    with LogSetup(args):
        api.optimize(module, level=args.O)
    irutils.Writer().write(module, args.output)


def yacc_cmd(args=None):
    """
    Parser generator utility. This script can generate a python script from a
    grammar description.

    Invoke the script on a grammar specification file:

    .. code::

        $ ./yacc.py test.x -o test_parser.py

    And use the generated parser by deriving a user class:


    .. code::

        import test_parser
        class MyParser(test_parser.Parser):
            pass
        p = MyParser()
        p.parse()


    Alternatively you can load the parser on the fly:

    .. code::

        import yacc
        parser_mod = yacc.load_as_module('mygrammar.x')
        class MyParser(parser_mod.Parser):
            pass
        p = MyParser()
        p.parse()

    """
    parser = argparse.ArgumentParser(
        description='xacc compiler compiler', parents=[base_parser])
    parser.add_argument(
        'source', type=argparse.FileType('r'), help='the parser specification')
    parser.add_argument(
        '-o', '--output', type=argparse.FileType('w'), required=True)

    args = parser.parse_args(args)
    with LogSetup(args):
        transform(args.source, args.output)
        args.output.close()


def hex2int(s):
    if s.startswith('0x'):
        s = s[2:]
        return int(s, 16)
    raise ValueError('Hexadecimal value must begin with 0x')


hexutil_parser = argparse.ArgumentParser(
    description='hexfile manipulation tool by Windel Bouwman')
subparsers = hexutil_parser.add_subparsers(
    title='commands',
    description='possible commands', dest='command')

p = subparsers.add_parser('info', help='dump info about hexfile')
p.add_argument('hexfile', type=argparse.FileType('r'))

p = subparsers.add_parser('new', help='create a hexfile')
p.add_argument('hexfile', type=argparse.FileType('w'))
p.add_argument('address', type=hex2int, help="hex address of the data")
p.add_argument(
    'datafile', type=argparse.FileType('rb'), help='binary file to add')

p = subparsers.add_parser('merge', help='merge two hexfiles into a third')
p.add_argument('hexfile1', type=argparse.FileType('r'), help="hexfile 1")
p.add_argument('hexfile2', type=argparse.FileType('r'), help="hexfile 2")
p.add_argument(
    'rhexfile', type=argparse.FileType('w'), help="resulting hexfile")


def hexutil(args=None):
    """
        Hexfile manipulation command.
    """
    args = hexutil_parser.parse_args(args)
    if not args.command:
        hexutil_parser.print_usage()
        sys.exit(1)

    if args.command == 'info':
        hexfile = HexFile.load(args.hexfile)
        hexfile.dump()
        args.hexfile.close()
    elif args.command == 'new':
        hexfile = HexFile()
        data = args.datafile.read()
        args.datafile.close()
        hexfile.add_region(args.address, data)
        hexfile.save(args.hexfile)
        args.hexfile.close()
    elif args.command == 'merge':
        # Load first hexfile:
        hexfile1 = HexFile.load(args.hexfile1)
        args.hexfile1.close()

        # Load second hexfile:
        hexfile2 = HexFile.load(args.hexfile2)
        args.hexfile2.close()

        hexfile = HexFile()
        hexfile.merge(hexfile1)
        hexfile.merge(hexfile2)
        hexfile.save(args.rhexfile)
        args.rhexfile.close()
    else:  # pragma: no cover
        raise NotImplementedError()


class LogSetup:
    """ Context manager that attaches logging to a snippet """
    def __init__(self, args):
        self.args = args
        self.console_handler = None
        self.file_handler = None
        self.logger = logging.getLogger()

    def __enter__(self):
        self.logger.setLevel(logging.DEBUG)
        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(ColoredFormatter(logformat))
        self.console_handler.setLevel(self.args.log)
        self.logger.addHandler(self.console_handler)

        if self.args.verbose > 0:
            self.console_handler.setLevel(logging.DEBUG)

        if self.args.report:
            self.file_handler = logging.StreamHandler(self.args.report)
            self.logger.addHandler(self.file_handler)
        self.logger.debug('Loggers attached')
        self.logger.info(version_text)

    def __exit__(self, exc_type, exc_value, traceback):
        # Check if a task error was raised:
        if isinstance(exc_value, TaskError):
            self.logger.error(str(exc_value.msg))
            err = True
        else:
            err = False

        if isinstance(exc_value, CompilerError):
            self.logger.error(str(exc_value))
            self.logger.error(str(exc_value.loc))
            exc_value.print()

        if exc_value is not None:
            # Exception happened, close file and remove
            if hasattr(self.args, 'output'):
                self.args.output.close()
                if hasattr(self.args.output, 'name'):
                    filename = self.args.output.name
                    os.remove(filename)

        self.logger.debug('Removing loggers')
        if self.args.report:
            self.logger.removeHandler(self.file_handler)
            self.args.report.close()

        self.logger.removeHandler(self.console_handler)

        # exit code when error:
        if err:
            sys.exit(1)
