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
from ppci.wasm import wasm_to_ir
from ppci.api import get_arch

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

with open('runtime.wasm', 'rb') as f:
    wasm_module = Module(f.read())


print(wasm_module)

wasm_module.show_interface()

ptr_info = get_arch('x86_64').info.get_type_info('ptr')
ir_module = wasm_to_ir(wasm_module, ptr_info)

