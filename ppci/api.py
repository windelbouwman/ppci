
"""
This module contains a set of handy functions to invoke compilation, linking
and assembling.
"""

import logging
import warnings
import os
import stat
import xml
from .arch.arch import Architecture
from .lang.c import CBuilder
from .lang.c3 import C3Builder
from .lang.bf import BrainFuckGenerator
from .lang.fortran import FortranBuilder
from .irutils import Verifier
from .utils.reporting import DummyReportGenerator
from .opt.transform import DeleteUnusedInstructionsPass
from .opt.transform import RemoveAddZeroPass
from .opt.transform import CommonSubexpressionEliminationPass
from .opt.transform import ConstantFolder
from .opt.transform import LoadAfterStorePass
from .opt.transform import CleanPass
from .opt.mem2reg import Mem2RegPromotor
from .codegen import CodeGenerator
from .binutils.linker import Linker
from .binutils.layout import Layout, load_layout
from .binutils.outstream import BinaryOutputStream
from .binutils.objectfile import ObjectFile, load_object
from .binutils.debuginfo import DebugDb, DebugAddress
from .utils.hexfile import HexFile
from .utils.elffile import ElfFile
from .utils.exefile import ExeWriter
from .tasks import TaskError, TaskRunner
from .recipe import RecipeLoader
from .common import CompilerError, DiagnosticsManager
from .ir2py import IrToPython
from .arch.target_list import create_arch

# When using 'from ppci.api import *' include the following:
__all__ = [
    'asm', 'c3c', 'link', 'objcopy', 'bfcompile', 'construct', 'optimize',
    'get_arch']


def get_arch(arch):
    """ Try to return an architecture instance.
        arch can be a string in the form of arch:option1:option2
    """
    if isinstance(arch, Architecture):
        return arch
    elif isinstance(arch, str):
        if ':' in arch:
            # We have target with options attached
            l = arch.split(':')
            return create_arch(l[0], options=tuple(l[1:]))
        else:
            return create_arch(arch)
    raise TaskError('Invalid architecture {}'.format(arch))


def fix_file(f):
    """ Determine if argument is a file like object or make it so! """
    if hasattr(f, 'read'):
        # Assume this is a file like object
        return f
    elif isinstance(f, str):
        try:
            return open(f, 'r')
        except FileNotFoundError:
            raise TaskError('Cannot open {}'.format(f))
    else:
        raise TaskError('Cannot open {}'.format(f))


def fix_object(obj):
    """ Try hard to load an object """
    if not isinstance(obj, ObjectFile):
        f = fix_file(obj)
        obj = load_object(f)
        f.close()
    return obj


def fix_layout(l):
    if isinstance(l, Layout):
        return l
    else:
        f = fix_file(l)
        layout = load_layout(f)
        f.close()
        return layout


def construct(buildfile, targets=()):
    """
        Construct the given buildfile.
        Raise task error if something goes wrong.
    """
    # Ensure file:
    buildfile = fix_file(buildfile)
    recipe_loader = RecipeLoader()
    try:
        project = recipe_loader.load_file(buildfile)
    except OSError:
        raise TaskError('Could not load {}'.format(buildfile))
    except xml.parsers.expat.ExpatError:
        raise TaskError('Invalid xml')
    finally:
        buildfile.close()

    if not project:
        raise TaskError('No project loaded')

    runner = TaskRunner()
    runner.run(project, list(targets))


def asm(source, march):
    """ Assemble the given source for machine march.

    source can be a filename or a file like object.
    march can be a machine instance or a string indicating the target.

    For example:

    .. doctest::

        >>> import io
        >>> from ppci.api import asm
        >>> source_file = io.StringIO("db 0x77")
        >>> obj = asm(source_file, 'arm')
        >>> print(obj)
        CodeObject of 1 bytes
    """
    logger = logging.getLogger('assemble')
    diag = DiagnosticsManager()
    march = get_arch(march)
    assembler = march.assembler
    source = fix_file(source)
    obj = ObjectFile(march)
    logger.debug('Assembling into code section')
    ostream = BinaryOutputStream(obj)
    ostream.select_section('code')
    try:
        assembler.prepare()
        assembler.assemble(source, ostream, diag)
        assembler.flush()
    except CompilerError as ex:
        diag.error(ex.msg, ex.loc)
        diag.print_errors()
        raise TaskError('Errors during assembling')
    return obj


def c3toir(sources, includes, march, reporter=DummyReportGenerator()):
    """ Compile c3 sources to ir code using the includes and for the given
    target """
    logger = logging.getLogger('c3c')
    logger.debug('C3 compilation started')
    march = get_arch(march)
    sources = [fix_file(fn) for fn in sources]
    includes = [fix_file(fn) for fn in includes]
    diag = DiagnosticsManager()
    c3b = C3Builder(diag, march)

    try:
        _, ir_modules, debug_info = c3b.build(sources, includes)
        for ircode in ir_modules:
            Verifier().verify(ircode)
    except CompilerError as ex:
        diag.error(ex.msg, ex.loc)
        diag.print_errors()
        raise TaskError('Compile errors')

    reporter.message('C3 compilation listings for {}'.format(sources))
    for ir_module in ir_modules:
        reporter.message('{} {}'.format(ir_module, ir_module.stats()))
        reporter.dump_ir(ir_module)

    return ir_modules, debug_info


def optimize(ir_module, reporter=None, debug_db=None):
    """
        Run a bag of tricks against the ir-code.
        This is an in-place operation!
    """
    logger = logging.getLogger('optimize')
    logger.info('Optimizing module %s', ir_module.name)

    if not reporter:
        reporter = DummyReportGenerator()

    if not debug_db:
        debug_db = DebugDb()

    # Create the verifier:
    verifier = Verifier()

    # Optimization passes (bag of tricks) run them three times:
    opt_passes = [Mem2RegPromotor(debug_db),
                  RemoveAddZeroPass(debug_db),
                  ConstantFolder(debug_db),
                  CommonSubexpressionEliminationPass(debug_db),
                  LoadAfterStorePass(debug_db),
                  DeleteUnusedInstructionsPass(debug_db),
                  CleanPass(debug_db)] * 3

    # Run the passes over the module:
    verifier.verify(ir_module)
    for opt_pass in opt_passes:
        opt_pass.run(ir_module)
        # reporter.message('{} after {}:'.format(ir_module, opt_pass))
        # reporter.dump_ir(ir_module)
    verifier.verify(ir_module)

    # Dump report:
    reporter.message('{} after optimization:'.format(ir_module))
    reporter.message('{} {}'.format(ir_module, ir_module.stats()))
    reporter.dump_ir(ir_module)


def ir_to_object(
        ir_modules, march, debug_db, reporter=None, opt=None):
    """ Translate the given list of IR-modules into object code for the given
    architecture """
    if not reporter:
        reporter = DummyReportGenerator()
    march = get_arch(march)
    code_generator = CodeGenerator(march, debug_db)
    verifier = Verifier()

    obj = ObjectFile(march)
    output_stream = BinaryOutputStream(obj)

    for ir_module in ir_modules:
        verifier.verify(ir_module)

        # Code generation:
        code_generator.generate(ir_module, output_stream, reporter=reporter)

    # TODO: refactor polishing?
    obj.polish()
    reporter.message('All modules generated!')
    return obj


def ir_to_python(ir_modules, f, reporter=None):
    """ Convert ir-code to python code """
    if not reporter:
        reporter = DummyReportGenerator()
    generator = IrToPython(f)
    generator.header()
    for ir_module in ir_modules:
        optimize(ir_module, reporter=reporter)
        reporter.message('Optimized module:')
        reporter.dump_ir(ir_module)
        generator.generate(ir_module)


def cc(source, march, reporter=None):
    """ C compiler. compiles a single source file into an object file """
    if not reporter:
        reporter = DummyReportGenerator()
    march = get_arch(march)
    cbuilder = CBuilder(march)
    cbuilder.build(source)
    raise NotImplementedError('TODO')


def c3c(sources, includes, march, reporter=None, debug=False):
    """
    Compile a set of sources into binary format for the given target.

    For example:

    .. doctest::

        >>> import io
        >>> from ppci.api import c3c
        >>> source_file = io.StringIO("module main; var int a;")
        >>> obj = c3c([source_file], [], 'arm')
        >>> print(obj)
        CodeObject of 4 bytes
    """
    if not reporter:
        reporter = DummyReportGenerator()
    march = get_arch(march)
    ir_modules, debug_db = \
        c3toir(sources, includes, march, reporter=reporter)

    for ircode in ir_modules:
        optimize(ircode, reporter=reporter)

    return ir_to_object(ir_modules, march, debug_db, reporter=reporter)


def bf2ir(source, target):
    """ Compile brainfuck source into ir code """
    target = get_arch(target)
    ircode = BrainFuckGenerator(target).generate(source)
    return ircode


def fortran_to_ir(source):
    """ Translate fortran source into IR-code """
    builder = FortranBuilder()
    ir_modules = builder.build(source)
    return ir_modules


def bfcompile(source, target, reporter=None):
    """ Compile brainfuck source into binary format for the given target

    source can be a filename or a file like object.
    march can be a machine instance or a string indicating the target.

    For example:

    .. doctest::

        >>> import io
        >>> from ppci.api import bfcompile
        >>> source_file = io.StringIO(">>[-]<<[->>+<<]")
        >>> obj = bfcompile(source_file, 'arm')
    """
    if not reporter:
        reporter = DummyReportGenerator()
    reporter.message('brainfuck compilation listings')
    target = get_arch(target)
    ir_module = bf2ir(source, target)
    reporter.message(
        'Before optimization {} {}'.format(ir_module, ir_module.stats()))
    reporter.dump_ir(ir_module)
    optimize(ir_module, reporter=reporter)
    debug_db = DebugDb()
    return ir_to_object([ir_module], target, debug_db, reporter=reporter)


def fortrancompile(sources, target, reporter=DummyReportGenerator()):
    """ Compile fortran code to target """
    # TODO!
    ir_modules = fortran_to_ir(sources[0])
    return ir_to_object(ir_modules, target, reporter=reporter)


def link(
        objects, layout=None, arch=None, use_runtime=False, partial_link=False,
        reporter=None, debug=False):
    """ Links the iterable of objects into one using the given layout.

    """
    if not reporter:
        reporter = DummyReportGenerator()

    objects = [fix_object(obj) for obj in objects]
    if not objects:
        raise ValueError('Please provide some objects as input')

    if layout:
        layout = fix_layout(layout)

    if arch:
        warnings.warn('No need to give arch here!', DeprecationWarning)
        march = get_arch(arch)
    else:
        march = objects[0].arch

    if use_runtime:
        objects.append(march.runtime)

    linker = Linker(march, reporter)
    try:
        output_obj = linker.link(objects, layout=layout, debug=debug)
    except CompilerError as err:
        raise TaskError(err.msg)
    return output_obj


def objcopy(obj, image_name, fmt, output_filename):
    """ Copy some parts of an object file to an output """
    fmts = ['bin', 'hex', 'elf', 'exe', 'ldb']
    if fmt not in fmts:
        formats = ', '.join(fmts[:-1]) + ' and ' + fmts[-1]
        raise TaskError('Only {} are supported'.format(formats))

    obj = fix_object(obj)
    if fmt == "bin":
        image = obj.get_image(image_name)
        with open(output_filename, 'wb') as output_file:
            output_file.write(image.data)
    elif fmt == "elf":
        elf_file = ElfFile()
        with open(output_filename, 'wb') as output_file:
            elf_file.save(output_file, obj)
        status = os.stat(output_filename)
        os.chmod(output_filename, status.st_mode | stat.S_IEXEC)
    elif fmt == "hex":
        image = obj.get_image(image_name)
        hexfile = HexFile()
        hexfile.add_region(image.location, image.data)
        with open(output_filename, 'w') as output_file:
            hexfile.save(output_file)
    elif fmt == 'ldb':
        # TODO: fix this some other way to extract debug info
        with open(output_filename, 'w') as output_file:
            write_ldb(obj, output_file)
    elif fmt == 'exe':
        writer = ExeWriter()
        with open(output_filename, 'wb') as output_file:
            writer.write(obj, output_file)
    else:  # pragma: no cover
        raise NotImplementedError("output format not implemented")


def write_ldb(obj, output_file):
    """ Export debug info from object to ldb format.
        See for example:
        - https://github.com/embedded-systems/qr/blob/master/in4073_xufo/
          x32-debug/ex2.dbg
    """
    def fx(address):
        assert isinstance(address, DebugAddress)
        return obj.get_section(address.section).address + address.offset
    debug_info = obj.debug_info
    for debug_location in debug_info.locations:
        filename = debug_location.loc.filename
        row = debug_location.loc.row
        address = fx(debug_location.address)
        print(
            'line: "{}":{} @ 0x{:08X}'.format(filename, row, address),
            file=output_file)
    for func in debug_info.functions:
        name = func.name
        address = fx(func.begin)
        print(
            'function: {} <0> @ 0x{:08X}'.format(name, address),
            file=output_file)
    for var in debug_info.variables:
        if var.scope != 'global':
            continue
        name = var.name
        address = fx(var.address)
        print(
            'global: {} <0> @ 0x{:08X}'.format(name, address),
            file=output_file)
