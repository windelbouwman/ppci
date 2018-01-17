import io
from .builder import CBuilder
from .preprocessor import CTokenPrinter, CPreProcessor
from .options import COptions
from ...utils.reporting import DummyReportGenerator


def preprocess(f, output_file, coptions=None):
    """ Pre-process a file into the other file. """
    if coptions is None:
        coptions = COptions()
    preprocessor = CPreProcessor(coptions)
    filename = f.name if hasattr(f, 'name') else None
    tokens = preprocessor.process(f, filename=filename)
    CTokenPrinter().dump(tokens, file=output_file)


def c_to_ir(
        source: io.TextIOBase, march, coptions=None, reporter=None):
    """ C to ir translation.

    Args:
        source (file-like object): The C source to compile.
        march (str): The targetted architecture.
        coptions: C specific compilation options.

    Returns:
        An :class:`ppci.ir.Module`.
    """

    if not reporter:  # pragma: no cover
        reporter = DummyReportGenerator()

    if not coptions:  # pragma: no cover
        coptions = COptions()

    from ...api import get_arch
    march = get_arch(march)
    cbuilder = CBuilder(march.info, coptions)
    assert isinstance(source, io.TextIOBase)
    if hasattr(source, 'name'):
        filename = getattr(source, 'name')
    else:
        filename = None

    ir_module = cbuilder.build(source, filename, reporter=reporter)
    return ir_module
