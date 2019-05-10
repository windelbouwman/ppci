import argparse
import logging
from .cmo import read_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("cmo_file", help="cmo or bytecode file to read")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    read_file(args.cmo_file)
