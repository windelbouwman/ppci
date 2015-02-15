#!/usr/bin/env python

import argparse
import sys
import logging
from ppci.utils import stlink, stm32
from ppci.utils import hexfile
from ppci.utils.stlink import stlink_trace, stlink_flash, stlink_info
from ppci.utils.stlink import stlink_run_sram_and_trace


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
    writeparser.add_argument('address', type=hex2int)
    writeparser.add_argument('filename', type=argparse.FileType('rb'))

    hexwriteparser = subparsers.add_parser(
        'hexwrite', help='write hexfile to flash')
    hexwriteparser.add_argument('hexfile', type=argparse.FileType('r'))

    verifyparser = subparsers.add_parser('verify',
                                         help='verify flash contents')
    verifyparser.add_argument('filename', type=argparse.FileType('rb'))
    verifyparser.add_argument('address', type=hex2int)

    subparsers.add_parser('erase', help='erase flash contents')
    subparsers.add_parser('info', help='read id of stlink')
    subparsers.add_parser('trace', help='Trace data to stdout')
    run_trace = subparsers.add_parser(
        'run_and_trace', help='Put image in sram and trace')
    run_trace.add_argument('filename', type=argparse.FileType('rb'))
    return parser


def do_flashing(args):
    """ Perform the action as given by the args """
    # In any command case, open a device:

    if args.command == 'read':
        stl = stlink.STLink2()
        stl.open()

        if stl.ChipId != 0x10016413:
            print('Only working on stm32f4discovery board for now.')
            sys.exit(2)

        # Create the device:
        dev = stm32.Stm32F40x(stl)
        dev_content = dev.readFlash(args.address, args.size)
        args.filename.write(dev_content)
        stl.reset()
        stl.run()
        stl.close()
    elif args.command == 'write':
        stlink_flash(args.address, args.filename.read())
    elif args.command == 'hexwrite':
        stl = stlink.STLink2()
        stl.open()

        if stl.ChipId != 0x10016413:
            print('Only working on stm32f4discovery board for now.')
            sys.exit(2)

        # Create the device:
        dev = stm32.Stm32F40x(stl)
        hf = hexfile.HexFile()
        hf.load(args.hexfile)
        for region in hf.regions:
            print('flashing {}'.format(region))
            dev.writeFlash(region.address, region.data)
        stl.reset()
        stl.run()
        stl.close()
    elif args.command == 'verify':
        stl = stlink.STLink2()
        stl.open()

        if stl.ChipId != 0x10016413:
            print('Only working on stm32f4discovery board for now.')
            sys.exit(2)

        # Create the device:
        dev = stm32.Stm32F40x(stl)
        content = args.filename.read()
        dev.verifyFlash(args.address, content)
        stl.reset()
        stl.run()
        stl.close()
    elif args.command == 'erase':
        stl = stlink.STLink2()
        stl.open()

        if stl.ChipId != 0x10016413:
            print('Only working on stm32f4discovery board for now.')
            sys.exit(2)

        # Create the device:
        dev = stm32.Stm32F40x(stl)
        dev.eraseFlash()
        stl.reset()
        stl.run()
        stl.close()
    elif args.command == 'info':
        stlink_info()
    elif args.command == 'trace':
        stlink_trace()
    elif args.command == 'run_and_trace':
        stlink_run_sram_and_trace(args.filename.read())
    else:
        print('unknown command', args.command)


if __name__ == '__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    parser = make_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_usage()
        sys.exit(1)
    do_flashing(args)
