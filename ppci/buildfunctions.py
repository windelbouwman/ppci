
"""
    This module contains a set of handy functions to invoke compilation,
        linking
    and assembling.
"""

import logging
from .target import Target
from .c3 import Builder
from .bf import BrainFuckGenerator
from .irutils import Verifier
from .codegen import CodeGenerator
from .transform import CleanPass, DeleteUnusedInstructionsPass
from .transform import RemoveAddZeroPass, CommonSubexpressionEliminationPass
from .transform import ConstantFolder, LoadAfterStorePass
from .mem2reg import Mem2RegPromotor
from .binutils.linker import Linker
from .binutils.layout import Layout, load_layout
from .target import get_target
from .binutils.outstream import BinaryOutputStream
from .binutils.objectfile import ObjectFile, load_object
from .utils.hexfile import HexFile
from . import DiagnosticsManager
from .tasks import TaskError, TaskRunner
from .recipe import RecipeLoader
from .common import CompilerError
from .ir2py import IrToPython


def fix_target(tg):
    """ Try to return an instance of the Target class """
    if isinstance(tg, Target):
        return tg
    elif isinstance(tg, str):
        return get_target(tg)
    raise TaskError('Invalid target {}'.format(tg))


def fix_file(f):
    """ Determine if argument is a file like object or make it so! """
    if hasattr(f, 'read'):
        # Assume this is a file like object
        return f
    elif isinstance(f, str):
        return open(f, 'r')
    else:
        raise TaskError('cannot use {} as input'.format(f))


def fix_object(o):
    if isinstance(o, ObjectFile):
        return o
    elif isinstance(o, str):
        try:
            with open(o, 'r') as f:
                return load_object(f)
        except OSError:
            raise TaskError('Could not load {}'.format(o))
    else:
        raise TaskError('Cannot use {} as objectfile'.format(o))


def fix_layout(l):
    if isinstance(l, Layout):
        return l
    elif hasattr(l, 'read'):
        # Assume file handle
        return load_layout(l)
    elif isinstance(l, str):
        try:
            with open(l, 'r') as f:
                return load_layout(f)
        except OSError:
            raise TaskError('Could not load {}'.format(l))
    else:
        raise TaskError('Cannot use {} as layout'.format(l))


def construct(buildfile, targets=[]):
    recipe_loader = RecipeLoader()
    try:
        project = recipe_loader.load_file(buildfile)
    except OSError:
        raise TaskError('Could not load {}'.format(buildfile))
        project = None

    if project:
        runner = TaskRunner()
        res = runner.run(project, targets)
    else:
        res = 1

    return res


def assemble(source, target):
    """ Invoke the assembler on the given source, returns an object containing
        the output. """
    logger = logging.getLogger('assemble')
    target = fix_target(target)
    source = fix_file(source)
    output = ObjectFile()
    assembler = target.assembler
    logger.debug('Assembling into code section')
    ostream = BinaryOutputStream(output)
    ostream.select_section('code')
    assembler.prepare()
    assembler.assemble(source, ostream)
    assembler.flush()
    return output


def c3toir(sources, includes, target):
    """ Compile c3 sources to ir code """
    logger = logging.getLogger('c3c')
    logger.debug('C3 compilation started')
    target = fix_target(target)
    sources = [fix_file(fn) for fn in sources]
    includes = [fix_file(fn) for fn in includes]
    diag = DiagnosticsManager()
    c3b = Builder(diag, target)

    ir_modules = []
    for ircode in c3b.build(sources, includes):
        if not ircode:
            # Something went wrong, do not continue the code generation
            continue

        Verifier().verify(ircode)
        ir_modules.append(ircode)

    if not c3b.ok:
        diag.printErrors()
        raise TaskError('Compile errors')
    return ir_modules


def optimize(ircode, do_verify=False):
    """
        Run a bag of tricks against the ir-code.
        This is an in-place operation!
    """
    verifier = Verifier()
    if do_verify:
        verifier.verify(ircode)
    # Optimization passes:
    # CleanPass().run(ircode)

    Mem2RegPromotor().run(ircode)
    DeleteUnusedInstructionsPass().run(ircode)
    RemoveAddZeroPass().run(ircode)
    # CommonSubexpressionEliminationPass().run(ircode)
    # LoadAfterStorePass().run(ircode)
    DeleteUnusedInstructionsPass().run(ircode)
    # CleanPass().run(ircode)

    if do_verify:
        verifier.verify(ircode)


def ir_to_code(ir_modules, target):
    logger = logging.getLogger('ir_to_code')
    cg = CodeGenerator(target)

    output = ObjectFile()
    output_stream = BinaryOutputStream(output)

    for ircode in ir_modules:
        Verifier().verify(ircode)

        # Code generation:
        logger.debug('Starting code generation for {}'.format(ircode))
        cg.generate(ircode, output_stream)

    return output


def ir_to_python(ircode, f):
    """ Convert ir-code to python code """
    optimize(ircode)
    IrToPython().generate(ircode, f)


def c3compile(sources, includes, target):
    """ Compile a set of sources into binary format for the given target """
    target = fix_target(target)
    ir_mods = list(c3toir(sources, includes, target))
    for ircode in ir_mods:
        optimize(ircode)
    return ir_to_code(ir_mods, target)


def bf2ir(source):
    """ Compile brainfuck source into ir code """
    ircode = BrainFuckGenerator().generate(source)
    optimize(ircode)
    return ircode


def bfcompile(source, target):
    """ Compile brainfuck source into binary format for the given target """
    ircode = bf2ir(source)
    optimize(ircode)
    target = fix_target(target)
    return ir_to_code([ircode], target)


def link(objects, layout, target):
    """ Links the iterable of objects into one using the given layout """
    objects = list(map(fix_object, objects))
    layout = fix_layout(layout)
    target = fix_target(target)
    linker = Linker(target)
    try:
        output_obj = linker.link(objects, layout)
    except CompilerError as err:
        raise TaskError(err.msg)
    return output_obj


def objcopy(obj, image_name, fmt, output_filename):
    """ Copy some parts of an object file to an output """
    if fmt not in ['bin', 'hex']:
        raise TaskError('Only bin or hex formats supported')

    obj = fix_object(obj)
    image = obj.get_image(image_name)
    if fmt == "bin":
        with open(output_filename, 'wb') as output_file:
            output_file.write(image.data)
    elif fmt == "hex":
        hf = HexFile()
        hf.add_region(image.location, image.data)
        with open(output_filename, 'w') as output_file:
            hf.save(output_file)
    else:
        raise NotImplementedError("output format not implemented")
