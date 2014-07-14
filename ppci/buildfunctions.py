
"""
    This module contains a set of handy functions to invoke compilation,
        linking
    and assembling.
"""

import logging
from .target import Target
from .c3 import Builder
from .irutils import Verifier
from .codegen import CodeGenerator
from .transform import CleanPass, RemoveAddZero
from .linker import Linker
from .layout import Layout, load_layout
from .target.target_list import targets
from .outstream import BinaryOutputStream
from .objectfile import ObjectFile, load_object
from . import DiagnosticsManager
from .tasks import TaskError, TaskRunner
from .recipe import RecipeLoader


def fix_target(tg):
    """ Try to return an instance of the Target class """
    if isinstance(tg, Target):
        return tg
    elif isinstance(tg, str):
        if tg in targets:
            return targets[tg]
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
        with open(o, 'r') as f:
            return load_object(f)
    else:
        raise TaskError('Cannot use {} as objectfile'.format(o))


def fix_layout(l):
    if isinstance(l, Layout):
        return l
    elif hasattr(l, 'read'):
        # Assume file handle
        return load_layout(l)
    elif isinstance(l, str):
        with open(l, 'r') as f:
            return load_layout(f)
    else:
        raise TaskError('Cannot use {} as layout'.format(l))


def construct(buildfile, targets=[]):
    recipe_loader = RecipeLoader()
    try:
        project = recipe_loader.load_file(buildfile)
    except OSError:
        raise TaskError('Could not construct {}'.format(buildfile))
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


def ir_to_code(ircode):
    pass


def c3compile(sources, includes, target):
    """ Compile a set of sources into binary format for the given target """
    logger = logging.getLogger('c3c')
    target = fix_target(target)
    output = ObjectFile()
    cg = CodeGenerator(target)

    output_stream = BinaryOutputStream(output)

    for ircode in c3toir(sources, includes, target):
        Verifier().verify(ircode)

        # Optimization passes:
        # CleanPass().run(ircode)
        Verifier().verify(ircode)
        # RemoveAddZero().run(ircode)
        Verifier().verify(ircode)
        # CleanPass().run(ircode)
        Verifier().verify(ircode)

        # Code generation:
        d = {'ircode': ircode}
        logger.debug('Starting code generation for {}'.format(ircode), extra=d)

        cg.generate(ircode, output_stream)

    return output


def link(objects, layout, target):
    """ Links the iterable of objects into one using the given layout """
    objects = list(map(fix_object, objects))
    layout = fix_layout(layout)
    target = fix_target(target)
    linker = Linker(target)
    output_obj = linker.link(objects, layout)
    return output_obj
