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

this_dir = os.path.abspath(os.path.dirname(__file__))


def test_nos_on_riscv(benchmark):
    benchmark(compile_nos_for_riscv)


def test_compile_8cc(benchmark):
    benchmark(compile_8cc)


def compile_nos_for_riscv():
    """ Compile nOS for riscv architecture. """
    logging.basicConfig(level=logging.INFO)
    murax_folder = os.path.join(this_dir, "..", "examples", "riscvmurax")
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


def compile_8cc():
    """ Compile the 8cc compiler.

    8cc homepage:
    https://github.com/rui314/8cc
    """

    home = os.environ['HOME']
    _8cc_folder = os.path.join(home, 'GIT', '8cc')
    libc_includes = os.path.join(this_dir, '..', 'librt', 'libc', 'include')
    linux_include_dir = '/usr/include'
    arch = api.get_arch('x86_64')
    coptions = COptions()
    include_paths = [
        libc_includes,
        _8cc_folder,
        linux_include_dir,
        ]
    coptions.add_include_paths(include_paths)
    coptions.add_define('BUILD_DIR', '"{}"'.format(_8cc_folder))

    sources = [
        'cpp.c',
        'debug.c',
        'dict.c',
        'gen.c',
        'lex.c',
        'vector.c',
        'parse.c',
        'buffer.c',
        'map.c',
        'error.c',
        'path.c',
        'file.c',
        'set.c',
        'encoding.c',
    ]
    objs = []
    for filename in sources:
        source_path = os.path.join(_8cc_folder, filename)
        with open(source_path, 'r') as f:
            objs.append(api.cc(f, arch, coptions=coptions))

    # TODO: maybe link it?