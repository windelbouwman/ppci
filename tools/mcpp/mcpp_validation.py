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
from ppci.common import CompilerError


def run_test_t(directory):
    directory = os.path.normpath(directory)
    logging.info('Running t-tests in %s', directory)
    num_total = 0
    num_passed = 0
    for filename in glob.iglob(os.path.join(directory, 'n_*.t')):
        logging.info('Testing sample %s', filename)
        with open(filename, 'r') as f:
            output_file = io.StringIO()
            num_total += 1
            try:
                ppci.api.preprocess(f, output_file, include_paths=[directory])
                num_passed += 1
                logging.info('PASS')
            except CompilerError as e:
                logging.error('ERROR %s', e.msg)
                print('ERROR', e)
            except UnicodeDecodeError as e:
                print(e)
            except FileNotFoundError as e:
                print(e)
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
