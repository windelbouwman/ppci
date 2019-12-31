""" Jar file handling.
"""

import argparse
import logging
from .io import read_jar


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("jarfile")

    args = parser.parse_args()

    read_jar(args.jarfile)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
