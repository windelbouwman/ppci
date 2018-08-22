""" Parser generator utility.

This script can generate a python script from a grammar description.

Invoke the script on a grammar specification file:

.. code::

    $ ppci-yacc test.x -o test_parser.py

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
from .base import base_parser, LogSetup
from ..lang.tools.yacc import transform


parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[base_parser])
parser.add_argument(
    'source', type=argparse.FileType('r'), help='the parser specification')
parser.add_argument(
    '-o', '--output', type=argparse.FileType('w'), required=True)


def yacc(args=None):
    args = parser.parse_args(args)
    with LogSetup(args):
        transform(args.source, args.output)
        args.output.close()


if __name__ == '__main__':
    yacc()
