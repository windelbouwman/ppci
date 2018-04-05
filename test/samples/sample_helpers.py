import io
import logging
import re
import os
from tempfile import mkstemp
from util import has_qemu, qemu, relpath, run_python, source_files
from util import has_iverilog, run_msp430, run_picorv32
from util import has_avr_emulator, run_avr, run_nodejs
from util import do_long_tests, do_iverilog, make_filename
from ppci.api import asm, c3c, link, objcopy, bfcompile, cc, get_current_arch
from ppci.api import c3_to_ir, bf_to_ir, ir_to_python, optimize, c_to_ir
from ppci.utils.reporting import HtmlReportGenerator
from ppci.formats import uboot_image
from ppci.binutils.objectfile import merge_memories
from ppci.lang.c import COptions


def create_test_function(source, output, lang):
    """ Create a test function for a source file """
    with open(source) as f:
        snippet = f.read()
    with open(output) as f:
        res = f.read()

    def tst_func(slf):
        slf.do(snippet, res, lang=lang)

    return tst_func


def add_samples(*folders):
    """ Create a decorator function that adds tests in the given folders """

    extensions = ('.c3', '.bf', '.c')

    def deco(cls):
        for folder in folders:
            for source in source_files(
                    relpath('samples', folder), extensions):
                output = os.path.splitext(source)[0] + '.out'
                basename = os.path.basename(source)
                name, lang = os.path.splitext(basename)
                lang = lang[1:]
                func_name = 'test_' + name
                tf = create_test_function(source, output, lang)
                assert not hasattr(cls, func_name)
                setattr(cls, func_name, tf)
        return cls

    return deco


def partial_build(src, lang, bsp_c3, opt_level, march, reporter):
    """ Compile source and return an object """
    if lang == 'c3':
        srcs = [
            relpath('..', 'librt', 'io.c3'),
            bsp_c3,
            io.StringIO(src)]
        o2 = c3c(
            srcs, [], march, opt_level=opt_level,
            reporter=reporter, debug=True)
        objs = [o2]
    elif lang == 'bf':
        o3 = bfcompile(src, march, reporter=reporter)
        o2 = c3c(
            [bsp_c3], [], march, reporter=reporter)
        objs = [o2, o3]
    elif lang == 'c':
        o2 = c3c(
            [bsp_c3], [], march, reporter=reporter)
        coptions = COptions()
        include_path1 = relpath('..', 'librt', 'libc')
        coptions.add_include_path(include_path1)
        with open(relpath('..', 'librt', 'libc', 'lib.c'), 'r') as f:
            o3 = cc(
                f, march, coptions=coptions, debug=True,
                reporter=reporter)
        o4 = cc(
            io.StringIO(src), march, coptions=coptions, debug=True,
            reporter=reporter)
        objs = [o2, o3, o4]
    else:
        raise NotImplementedError('language not implemented')
    obj = link(
        objs, partial_link=True,
        use_runtime=True, reporter=reporter, debug=True)
    return obj


def build(
        base_filename, src, bsp_c3, crt0_asm, march, opt_level, mmap,
        lang='c3', bin_format=None, elf_format=None, code_image='code'):
    """ Construct object file from source snippet """
    list_filename = base_filename + '.html'

    with HtmlReportGenerator(open(list_filename, 'w')) as reporter:
        o1 = asm(crt0_asm, march)
        if lang == 'c3':
            srcs = [
                relpath('..', 'librt', 'io.c3'),
                bsp_c3,
                io.StringIO(src)]
            o2 = c3c(
                srcs, [], march, opt_level=opt_level,
                reporter=reporter, debug=True)
            objs = [o1, o2]
        elif lang == 'bf':
            o3 = bfcompile(src, march, reporter=reporter)
            o2 = c3c(
                [bsp_c3], [], march, reporter=reporter)
            objs = [o1, o2, o3]
        elif lang == 'c':
            o2 = c3c(
                [bsp_c3], [], march, reporter=reporter)
            coptions = COptions()
            include_path1 = relpath('..', 'librt', 'libc')
            coptions.add_include_path(include_path1)
            with open(relpath('..', 'librt', 'libc', 'lib.c'), 'r') as f:
                o3 = cc(
                    f, march, coptions=coptions,
                    reporter=reporter)
            o4 = cc(
                io.StringIO(src), march, coptions=coptions,
                reporter=reporter)
            objs = [o1, o2, o3, o4]
        else:
            raise NotImplementedError('language not implemented')
        obj = link(
            objs, layout=mmap,
            use_runtime=True, reporter=reporter, debug=True)

    # Save object:
    obj_file = base_filename + '.oj'
    with open(obj_file, 'w') as f:
        obj.save(f)

    if elf_format:
        elf_filename = base_filename + '.' + elf_format
        objcopy(obj, code_image, elf_format, elf_filename)

    # Export code image to some format:
    if bin_format:
        sample_filename = base_filename + '.' + bin_format
        objcopy(obj, code_image, bin_format, sample_filename)

    return obj
