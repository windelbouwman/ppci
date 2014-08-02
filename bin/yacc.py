#!/usr/bin/env python

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

import argparse
import sys
from ppci.pyyacc import main


def make_argument_parser():
    # Parse arguments:
    parser = argparse.ArgumentParser(description='xacc compiler compiler')
    parser.add_argument('source', type=argparse.FileType('r'), \
      help='the parser specification')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'), \
        default=sys.stdout)
    return parser


if __name__ == '__main__':
    args = make_argument_parser().parse_args()
    main(args)
