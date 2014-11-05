#!/usr/bin/env python

import sys
import argparse
from ppci.utils.hexfile import HexFile

def hex2int(s):
    if s.startswith('0x'):
        s = s[2:]
        return int(s, 16)
    raise ValueError('Hexadecimal value must begin with 0x')

parser = argparse.ArgumentParser(
   description='hexfile manipulation tool by Windel Bouwman')
subparsers = parser.add_subparsers(title='commands',
         description='possible commands', dest='command')

p = subparsers.add_parser('info', help='dump info about hexfile')
p.add_argument('hexfile', type=argparse.FileType('r'))

p = subparsers.add_parser('new', help='create a hexfile')
p.add_argument('hexfile', type=argparse.FileType('w'))
p.add_argument('address', type=hex2int, help="hex address of the data")
p.add_argument('datafile', type=argparse.FileType('rb'), help='binary file to add')

p = subparsers.add_parser('merge', help='merge two hexfiles into a third')
p.add_argument('hexfile1', type=argparse.FileType('r'), help="hexfile 1")
p.add_argument('hexfile2', type=argparse.FileType('r'), help="hexfile 2")
p.add_argument('rhexfile', type=argparse.FileType('w'), help="resulting hexfile")


def main(args):
    if args.command == 'info':
        hexfile = HexFile()
        hexfile.load(args.hexfile)
        print(hexfile)
        for region in hexfile.regions:
            print(region)
    elif args.command == 'new':
        hf = HexFile()
        data = args.datafile.read()
        hf.addRegion(args.address, data)
        hf.save(args.hexfile)
    elif args.command == 'merge':
        hf = HexFile()
        hf.load(args.hexfile1)
        hf2 = HexFile()
        hf2.load(args.hexfile2)
        hf.merge(hf2)
        hf.save(args.rhexfile)
    else:
        raise NotImplementedError()


if __name__ == '__main__':
    args = parser.parse_args()
    if not args.command:
        parser.print_usage()
        sys.exit(1)
    main(args)
