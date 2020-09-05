"""
wasmboy.wasm was made using:
$ clone https://github.com/torch2424/wasmBoy
$ npm run build
$ copy the file dist/core/index.untouched.wasm
"""
import sys
import logging
import os
import argparse

import numpy as np
import pygame
from pygame.locals import QUIT

from ppci.wasm import Module, instantiate
from ppci.utils import reporting

parser = argparse.ArgumentParser()
parser.add_argument('--rom', default='cpu_instrs.gb')
args = parser.parse_args()
logging.basicConfig(level=logging.INFO)

with open('wasmboy.wasm', 'rb') as f:
    wasm_module = Module(f)


def log(a: int, b: int, c: int, d: int, e: int, f: int, g: int) -> None:
    print('Log:', a, b, c, d, e, f, g)


this_dir = os.path.dirname(os.path.abspath(__file__))
html_report = os.path.join(this_dir, 'wasmboy_report.html')
with reporting.html_reporter(html_report) as reporter:
    wasm_boy = instantiate(
        wasm_module,
        imports={'env': {'log': log}},
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
pygame.mixer.pre_init(48000)
pygame.init()
print('audio settings:', pygame.mixer.get_init())
resolution = (160, 144)
screen = pygame.display.set_mode(resolution)
channel = pygame.mixer.find_channel()
clock = pygame.time.Clock()

while True:
    # Handle some events:
    for event in pygame.event.get():
        if event.type == QUIT:
            sys.exit()

    # Run emulator wasm:
    # 1. Check audio:
    num_samples = wasm_boy.exports.getNumberOfSamplesInAudioBuffer()
    if num_samples > 4096:
        audio_buffer_location = wasm_boy.exports.AUDIO_BUFFER_LOCATION.read()
        audio_data = wasm_boy.exports.memory[
            audio_buffer_location:audio_buffer_location+num_samples*2]
        wasm_boy.exports.clearAudioBuffer()

        # Do some random conversions on the audio:
        audio = np.array(
            [(s - 127)*250 for s in audio_data],
            dtype=np.int16
        ).reshape((-1, 2))
        sound = pygame.sndarray.make_sound(audio)
        # print(num_samples, time.time())

        # Let last sample move out of queue:
        while channel.get_queue():
            pygame.time.delay(5)

        if channel.get_busy():
            channel.queue(sound)
        else:
            channel.play(sound)

    # Update keys:
    pressed_keys = pygame.key.get_pressed()
    wasm_boy.exports.setJoypadState(
        pressed_keys[pygame.K_UP],
        pressed_keys[pygame.K_RIGHT],
        pressed_keys[pygame.K_DOWN],
        pressed_keys[pygame.K_LEFT],
        pressed_keys[pygame.K_a],
        pressed_keys[pygame.K_b],
        pressed_keys[pygame.K_RETURN],  # start
        False  # select  # TODO
    )
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

    # Use deliberate higher framerate here, we will use audio to sync time
    clock.tick(65)
