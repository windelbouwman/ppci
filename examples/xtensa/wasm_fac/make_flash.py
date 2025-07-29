#!/usr/bin/python

from ppci.api import construct

construct("build.xml")

with open("hello.bin", "rb") as f:
    hello_bin = f.read()

flash_size = 4 * 1024 * 1024

with open("lx60.flash", "wb") as f:
    f.write(hello_bin)
    padding = flash_size - len(hello_bin)
    f.write(bytes(padding))
