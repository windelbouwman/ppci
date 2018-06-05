
"""
The api module contains a set of handy functions to invoke compilation,
linking and assembling.
"""

import io
import logging
import os
import stat
import xml
from .lang.c import preprocess, c_to_ir, COptions
from .lang.c3 import c3_to_ir
from .lang.bf import bf_to_ir
from .lang.fortran import fortran_to_ir
from .lang.llvmir import llvm_to_ir
from .lang.pascal import PascalBuilder
from .lang.ws import ws_to_ir
from .lang.python import python_to_ir, ir_to_python
from .wasm import wasm_to_ir, read_wasm
from .irutils import verify_module
from .utils.reporting import DummyReportGenerator, HtmlReportGenerator
from .opt.transform import DeleteUnusedInstructionsPass
from .opt.transform import RemoveAddZeroPass
from .opt import CommonSubexpressionEliminationPass
from .opt import ConstantFolder
from .opt import LoadAfterStorePass
from .opt import CleanPass
from .opt.mem2reg import Mem2RegPromotor
from .opt.cjmp import CJumpPass
from .opt.tailcall import TailCallOptimization
from .codegen import CodeGenerator
from .binutils.linker import link
from .binutils.outstream import BinaryOutputStream, TextOutputStream
from .binutils.outstream import MasterOutputStream, FunctionOutputStream
from .binutils.objectfile import ObjectFile, get_object
from .binutils.debuginfo import DebugAddress, DebugInfo
from .binutils.disasm import Disassembler
from .format.hexfile import HexFile
from .format.elf import write_elf
from .format.exefile import ExeWriter
from .format import uboot_image
from .build.tasks import TaskError, TaskRunner
from .build.recipe import RecipeLoader
from .common import CompilerError, DiagnosticsManager, get_file
from .arch import get_arch, get_current_arch

# When using 'from ppci.api import *' include the following:
__all__ = [
    'asm', 'c3c', 'cc', 'link', 'objcopy', 'bfcompile', 'construct',
    'optimize', 'preprocess',
    'get_arch', 'get_current_arch', 'is_platform_supported',
    'ir_to_object', 'ir_to_python',
    'bf_to_ir', 'ws_to_ir']


def get_reporter(reporter):
    if reporter is None:
        return DummyReportGenerator()
    elif isinstance(reporter, str):
        if reporter.endswith('.html'):
            f = open(reporter, 'wt', encoding='utf8')
            r = HtmlReportGenerator(f)
            r.header()
            return r
        else:
            raise ValueError(
                'Cannot determine report type for {}'.format(reporter))
    else:
        return reporter


def is_platform_supported():
    """ Determine if this platform is supported """
    return get_current_arch() is not None


def construct(buildfile, targets=()):
    """ Construct the given buildfile.

    Raise task error if something goes wrong.
    """
    # Ensure file:
    buildfile = get_file(buildfile)
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


def asm(source, march, debug=False):
    """ Assemble the given source for machine march.

    Args:
        source (str): can be a filename or a file like object.
        march (str): march can be a :class:`ppci.arch.arch.Architecture`
            instance or a string indicating the machine architecture.
        debug: generate debugging information

    Returns:
        A :class:`ppci.binutils.objectfile.ObjectFile` object

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
    source = get_file(source)
    obj = ObjectFile(march)
    if debug:
        obj.debug_info = DebugInfo()
    logger.debug('Assembling into code section')
    ostream = BinaryOutputStream(obj)
    ostream.select_section('code')
    try:
        assembler.prepare()
        assembler.assemble(source, ostream, diag, debug=debug)
        assembler.flush()
    except CompilerError as ex:
        diag.error(ex.msg, ex.loc)
        diag.print_errors()
        raise TaskError('Errors during assembling')
    return obj


def disasm(data, march):
    """ Disassemble the given binary data for machine march.

    Args:
        data: a filename or a file like object.
        march: a machine instance or a string indicating the architecture.

    .. doctest::

        >>> import io
        >>> from ppci.api import disasm
        >>> source_file = io.BytesIO([0x77])
        >>> disasm(source_file, 'arm')
    """
    march = get_arch(march)
    disassembler = Disassembler(march)
    f = get_file(data)
    data = f.read()
    f.close()
    ostream = TextOutputStream()
    disassembler.disasm(data, ostream)


OPT_LEVELS = ('0', '1', '2', 's')


def optimize(ir_module, level=0, reporter=None):
    """ Run a bag of tricks against the :doc:`ir-code<ir>`.

    This is an in-place operation!

    Args:
        ir_module (ppci.ir.Module): The ir module to optimize.
        level: The optimization level, 0 is default. Can be 0,1,2 or s
            0: No optimization
            1: some optimization
            2: more optimization
            s: optimize for size
        reporter: Report detailed log to this reporter
    """
    logger = logging.getLogger('optimize')
    level = str(level)

    logger.info('Optimizing module %s level %s', ir_module.name, level)

    if reporter:
        reporter.message('{} before optimization:'.format(ir_module))
        reporter.message('{} {}'.format(ir_module, ir_module.stats()))
        reporter.dump_ir(ir_module)

    assert level in OPT_LEVELS
    if level == '0':
        return

    # TODO: differentiate between optimization levels!

    # Optimization passes (bag of tricks) run them three times:
    opt_passes = [Mem2RegPromotor(),
                  RemoveAddZeroPass(),
                  ConstantFolder(),
                  CommonSubexpressionEliminationPass(),
                  TailCallOptimization(),
                  LoadAfterStorePass(),
                  DeleteUnusedInstructionsPass(),
                  CleanPass()] * 3

    if level == '3':
        opt_passes.append(CJumpPass())

    # Run the passes over the module:
    verify_module(ir_module)
    for opt_pass in opt_passes:
        opt_pass.run(ir_module)
        # reporter.message('{} after {}:'.format(ir_module, opt_pass))
        # reporter.dump_ir(ir_module)

    if reporter:
        # Dump report:
        reporter.message('{} after optimization:'.format(ir_module))
        reporter.message('{} {}'.format(ir_module, ir_module.stats()))
        reporter.dump_ir(ir_module)

    verify_module(ir_module)


def ir_to_stream(
        ir_module, march, output_stream, reporter=None,
        debug=False, opt='speed'):
    """ Translate IR module to output stream.
    """
    march = get_arch(march)

    if not reporter:  # pragma: no cover
        reporter = DummyReportGenerator()

    code_generator = CodeGenerator(march, optimize_for=opt)
    verify_module(ir_module)

    # Code generation:
    code_generator.generate(
        ir_module, output_stream, reporter=reporter, debug=debug)


def ir_to_object(
        ir_modules, march, reporter=None, debug=False,
        opt='speed', outstream=None):
    """ Translate IR-modules into code for the given architecture.

    Args:
        ir_modules: a collection of ir-modules that will be transformed into
            machine code.
        march: the architecture for which to compile.
        reporter: reporter to write compilation report to
        debug (bool): include debugging information
        opt (str): optimization goal. Can be 'speed', 'size' or 'co2'.
        outstream: instruction stream to write instructions to

    Returns:
        ObjectFile: An object file
    """
    march = get_arch(march)

    if not reporter:  # pragma: no cover
        reporter = DummyReportGenerator()

    reporter.heading(2, 'Code generation')
    reporter.message("Target: {}".format(march))

    # Construct output object:
    obj = ObjectFile(march)
    if debug:
        obj.debug_info = DebugInfo()

    # Construct the various instruction streams:
    binary_output_stream = BinaryOutputStream(obj)
    sub_streams = [binary_output_stream]
    instruction_list = []
    sub_streams.append(FunctionOutputStream(instruction_list.append))
    if outstream:
        sub_streams.append(outstream)
    output_stream = MasterOutputStream(sub_streams)

    for ir_module in ir_modules:
        ir_to_stream(
            ir_module, march, output_stream,
            reporter=reporter, debug=debug, opt=opt)

    # TODO: refactor polishing?
    obj.polish()
    reporter.message('All modules generated!')
    reporter.dump_instructions(instruction_list, march)
    return obj


def cc(source: io.TextIOBase, march, coptions=None, opt_level=0,
       debug=False, reporter=None):
    """ C compiler. compiles a single source file into an object file.

    Args:
        source: file like object from which text can be read
        march: The architecture for which to compile
        coptions: options for the C frontend
        debug: Create debug info when set to True

    Returns:
        an object file

    .. doctest::

        >>> import io
        >>> from ppci.api import cc
        >>> source_file = io.StringIO("void main() { int a; }")
        >>> obj = cc(source_file, 'x86_64')
        >>> print(obj)
        CodeObject of 25 bytes

    """
    if not reporter:  # pragma: no cover
        reporter = DummyReportGenerator()

    if not coptions:
        coptions = COptions()

    ir_module = c_to_ir(source, march, coptions=coptions, reporter=reporter)
    reporter.message('{} {}'.format(ir_module, ir_module.stats()))
    reporter.dump_ir(ir_module)
    optimize(ir_module, level=opt_level, reporter=reporter)
    return ir_to_object([ir_module], march, debug=debug, reporter=reporter)


def wasmcompile(source: io.TextIOBase, march, opt_level=2, reporter=None):
    """ Webassembly compile """
    march = get_arch(march)

    if not reporter:  # pragma: no cover
        reporter = DummyReportGenerator()

    wasm_module = read_wasm(source)
    ir_module = wasm_to_ir(
        wasm_module, march.info.get_type_info('ptr'), reporter=reporter)

    # Optimize:
    optimize(ir_module, level=opt_level)

    obj = ir_to_object([ir_module], march, reporter=reporter)
    return obj


def llc(source, march):
    """ Compile llvm assembly source into machine code """
    march = get_arch(march)
    ir_module = llvm_to_ir(source)
    return ir_to_object([ir_module], march)


def c3c(sources, includes, march, opt_level=0, reporter=None, debug=False,
        outstream=None):
    """ Compile a set of sources into binary format for the given target.

    Args:
        sources: a collection of sources that will be compiled.
        includes: a collection of sources that will be used for type
            and function information.
        march: the architecture for which to compile.
        reporter: reporter to write compilation report to
        debug: include debugging information

    Returns:
        An object file

    .. doctest::

        >>> import io
        >>> from ppci.api import c3c
        >>> source_file = io.StringIO("module main; var int a;")
        >>> obj = c3c([source_file], [], 'arm')
        >>> print(obj)
        CodeObject of 4 bytes
    """
    reporter = get_reporter(reporter)
    march = get_arch(march)
    ir_module = \
        c3_to_ir(sources, includes, march, reporter=reporter)

    optimize(ir_module, level=opt_level, reporter=reporter)

    opt_cg = 'size' if opt_level == 's' else 'speed'
    return ir_to_object(
        [ir_module], march, debug=debug, reporter=reporter,
        opt=opt_cg, outstream=outstream)


def pascal(sources, march, opt_level=0, reporter=None):
    """ Compile a set of pascal-sources for the given target.

    Args:
        sources: a collection of sources that will be compiled.
        march: the architecture for which to compile.

    Returns:
        An object file
    """
    diag = DiagnosticsManager()
    march = get_arch(march)
    if not reporter:  # pragma: no cover
        reporter = DummyReportGenerator()
    pascal_builder = PascalBuilder(diag, march.info)

    sources = [get_file(fn) for fn in sources]
    ir_modules = pascal_builder.build(sources)

    return ir_to_object(ir_modules, march, reporter=reporter)


def bfcompile(source, target, reporter=None):
    """ Compile brainfuck source into binary format for the given target

    Args:
        source: a filename or a file like object.
        march: a architecture instance or a string indicating the target.

    Returns:
        A new object.

    .. doctest::

        >>> import io
        >>> from ppci.api import bfcompile
        >>> source_file = io.StringIO(">>[-]<<[->>+<<]")
        >>> obj = bfcompile(source_file, 'arm')
        >>> print(obj) # doctest: +ELLIPSIS
        CodeObject of ... bytes
    """
    if not reporter:
        reporter = DummyReportGenerator()
    reporter.message('brainfuck compilation listings')
    target = get_arch(target)
    ir_module = bf_to_ir(source, target)
    reporter.message(
        'Before optimization {} {}'.format(ir_module, ir_module.stats()))
    reporter.dump_ir(ir_module)
    optimize(ir_module, reporter=reporter)
    return ir_to_object([ir_module], target, reporter=reporter)


def pycompile(source, march, reporter=None):
    """ Compile a piece of python code to machine code.

    Note that the python code must be type annotated for this
    to work.
    """
    march = get_arch(march)
    ir_module = python_to_ir(source)
    return ir_to_object([ir_module], march)


def fortrancompile(sources, target, reporter=DummyReportGenerator()):
    """ Compile fortran code to target """
    # TODO!
    ir_modules = fortran_to_ir(sources[0])
    return ir_to_object(ir_modules, target, reporter=reporter)


def objcopy(obj: ObjectFile, image_name: str, fmt: str, output_filename):
    """ Copy some parts of an object file to an output """
    fmts = ['bin', 'hex', 'elf', 'exe', 'ldb', 'uimage']
    if fmt not in fmts:
        formats = ', '.join(fmts[:-1]) + ' and ' + fmts[-1]
        raise TaskError('Only {} are supported'.format(formats))

    obj = get_object(obj)
    if fmt == "bin":
        image = obj.get_image(image_name)
        with open(output_filename, 'wb') as output_file:
            output_file.write(image.data)
    elif fmt == "elf":
        with open(output_filename, 'wb') as output_file:
            write_elf(obj, output_file)
        status = os.stat(output_filename)
        os.chmod(output_filename, status.st_mode | stat.S_IEXEC)
    elif fmt == "hex":
        image = obj.get_image(image_name)
        hexfile = HexFile()
        hexfile.add_region(image.address, image.data)
        with open(output_filename, 'wt', encoding='utf8') as output_file:
            hexfile.save(output_file)
    elif fmt == 'ldb':
        # TODO: fix this some other way to extract debug info
        with open(output_filename, 'wt', encoding='utf8') as output_file:
            write_ldb(obj, output_file)
    elif fmt == 'uimage':
        image = obj.get_image(image_name)
        uboot_architectures = {
            'arm': uboot_image.Architecture.ARM,
            'or1k': uboot_image.Architecture.OPENRISC,
            'xtensa': uboot_image.Architecture.XTENSA,
        }
        with open(output_filename, 'wb') as f:
            uboot_image.write_uboot_image(
                f, image.data,
                load_address=image.address, entry_point=image.address,
                arch=uboot_architectures[obj.arch.name])
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
        name = var.name
        address = fx(var.address)
        print(
            'global: {} <0> @ 0x{:08X}'.format(name, address),
            file=output_file)
