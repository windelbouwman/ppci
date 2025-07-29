import logging
from ppci import api

logging.basicConfig(level=logging.INFO)

arch = api.get_arch("x86_64:wincc")
obj1 = api.c3c(
    ["../src/hello/hello.c3", "../../librt/io.c3", "bsp.c3", "kernel32.c3"],
    [],
    arch,
)
with open("kernel32.s", "r") as f:
    obj2 = api.asm(f, arch)

obj = api.link([obj1, obj2], partial_link=True)
print(obj)
api.objcopy(obj, "code", "exe", "hello.exe")
