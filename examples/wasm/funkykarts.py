import os
import math
import logging

import requests
import tqdm

from ppci.wasm import Module
from ppci.wasm import wasm_to_ir
from ppci.api import get_arch, ir_to_object

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
# Download this file:
# https://www.funkykarts.rocks/demo.wasm


def download_file(url, filename):
    r = requests.get(url, stream=True)
    total_size = int(r.headers.get("content-length", 0))
    block_size = 1024
    total = math.ceil(total_size // block_size)

    with open(filename, "wb") as f:
        for data in tqdm.tqdm(
            r.iter_content(block_size), total=total, unit="KB", unit_scale=True
        ):
            f.write(data)


url = "https://www.funkykarts.rocks/demo.wasm"
local_filename = "funkykarts.wasm"
if not os.path.exists(local_filename):
    download_file(url, local_filename)

with open("funkykarts.wasm", "rb") as f:
    wasm_module = Module(f.read())

print(wasm_module)
wasm_module.show_interface()

arch = get_arch("x86_64")
ptr_info = arch.info.get_type_info("ptr")
ir_module = wasm_to_ir(wasm_module, ptr_info)

print(ir_module)
print(ir_module.stats())

obj = ir_to_object([ir_module], arch)
