#!/usr/bin/env python

""" MCPP validation suite runner.

See homepage: http://mcpp.sourceforge.net

This script helps to run the MCPP preprocessor validation suite.
"""

import argparse
import logging
import glob
import os.path
import io

import ppci
from ppci.api import preprocess
from ppci.lang.c import COptions
from ppci.common import CompilerError


def run_test_t(directory):
    directory = os.path.normpath(directory)
    logging.info('Running t-tests in %s', directory)
    num_total = 0
    num_passed = 0
    coptions = COptions()
    coptions.enable('trigraphs')
    coptions.add_include_path(directory)
    for filename in sorted(glob.iglob(os.path.join(directory, 'n_*.t'))):
        with open(filename, 'r') as f:
            output_file = io.StringIO()
            num_total += 1
            try:
                ppci.api.preprocess(f, output_file, coptions)
                num_passed += 1
                logging.info('Testing sample %s OK', filename)
            except CompilerError as e:
                logging.info('Testing sample %s ERROR %s', filename, e.msg)
                e.print()
                print('ERROR', e)
            except Exception as e:
                print('ERROR', e)
    logging.info('Summary %s passed of %s', num_passed, num_total)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-t', help='specify the test-t directory')
    args = parser.parse_args()
    logging.info('Testing version %s of ppci', ppci.__version__)
    if args.t:
        run_test_t(args.t)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
