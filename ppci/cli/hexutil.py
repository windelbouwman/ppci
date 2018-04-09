import argparse
import sys
from ..format.hexfile import HexFile


def hex2int(s):
    if s.startswith('0x'):
        s = s[2:]
        return int(s, 16)
    raise ValueError('Hexadecimal value must begin with 0x')


parser = argparse.ArgumentParser(
    description='hexfile manipulation tool by Windel Bouwman')
subparsers = parser.add_subparsers(
    title='commands',
    description='possible commands', dest='command')

p = subparsers.add_parser('info', help='dump info about hexfile')
p.add_argument('hexfile', type=argparse.FileType('r'))

p = subparsers.add_parser('new', help='create a hexfile')
p.add_argument('hexfile', type=argparse.FileType('w'))
p.add_argument('address', type=hex2int, help="hex address of the data")
p.add_argument(
    'datafile', type=argparse.FileType('rb'), help='binary file to add')

p = subparsers.add_parser('merge', help='merge two hexfiles into a third')
p.add_argument('hexfile1', type=argparse.FileType('r'), help="hexfile 1")
p.add_argument('hexfile2', type=argparse.FileType('r'), help="hexfile 2")
p.add_argument(
    'rhexfile', type=argparse.FileType('w'), help="resulting hexfile")


def hexutil(args=None):
    """ Hexfile manipulation command. """
    args = parser.parse_args(args)
    if not args.command:
        parser.print_usage()
        sys.exit(1)

    if args.command == 'info':
        hexfile = HexFile.load(args.hexfile)
        hexfile.dump()
        args.hexfile.close()
    elif args.command == 'new':
        hexfile = HexFile()
        data = args.datafile.read()
        args.datafile.close()
        hexfile.add_region(args.address, data)
        hexfile.save(args.hexfile)
        args.hexfile.close()
    elif args.command == 'merge':
        # Load first hexfile:
        hexfile1 = HexFile.load(args.hexfile1)
        args.hexfile1.close()

        # Load second hexfile:
        hexfile2 = HexFile.load(args.hexfile2)
        args.hexfile2.close()

        hexfile = HexFile()
        hexfile.merge(hexfile1)
        hexfile.merge(hexfile2)
        hexfile.save(args.rhexfile)
        args.rhexfile.close()
    else:  # pragma: no cover
        parser.print_usage()
        sys.exit(1)


if __name__ == '__main__':
    hexutil()
