"""
    Contains the command line interface functions.
"""
import sys
import platform
import argparse
import logging

from .report import RstFormatter
from .buildfunctions import construct
from .buildfunctions import c3compile
from .buildfunctions import assemble
from .utils.hexfile import HexFile
from .tasks import TaskError
from . import version
from .common import logformat


description = 'ppci {} compiler on {} {}'.format(
    version, platform.python_implementation(), platform.python_version())


def log_level(s):
    """ Converts a string to a valid logging level """
    numeric_level = getattr(logging, s.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: {}'.format(s))
    return numeric_level


def add_common_parser_options(parser):
    """ Add some common parser arguments to the parser """
    parser.add_argument('--log', help='Log level (INFO,DEBUG,WARN)',
                        type=log_level, default='INFO')
    parser.add_argument(
        '--report',
        help='Specify a file to write the compile report to',
        type=argparse.FileType('w'))
    parser.add_argument(
        '--verbose', '-v', action='count', default=0,
        help='Increase verbosity of the output')


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


def build(args=None):
    """ Run the build command from command line. Used by ppci-build.py """
    parser = argparse.ArgumentParser(description=description)

    add_common_parser_options(parser)
    parser.add_argument(
        '-f', '--buildfile',
        help='use buildfile, otherwise build.xml is the default',
        default='build.xml')
    parser.add_argument('targets', metavar='target', nargs='*')
    args = parser.parse_args(args)
    logger = logging.getLogger()
    with LogSetup(args):
        logger.info(description)
        logger.debug('Arguments: {}'.format(args))
        construct(args.buildfile, args.targets)


def c3c(args=None):
    """ Run c3 compile task """
    parser = argparse.ArgumentParser(description=description)
    add_common_parser_options(parser)

    parser.add_argument('--target', help='target machine', required=True)
    parser.add_argument('--output', '-o', help='output file',
                        type=argparse.FileType('w'),
                        default=sys.stdout)
    parser.add_argument('-i', '--include', action='append',
                        help='include file', default=[])
    parser.add_argument('sources', metavar='source',
                        help='source file', nargs='+')
    args = parser.parse_args(args)
    with LogSetup(args):
        logging.getLogger().info(description)

        # Compile sources:
        obj = c3compile(args.sources, args.include, args.target)

        # Write object file to disk:
        obj.save(args.output)
        args.output.close()


def asm(args=None):
    """ Run asm from command line """
    parser = argparse.ArgumentParser(description=description)
    add_common_parser_options(parser)
    parser.add_argument('sourcefile', type=argparse.FileType('r'),
                        help='the source file to assemble')
    parser.add_argument('--target', help='target machine', required=True)
    parser.add_argument('--output', '-o', help='output file',
                        type=argparse.FileType('w'),
                        default=sys.stdout)
    args = parser.parse_args(args)
    with LogSetup(args):
        logging.getLogger().info(description)

        # Assemble source:
        obj = assemble(args.sourcefile, args.target)

        # Write object file to disk:
        obj.save(args.output)
        args.output.close()


def hexutil(args=None):
    def hex2int(s):
        if s.startswith('0x'):
            s = s[2:]
            return int(s, 16)
        raise ValueError('Hexadecimal value must begin with 0x')

    parser = argparse.ArgumentParser(
       description='hexfile manipulation tool by Windel Bouwman')
    subparsers = parser.add_subparsers(
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

    args = parser.parse_args(args)
    if not args.command:
        parser.print_usage()
        sys.exit(1)

    if args.command == 'info':
        hexfile = HexFile()
        hexfile.load(args.hexfile)
        print(hexfile)
        for region in hexfile.regions:
            print(region)
    elif args.command == 'new':
        hexfile = HexFile()
        data = args.datafile.read()
        hexfile.add_region(args.address, data)
        hexfile.save(args.hexfile)
    elif args.command == 'merge':
        # Load first hexfile:
        hexfile1 = HexFile()
        hexfile1.load(args.hexfile1)

        # Load second hexfile:
        hexfile2 = HexFile()
        hexfile2.load(args.hexfile2)

        hexfile = HexFile()
        hexfile.merge(hexfile1)
        hexfile.merge(hexfile2)
        hexfile.save(args.rhexfile)
    else:
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
            self.file_handler.setFormatter(RstFormatter())
            self.logger.addHandler(self.file_handler)
        self.logger.debug('Loggers attached')

    def __exit__(self, exc_type, exc_value, traceback):
        # Check if a task error was raised:
        if isinstance(exc_value, TaskError):
            logging.getLogger().error(str(exc_value.msg))
            err = True
        else:
            err = False

        self.logger.debug('Removing loggers')
        if self.args.report:
            self.logger.removeHandler(self.file_handler)
            self.args.report.close()

        self.logger.removeHandler(self.console_handler)

        # exit code when error:
        if err:
            sys.exit(1)
