#!/usr/bin/env python

""" MCPP validation suite runner.

See homepage: http://mcpp.sourceforge.net

This script helps to run the MCPP preprocessor validation suite.

The validation suite is organized into directories test-t, test-c and test-l.
Test snippets are prefixed with n_ for valid snippets, i_ prefixed snippets
contain implementation defined snippets, e_ indicates that this file will
result in an error.

The test-t directory contains .t files which are text files to be preprocessed.
The test-c directory contains .c files which are the same as the .t files
but are valid c programs which might be compiled.

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

this_dir = os.path.dirname(os.path.abspath(__file__))


def run_test_t(directory, stop_at_first_error=False):
    directory = os.path.normpath(directory)
    logging.info('Running t-tests in %s', directory)
    num_total = 0
    num_passed = 0
    coptions = COptions()
    coptions.enable('trigraphs')
    coptions.add_include_path(directory)
    libc_dir = os.path.join(
        this_dir, '..', '..', 'librt', 'libc')
    coptions.add_include_path(libc_dir)
    for filename in sorted(glob.iglob(os.path.join(directory, 'n_*.t'))):
        logging.info('Testing sample %s ...', filename)
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
                if stop_at_first_error:
                    break
            except Exception as e:
                print('ERROR', e)
                if stop_at_first_error:
                    break
    logging.info('Summary %s passed of %s', num_passed, num_total)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-t', help='specify the test-t directory')
    parser.add_argument(
        '-x', help='Stop after first failure',
        action='store_true', default=False)
    args = parser.parse_args()
    logging.info('Testing version %s of ppci', ppci.__version__)
    if args.t:
        run_test_t(args.t, stop_at_first_error=args.x)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
