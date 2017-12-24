import logging
import io

from .base import SourceCodeProgram
from ..utils.reporting import DummyReportGenerator
from ..irutils import Verifier
from ..common import CompilerError, DiagnosticsManager, get_file
from ..build.tasks import TaskError

from ..lang.c3 import C3Builder


class C3Program(SourceCodeProgram):
    """ C3 is a novel programming language ispired by C, but avoiding some
    of its contraptions.

    The items in a C3Program are strings.
    """

    def _check_items(self, items):
        for item in items:
            assert isinstance(item, str)
        return items

    def _copy(self):
        return self._new('c3', [item for item in self.items])

    def _get_report(self, html):
        return '\n\n## ==========\n\n'.join(self.items)

    def to_ir(self, includes=None, march=None, reporter=None):
        """ Compile C3 to PPCI IR for the given architecture.
        """
        # todo: why would we have to specify an arch here?
        # circular ref, maybe move get_arch to utils?
        from ppci.api import get_arch
        from ppci.api import get_current_arch

        includes = [] if includes is None else includes
        march = get_current_arch() if march is None else get_arch(march)

        logger = logging.getLogger('c3c')
        if not reporter:  # pragma: no cover
            reporter = DummyReportGenerator()

        logger.debug('C3 compilation started')
        reporter.heading(2, 'c3 compilation')
        sources = [io.StringIO(i) for i in self.items]
        includes = [get_file(fn) for fn in includes]
        diag = DiagnosticsManager()
        c3b = C3Builder(diag, march.info)

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

        return self._new('ir', ir_modules)
