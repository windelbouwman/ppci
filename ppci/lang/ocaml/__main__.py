import argparse
import logging
import sys
from .cmo import read_file


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    read_file(sys.argv[1])
