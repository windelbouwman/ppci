""" This contains a set of benchmarks to benchmark the ppci
compiler internals.

This can be used to verify a certain change yields a performance
improvement or not.

Run the benchmarks with pytest with the benchmark plugin:

python -m pytest benchmark.py
"""

import time
import os
import logging
from glob import glob
from ppci import api
from ppci.lang.c import COptions


def test_nos_on_riscv(benchmark):
    benchmark(compile_nos_for_riscv)


def compile_nos_for_riscv():
    logging.basicConfig(level=logging.INFO)
    murax_folder = "../examples/riscvmurax"
    arch = api.get_arch("riscv")

    # Gather sources:
    path = os.path.join(murax_folder, "csrc", "nos")
    folders, srcs = get_sources(path, "*.c")
    folders += [os.path.join(murax_folder, "csrc")]
    print(srcs)

    coptions = COptions()
    for folder in folders:
        coptions.add_include_path(folder)

    # Build code:
    o1 = api.asm(os.path.join(murax_folder, "start.s"), arch)
    o2 = api.asm(os.path.join(murax_folder, "nOSPortasm.s"), arch)
    objs = [o1, o2]

    for src in srcs:
        with open(src) as f:
            objs.append(api.cc(f, "riscv", coptions=coptions, debug=True))

    # Link code:
    api.link(
        objs,
        os.path.join(murax_folder, "firmware.mmap"),
        use_runtime=True,
        debug=True,
    )


def get_sources(folder, extension):
    resfiles = []
    resdirs = []
    for x in os.walk(folder):
        subfolder = x[0]
        for y in glob(os.path.join(subfolder, extension)):
            resfiles.append(y)
        resdirs.append(subfolder)
    return (resdirs, resfiles)
