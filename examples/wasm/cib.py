"""
See this impressive demo:

https://tbfleming.github.io/cib/

"""

import os
import math
import logging

import requests
import tqdm

from ppci.wasm import Module

logging.basicConfig(level=logging.DEBUG)
# Download this file:
# https://www.funkykarts.rocks/demo.wasm

def download_file(url, filename):
    r = requests.get(url, stream=True)
    total_size = int(r.headers.get('content-length', 0))
    block_size = 1024
    total = math.ceil(total_size // block_size)

    with open(filename, 'wb') as f:
        for data in tqdm.tqdm(r.iter_content(block_size), total=total, unit='KB', unit_scale=True):
            f.write(data)


files = [
    'clang.wasm',
    'clang-format.wasm',
    'runtime.wasm',
]

for local_filename in files:
    url = 'https://tbfleming.github.io/cib/{}'.format(local_filename)
    if not os.path.exists(local_filename):
        download_file(url, local_filename)

with open('clang.wasm', 'rb') as f:
    m = Module(f.read())


print(m)

m.show_interface()

