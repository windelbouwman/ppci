import io
import os
from ..helper_util import relpath, source_files
from ppci import api
from ppci.utils.reporting import html_reporter
from ppci.lang.c import COptions


def create_test_function(source, output, lang):
    """Create a test function for a source file"""
    with open(source) as f:
        snippet = f.read()
    with open(output) as f:
        res = f.read()

    def tst_func(slf):
        slf.do(snippet, res, lang=lang)

    return tst_func


def add_samples(*folders):
    """Create a decorator function that adds tests in the given folders"""

    extensions = (".c3", ".bf", ".c", ".pas")

    def deco(cls):
        for folder in folders:
            for source in source_files(relpath("samples", folder), extensions):
                output = os.path.splitext(source)[0] + ".out"
                basename = os.path.basename(source)
                name, lang = os.path.splitext(basename)
                lang = lang[1:]
                func_name = "test_" + name
                tf = create_test_function(source, output, lang)
                assert not hasattr(cls, func_name)
                setattr(cls, func_name, tf)
        return cls

    return deco


def build_sample_to_ir(src, lang, bsp_c3, march, reporter):
    """Compile the given sample into ir-modules"""
    if lang == "c3":
        ir_modules = [
            api.c3_to_ir(
                [bsp_c3, relpath("..", "librt", "io.c3"), io.StringIO(src)],
                [],
                march,
                reporter=reporter,
            )
        ]
    elif lang == "bf":
        ir_modules = [api.bf_to_ir(src, march)]
    elif lang == "c":
        coptions = COptions()
        libc_path = relpath("..", "librt", "libc")
        include_path1 = os.path.join(libc_path, "include")
        lib = relpath("..", "librt", "libc", "lib.c")
        coptions.add_include_path(include_path1)
        with open(lib) as f:
            mod1 = api.c_to_ir(f, march, coptions=coptions, reporter=reporter)
        mod2 = api.c_to_ir(
            io.StringIO(src), march, coptions=coptions, reporter=reporter
        )
        ir_modules = [mod1, mod2]
    elif lang == "pas":
        pascal_ir_modules = api.pascal_to_ir(
            [io.StringIO(src)], api.get_arch(march)
        )
        ir_modules = pascal_ir_modules
    else:  # pragma: no cover
        raise NotImplementedError(f"Language {lang} not implemented")
    return ir_modules


def build_sample_to_code(src, lang, bsp_c3, opt_level, march, debug, reporter):
    """Turn example sample into code objects."""
    if lang == "c3":
        srcs = [relpath("..", "librt", "io.c3"), bsp_c3, io.StringIO(src)]
        o2 = api.c3c(
            srcs,
            [],
            march,
            opt_level=opt_level,
            reporter=reporter,
            debug=debug,
        )
        objs = [o2]
    elif lang == "bf":
        o3 = api.bfcompile(src, march, reporter=reporter)
        o2 = api.c3c([bsp_c3], [], march, reporter=reporter)
        objs = [o2, o3]
    elif lang == "c":
        o2 = api.c3c([bsp_c3], [], march, reporter=reporter)
        coptions = COptions()
        libc_path = relpath("..", "librt", "libc")
        include_path1 = os.path.join(libc_path, "include")
        coptions.add_include_path(include_path1)
        with open(relpath("..", "librt", "libc", "lib.c")) as f:
            o3 = api.cc(
                f, march, coptions=coptions, debug=debug, reporter=reporter
            )
        o4 = api.cc(
            io.StringIO(src),
            march,
            coptions=coptions,
            debug=debug,
            reporter=reporter,
        )
        objs = [o2, o3, o4]
    elif lang == "pas":
        o3 = api.pascal(
            [io.StringIO(src)], march, reporter=reporter, debug=debug
        )
        o2 = api.c3c([bsp_c3], [], march, reporter=reporter)
        objs = [o2, o3]
    else:
        raise NotImplementedError("language not implemented")
    return objs


def partial_build(src, lang, bsp_c3, opt_level, march, reporter):
    """Compile source and return an object"""
    objs = build_sample_to_code(
        src, lang, bsp_c3, opt_level, march, True, reporter
    )
    obj = api.link(
        objs,
        partial_link=True,
        use_runtime=True,
        reporter=reporter,
        debug=True,
    )
    return obj


def build(
    base_filename,
    src,
    bsp_c3,
    crt0_asm,
    march,
    opt_level,
    mmap,
    lang="c3",
    bin_format=None,
    elf_format=None,
    code_image="code",
):
    """Construct object file from source snippet"""
    list_filename = base_filename + ".html"

    with html_reporter(list_filename) as reporter:
        objs = build_sample_to_code(
            src, lang, bsp_c3, opt_level, march, True, reporter
        )
        o1 = api.asm(crt0_asm, march)
        objs.append(o1)
        obj = api.link(
            objs, layout=mmap, use_runtime=True, reporter=reporter, debug=True
        )

    # Save object:
    obj_file = base_filename + ".oj"
    with open(obj_file, "w") as f:
        obj.save(f)

    if elf_format:
        elf_filename = base_filename + "." + elf_format
        api.objcopy(obj, code_image, elf_format, elf_filename)

    # Export code image to some format:
    if bin_format:
        sample_filename = base_filename + "." + bin_format
        api.objcopy(obj, code_image, bin_format, sample_filename)

    return obj
