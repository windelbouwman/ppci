import argparse
import logging
from .reader import read_hunk


def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("hunk_file")
    args = parser.parse_args()
    read_hunk(args.hunk_file)


if __name__ == "__main__":
    main()
