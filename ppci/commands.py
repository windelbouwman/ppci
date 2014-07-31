

import argparse
import logging

from ppci.report import RstFormatter
from ppci.buildfunctions import construct
import ppci.buildtasks  # Include not used, but it registers build tasks.
import ppci


def logLevel(s):
    """ Converts a string to a valid logging level """
    numeric_level = getattr(logging, s.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: {}'.format(s))
    return numeric_level


def make_parser():
    parser = argparse.ArgumentParser(description='lcfos Compiler')

    parser.add_argument('--log', help='Log level (INFO,DEBUG,[WARN])',
                        type=logLevel, default='INFO')
    parser.add_argument(
        '--report',
        help='Specify a file to write the compile report to',
        type=argparse.FileType('w'))
    parser.add_argument(
        '--buildfile',
        help='use buildfile, otherwise build.xml is the default',
        default='build.xml')

    parser.add_argument('targets', metavar='target', nargs='*')
    return parser


def main(args):
    # Configure some logging:
    logging.getLogger().setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(ppci.logformat))
    ch.setLevel(args.log)
    logging.getLogger().addHandler(ch)

    if args.report:
        fh = logging.StreamHandler(args.report)
        fh.setFormatter(RstFormatter())
        logging.getLogger().addHandler(fh)

    res = construct(args.buildfile, args.targets)

    if args.report:
        logging.getLogger().removeHandler(fh)
        args.report.close()

    logging.getLogger().removeHandler(ch)
    return res
