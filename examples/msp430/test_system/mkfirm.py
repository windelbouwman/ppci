import argparse
from ppci.api import get_object
from ppci.binutils.objectfile import merge_memories

parser = argparse.ArgumentParser()
parser.add_argument('object_file', type=argparse.FileType('r'))
args = parser.parse_args()

o = get_object(args.object_file)
print('using object', o)

flash = o.get_image('flash')
ivect = o.get_image('vector16')
rom = merge_memories(flash, ivect, 'rom')
rom_data = rom.data

assert len(rom_data) % 2 == 0

with open('pmem.mem', 'w') as f:
    for i in range(len(rom_data) // 2):
        w = rom_data[2*i:2*i+2]
        print('%02x%02x' % (w[1], w[0]), file=f)
