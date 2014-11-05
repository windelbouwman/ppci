
import sys
import argparse
import logging
import io

from .report import RstFormatter
from .buildfunctions import construct, bf2ir, optimize, bfcompile, c3toir
from .buildfunctions import c3compile
from .irutils import Writer
from .tasks import TaskError
from . import buildtasks  # Include not used, but it registers build tasks.
from . import logformat, machines


def logLevel(s):
    """ Converts a string to a valid logging level """
    numeric_level = getattr(logging, s.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: {}'.format(s))
    return numeric_level


def make_parser():
    parser = argparse.ArgumentParser(description='ppci compiler')

    parser.add_argument('--log', help='Log level (INFO,DEBUG,[WARN])',
                        type=logLevel, default='INFO')
    parser.add_argument(
        '--report',
        help='Specify a file to write the compile report to',
        type=argparse.FileType('w'))

    subparsers = parser.add_subparsers(
        title='commands',
        description='possible commands', dest='command')

    build_parser = subparsers.add_parser(
        'build',
        help='build project from xml description')
    build_parser.add_argument(
        '-b', '--buildfile',
        help='use buildfile, otherwise build.xml is the default',
        default='build.xml')
    build_parser.add_argument('targets', metavar='target', nargs='*')

    bf2ir_parser = subparsers.add_parser(
        'bf2ir', help='Compile brainfuck code into ir code.')
    bf2ir_parser.add_argument('source', type=argparse.FileType('r'))
    bf2ir_parser.add_argument(
        '-o', '--output', help='output file',
        type=argparse.FileType('w'), default=sys.stdout)

    bf2hex_parser = subparsers.add_parser(
        'bf2hex', help='Compile brainfuck code into hexfile for stm32f4.')
    bf2hex_parser.add_argument('source', type=argparse.FileType('r'))
    bf2hex_parser.add_argument('-o', '--output', help='output file',
                               type=argparse.FileType('w'))

    c32ir_parser = subparsers.add_parser(
        'c32ir', help='Compile c3 code into ir code.')
    c32ir_parser.add_argument('--target', help='target machine', default="arm")
    c32ir_parser.add_argument('-o', '--output', help='output file',
                              type=argparse.FileType('w'), default=sys.stdout)
    c32ir_parser.add_argument('-i', '--include', action='append',
                              help='include file', default=[])
    c32ir_parser.add_argument('sources', metavar='source',
                              help='source file', nargs='+')
    return parser


def main(args):
    # Configure some logging:
    logging.getLogger().setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(logformat))
    ch.setLevel(args.log)
    logging.getLogger().addHandler(ch)

    if args.report:
        fh = logging.StreamHandler(args.report)
        fh.setFormatter(RstFormatter())
        logging.getLogger().addHandler(fh)

    try:
        res = 0
        if args.command == 'build':
            res = construct(args.buildfile, args.targets)
        elif args.command == 'bf2ir':
            ircode = bf2ir(args.source.read())
            optimize(ircode)
            Writer().write(ircode, args.output)
        elif args.command == 'bf2hex':
            march = "thumb"
            obj = bfcompile(args.source.read(), march)
            realpb_arch = """
                module arch;

                function void putc(int c)
                {
                    var int *UART0DR;
                    UART0DR = cast<int*>(0x10009000);
                    *UART0DR = c;
                }
            """
            o2 = c3compile([io.StringIO(realpb_arch)], [], march)
            machines.wrap([obj, o2], march, "tst.bin")
            # TODO: link and hexwrite
            raise NotImplementedError('TODO: writeout hex')
        elif args.command == 'c3c':
            res = c3toir(args.sources, args.include, args.target)
            writer = Writer()
            for ir_module in res:
                writer.write(ir_module, args.output)
        else:
            raise Exception('command = {}'.format(args.command))
    except TaskError as err:
        logging.getLogger().error(str(err.msg))
        res = 1

    if args.report:
        logging.getLogger().removeHandler(fh)
        args.report.close()

    logging.getLogger().removeHandler(ch)
    return res
