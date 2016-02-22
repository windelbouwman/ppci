
"""
This module contains a set of handy functions to invoke compilation, linking
and assembling.
"""

import logging
import os
import stat
import xml
from .arch.target import Target
from .c3 import Builder
from .bf import BrainFuckGenerator
from .fortran import FortranBuilder
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
from .utils.hexfile import HexFile
from .utils.elffile import ElfFile
from .tasks import TaskError, TaskRunner
from .recipe import RecipeLoader
from .common import CompilerError, DiagnosticsManager
from .ir2py import IrToPython


def fix_target(target_name):
    """ Try to return an instance of the Target class.
        target_name can be in the form of arch:option1:option2
    """
    # TODO: this is ugly, but is works:
    from .arch.target_list import get_arch
    # TODO: fix this recursive import different
    if isinstance(target_name, Target):
        return target_name
    elif isinstance(target_name, str):
        if ':' in target_name:
            # We have target with options attached
            l = target_name.split(':')
            return get_arch(l[0], options=tuple(l[1:]))
        else:
            return get_arch(target_name)
    raise TaskError('Invalid target {}'.format(target_name))


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
    assembler = fix_target(march).assembler
    source = fix_file(source)
    output = ObjectFile()
    logger.debug('Assembling into code section')
    ostream = BinaryOutputStream(output)
    ostream.select_section('code')
    try:
        assembler.prepare()
        assembler.assemble(source, ostream, diag)
        assembler.flush()
    except CompilerError as ex:
        diag.error(ex.msg, ex.loc)
        diag.print_errors()
        raise TaskError('Errors during assembling')
    return output


def c3toir(sources, includes, target, reporter=DummyReportGenerator()):
    """ Compile c3 sources to ir code using the includes and for the given
    target """
    logger = logging.getLogger('c3c')
    logger.debug('C3 compilation started')
    target = fix_target(target)
    sources = [fix_file(fn) for fn in sources]
    includes = [fix_file(fn) for fn in includes]
    diag = DiagnosticsManager()
    c3b = Builder(diag, target)

    try:
        _, ir_modules = c3b.build(sources, includes)
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

    return ir_modules


def optimize(ir_module, reporter=DummyReportGenerator()):
    """
        Run a bag of tricks against the ir-code.
        This is an in-place operation!
    """
    logger = logging.getLogger('optimize')
    logger.info('Optimizing module %s', ir_module.name)

    # Create the verifier:
    verifier = Verifier()

    # Optimization passes (bag of tricks) run them three times:
    opt_passes = [Mem2RegPromotor(),
                  RemoveAddZeroPass(),
                  ConstantFolder(),
                  CommonSubexpressionEliminationPass(),
                  LoadAfterStorePass(),
                  DeleteUnusedInstructionsPass(),
                  CleanPass()] * 3

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


def ir_to_object(ir_modules, march, reporter=DummyReportGenerator()):
    """ Translate the given list of IR-modules into object code for the given
    target """
    logger = logging.getLogger('ir_to_code')
    code_generator = CodeGenerator(march)
    verifier = Verifier()

    output = ObjectFile()
    output_stream = BinaryOutputStream(output)

    for ir_module in ir_modules:
        verifier.verify(ir_module)

        # Code generation:
        logger.debug('Starting code generation for %s', ir_module.name)
        code_generator.generate(ir_module, output_stream, reporter=reporter)

    reporter.message('All modules generated!')
    return output


def ir_to_python(ir_modules, f, reporter=DummyReportGenerator()):
    """ Convert ir-code to python code """
    generator = IrToPython()
    generator.f = f
    generator.header()
    for ir_module in ir_modules:
        optimize(ir_module, reporter=reporter)
        reporter.message('Optimized module:')
        reporter.dump_ir(ir_module)
        generator.generate(ir_module, f)


def c3c(sources, includes, march, reporter=DummyReportGenerator()):
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
    march = fix_target(march)
    ir_modules = list(c3toir(sources, includes, march, reporter=reporter))

    for ircode in ir_modules:
        optimize(ircode, reporter=reporter)

    return ir_to_object(ir_modules, march, reporter=reporter)


def bf2ir(source, target):
    """ Compile brainfuck source into ir code """
    target = fix_target(target)
    ircode = BrainFuckGenerator(target).generate(source)
    return ircode


def fortran_to_ir(source):
    """ Translate fortran source into IR-code """
    builder = FortranBuilder()
    ir_modules = builder.build(source)
    return ir_modules


def bfcompile(source, target, reporter=DummyReportGenerator()):
    """ Compile brainfuck source into binary format for the given target """
    reporter.message('brainfuck compilation listings')
    target = fix_target(target)
    ir_module = bf2ir(source, target)
    reporter.message(
        'Before optimization {} {}'.format(ir_module, ir_module.stats()))
    reporter.dump_ir(ir_module)
    optimize(ir_module, reporter=reporter)
    return ir_to_object([ir_module], target, reporter=reporter)


def fortrancompile(sources, target, reporter=DummyReportGenerator()):
    """ Compile fortran code to target """
    # TODO!
    ir_modules = fortran_to_ir(sources[0])
    return ir_to_object(ir_modules, target, reporter=reporter)


def link(
        objects, layout, march,
        use_runtime=False, partial_link=False,
        reporter=DummyReportGenerator()):
    """ Links the iterable of objects into one using the given layout.

    """
    objects = [fix_object(obj) for obj in objects]
    layout = fix_layout(layout)
    march = fix_target(march)
    if use_runtime:
        objects.append(march.runtime)
    linker = Linker(march, reporter)
    try:
        output_obj = linker.link(objects, layout)
    except CompilerError as err:
        raise TaskError(err.msg)
    return output_obj


def objcopy(obj, image_name, fmt, output_filename):
    """ Copy some parts of an object file to an output """
    if fmt not in ['bin', 'hex', 'elf']:
        raise TaskError('Only bin, elf and hex formats supported')

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
    else:  # pragma: no cover
        raise NotImplementedError("output format not implemented")
