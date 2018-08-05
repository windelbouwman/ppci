"""
wasmboy.wasm was made using:
$ clone https://github.com/torch2424/wasmBoy
$ npm run build
$ copy the file dist/core/index.untouched.wasm
"""
import sys
import logging
import os
import time
import argparse

import pygame
from pygame.locals import QUIT, KEYDOWN

from ppci.wasm import Module, instantiate
from ppci.wasm import wasm_to_ir
from ppci.api import get_arch, ir_to_object
from ppci.utils import reporting

parser = argparse.ArgumentParser()
parser.add_argument('--rom', default='cpu_instrs.gb')
args = parser.parse_args()
logging.basicConfig(level=logging.INFO)

with open('wasmboy.wasm', 'rb') as f:
    wasm_module = Module(f.read())

def log(a: int, b: int, c: int, d: int, e: int, f: int, g: int) -> None:
    print('Log:', a, b, c, d, e, f, g)

this_dir = os.path.dirname(os.path.abspath(__file__))
html_report = os.path.join(this_dir, 'wasmboy_report.html')
with open(html_report, 'w') as f, reporting.HtmlReportGenerator(f) as reporter:
    wasm_boy = instantiate(
        wasm_module,
        {'env': {'log': log}},
        target='native',
        reporter=reporter
    )

# Following this explanation: 
# https://github.com/torch2424/wasmBoy/wiki/%5BWIP%5D-Core-API

rom_filename = args.rom
logging.info('Loading %s', rom_filename)
# Load in a game to CARTRIDGE_ROM_LOCATION
rom_location = wasm_boy.exports.CARTRIDGE_ROM_LOCATION.read()
with open(rom_filename, 'rb') as f:
    rom_data = f.read()
rom_size = len(rom_data)
wasm_boy.exports.memory[rom_location:rom_location+rom_size] = rom_data

# Config
wasm_boy.exports.config(
    False, False, False, False, False, False, False, False, False
)

# Run pygame loop:
pygame.init()
resolution = (160, 144)
screen = pygame.display.set_mode(resolution)

while True:
    # Handle some events:
    for event in pygame.event.get():
        if event.type in (QUIT, KEYDOWN):
            sys.exit()

    # Run emulator wasm:
    # 1. Check audio:
    num_samples = wasm_boy.exports.getNumberOfSamplesInAudioBuffer()
    # print('num audio samples', num_samples)
    # TODO: emit sound to pygame
    wasm_boy.exports.clearAudioBuffer()
    res = wasm_boy.exports.executeFrame()
    if res != 0:
        raise RuntimeError('Gameboy died')

    # Fetch screen buffer:
    screen_offset = wasm_boy.exports.FRAME_LOCATION.read()
    screen_size = resolution[0] * resolution[1] * 3
    data = wasm_boy.exports.memory[screen_offset:screen_offset+screen_size]

    # Emit to pygame screen:
    img = pygame.image.frombuffer(data, resolution, 'RGB')
    screen.blit(img, (0, 0))
    pygame.display.update()
    pygame.time.delay(1)

