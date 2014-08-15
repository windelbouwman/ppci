#!/usr/bin/env python

import argparse
import sys
from ppci.utils import stlink, stm32
from ppci.utils import hexfile


def hex2int(s):
    if s.startswith('0x'):
        s = s[2:]
        return int(s, 16)
    raise ValueError('Hexadecimal value must begin with 0x')


def make_parser():
    parser = argparse.ArgumentParser(
        description='ST-link flash utility by Windel Bouwman')
    subparsers = parser.add_subparsers(
        title='commands',
        description='possible commands', dest='command')

    readparser = subparsers.add_parser('read', help='read flash contents')
    readparser.add_argument('filename', type=argparse.FileType('wb', 0))
    readparser.add_argument('address', type=hex2int)
    readparser.add_argument('size', type=hex2int)

    writeparser = subparsers.add_parser('write', help='write flash contents')
    writeparser.add_argument('filename', type=argparse.FileType('rb'))
    writeparser.add_argument('address', type=hex2int)

    hexwriteparser = subparsers.add_parser(
        'hexwrite', help='write hexfile to flash')
    hexwriteparser.add_argument('hexfile', type=argparse.FileType('r'))

    verifyparser = subparsers.add_parser('verify',
                                         help='verify flash contents')
    verifyparser.add_argument('filename', type=argparse.FileType('rb'))
    verifyparser.add_argument('address', type=hex2int)

    subparsers.add_parser('erase', help='erase flash contents')
    return parser


def do_flashing(args):
    # In any command case, open a device:
    stl = stlink.STLink2()
    stl.open()

    # Enter the right mode:
    if stl.CurrentMode == stlink.DFU_MODE:
        stl.exitDfuMode()

    if stl.CurrentMode != stlink.DEBUG_MODE:
        stl.enterSwdMode()

    if stl.ChipId != 0x10016413:
        print('Only working on stm32f4discovery board for now.')
        sys.exit(2)

    # Retrieve the connected device, if any:
    dev = stl.createDevice()

    if args.command == 'read':
        dev_content = dev.readFlash(args.address, args.size)
        args.filename.write(dev_content)
    elif args.command == 'write':
        content = args.filename.read()
        dev.writeFlash(args.address, content)
    elif args.command == 'hexwrite':
        hf = hexfile.HexFile()
        hf.load(args.hexfile)
        for region in hf.regions:
            print('flashing {}'.format(region))
            dev.writeFlash(region.address, region.data)
    elif args.command == 'verify':
        content = args.filename.read()
        dev.verifyFlash(args.address, content)
    elif args.command == 'erase':
        dev.eraseFlash()
    else:
        print('unknown command', args.command)

    stl.reset()
    stl.run()
    stl.exitDebugMode()


if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_usage()
        sys.exit(1)
    do_flashing(args)
