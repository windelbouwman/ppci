
"""
This module contains a set of handy functions to invoke compilation, linking
and assembling.
"""

import logging
from .target import Target
from .c3 import Builder
from .bf import BrainFuckGenerator
from .irutils import Verifier, Writer
from .codegen import CodeGenerator
from .transform import DeleteUnusedInstructionsPass
from .transform import RemoveAddZeroPass
from .transform import CommonSubexpressionEliminationPass
from .transform import ConstantFolder
from .transform import LoadAfterStorePass
from .transform import CleanPass
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
    """ Construct the given buildfile """
    recipe_loader = RecipeLoader()
    try:
        project = recipe_loader.load_file(buildfile)
    except OSError:
        raise TaskError('Could not load {}'.format(buildfile))

    if project:
        runner = TaskRunner()
        res = runner.run(project, targets)
    else:
        res = 1
        # TODO: fix strange return code. 1 means error?
        # TODO: use exceptions instead..

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
        ir_modules = c3b.build(sources, includes)
        for ircode in ir_modules:
            Verifier().verify(ircode)
    except CompilerError:
        diag.printErrors()
        raise TaskError('Compile errors')
    return ir_modules


def optimize(ircode, do_verify=False):
    """
        Run a bag of tricks against the ir-code.
        This is an in-place operation!
    """
    # Create the verifier:
    verifier = Verifier()
    verifier.verify(ircode)

    # Optimization passes:
    passes = [Mem2RegPromotor(),
              RemoveAddZeroPass(),
              ConstantFolder(),
              CommonSubexpressionEliminationPass(),
              LoadAfterStorePass(),
              DeleteUnusedInstructionsPass(),
              CleanPass()]

    # Brute force 3 times:
    for _ in range(3):
        for pas in passes:
            if do_verify:
                verifier.verify(ircode)
            # verifier.verify(ircode)
            pas.run(ircode)
            # verifier.verify(ircode)

    # One last verify:
    if do_verify:
        verifier.verify(ircode)


def ir_to_code(ir_modules, target, lst_file=None):
    """ Translate the given list of IR-modules into object code for the given
    target """
    logger = logging.getLogger('ir_to_code')
    code_generator = CodeGenerator(target)

    output = ObjectFile()
    output_stream = BinaryOutputStream(output)

    for ircode in ir_modules:
        Verifier().verify(ircode)

        # Code generation:
        logger.debug('Starting code generation for {}'.format(ircode))
        code_generator.generate(ircode, output_stream, dump_file=lst_file)

    return output


def ir_to_python(ircode, f):
    """ Convert ir-code to python code """
    optimize(ircode)
    IrToPython().generate(ircode, f)


def c3compile(sources, includes, target, lst_file=None):
    """ Compile a set of sources into binary format for the given target """
    target = fix_target(target)
    writer = Writer()
    ir_mods = list(c3toir(sources, includes, target))
    if lst_file:
        print('C3 compilation listings for {}'.format(sources), file=lst_file)
        print('Before optimization {}'.format(ir_mods), file=lst_file)
        for ir_module in ir_mods:
            writer.write(ir_module, lst_file)
        print('============', file=lst_file)

    for ircode in ir_mods:
        optimize(ircode, )

    # Write output to listings file:
    if lst_file:
        print('After optimization {}'.format(ir_mods), file=lst_file)
        for ir_module in ir_mods:
            writer.write(ir_module, lst_file)
        print('============', file=lst_file)
    obj = ir_to_code(ir_mods, target, lst_file=lst_file)
    return obj


def bf2ir(source):
    """ Compile brainfuck source into ir code """
    ircode = BrainFuckGenerator().generate(source)
    return ircode


def bfcompile(source, target, lst_file=None):
    """ Compile brainfuck source into binary format for the given target """
    if lst_file:
        print('brainfuck compilation listings', file=lst_file)
    ircode = bf2ir(source)
    if lst_file:
        print(
            'Before optimization {} {}'.format(ircode, ircode.stats()),
            file=lst_file)
        writer = Writer()
        print('==========================', file=lst_file)
        writer.write(ircode, lst_file)
        print('==========================', file=lst_file)
    optimize(ircode)

    if lst_file:
        print(
            'After optimization {} {}'.format(ircode, ircode.stats()),
            file=lst_file)
        writer = Writer()
        print('==========================', file=lst_file)
        writer.write(ircode, lst_file)
        print('==========================', file=lst_file)

    target = fix_target(target)
    return ir_to_code([ircode], target, lst_file=lst_file)


def link(objects, layout, target, lst_file=None):
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
        hexfile = HexFile()
        hexfile.add_region(image.location, image.data)
        with open(output_filename, 'w') as output_file:
            hexfile.save(output_file)
    else:
        raise NotImplementedError("output format not implemented")
