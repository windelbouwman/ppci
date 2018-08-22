
"""
Defines task classes that can compile, link etc..
Task can depend upon one another.
These task are wrappers around the functions provided in the buildfunctions
module
"""

from .tasks import Task, TaskError, register_task
from ..utils.reporting import HtmlReportGenerator, DummyReportGenerator
from .. import api
from ..lang.tools.common import ParserException
from ..common import CompilerError


@register_task
class EmptyTask(Task):
    """ Basic task that does nothing """
    def run(self):
        pass


@register_task
class EchoTask(Task):
    """ Simple task that echoes a message """
    def run(self):
        message = self.get_argument('message')
        print(message)


@register_task
class PropertyTask(Task):
    """ Sets a property to a value """
    def run(self):
        name = self.arguments['name']
        value = self.arguments['value']
        self.target.project.set_property(name, value)


@register_task
class BuildTask(Task):
    """ Builds another build description file (build.xml) """
    def run(self):
        project = self.relpath(self.get_argument('file'))
        api.construct(project)


class OutputtingTask(Task):
    """ Base task for tasks that create an object file """

    def store_object(self, obj):
        """ Store the object in the specified file """
        output_filename = self.relpath(self.get_argument('output'))
        self.ensure_path(output_filename)
        with open(output_filename, 'wt', encoding='utf8') as output_file:
            obj.save(output_file)


@register_task
class AssembleTask(OutputtingTask):
    """ Task that can runs the assembler over the source and enters the
        output into an object file """

    def run(self):
        arch = self.get_argument('arch')
        source = self.relpath(self.get_argument('source'))
        if 'debug' in self.arguments:
            debug = bool(self.get_argument('debug'))
        else:
            debug = False

        try:
            obj = api.asm(source, arch, debug=debug)
        except ParserException as err:
            raise TaskError('Error during assembly:' + str(err))
        except CompilerError as err:
            raise TaskError('Error during assembly:' + str(err))
        except OSError as err:
            raise TaskError('Error:' + str(err))

        self.store_object(obj)
        self.logger.debug('Assembling finished')


@register_task
class C3CompileTask(OutputtingTask):
    """ Task that compiles C3 source for some target into an object file """
    def run(self):
        arch = self.get_argument('arch')
        sources = self.open_file_set(self.arguments['sources'])
        if 'includes' in self.arguments:
            includes = self.open_file_set(self.arguments['includes'])
        else:
            includes = []

        if 'report' in self.arguments:
            report_file = self.relpath(self.arguments['report'])
            reporter = HtmlReportGenerator(open(report_file, 'wt', encoding='utf8'))
        else:
            reporter = DummyReportGenerator()

        debug = bool(self.get_argument('debug', default=False))
        opt = int(self.get_argument('optimize', default='0'))

        with reporter:
            obj = api.c3c(
                sources, includes, arch, opt_level=opt,
                reporter=reporter, debug=debug)

        self.store_object(obj)


@register_task
class CCompileTask(OutputtingTask):
    """ Task that compiles C code for some target into an object file """
    def run(self):
        arch = self.get_argument('arch')
        sources = self.open_file_set(self.arguments['sources'])
        if 'includes' in self.arguments:
            includes = self.open_file_set(self.arguments['includes'])
        else:
            includes = []

        if 'report' in self.arguments:
            report_file = self.relpath(self.arguments['report'])
            reporter = HtmlReportGenerator(open(report_file, 'wt', encoding='utf8'))
        else:
            reporter = DummyReportGenerator()

        debug = bool(self.get_argument('debug', default=False))
        opt = int(self.get_argument('optimize', default='0'))

        coptions = api.COptions()
        coptions.add_include_paths(includes)

        with reporter:
            objs = []
            for source in sources:
                with open(source, 'r') as f:
                    obj = api.cc(
                        f, arch, coptions=coptions, opt_level=opt,
                        reporter=reporter, debug=debug)
                objs.append(obj)
            obj = api.link(
                objs, partial_link=True, reporter=reporter, debug=debug)

        self.store_object(obj)


@register_task
class WasmCompileTask(OutputtingTask):
    """ Task that compiles a wasm module into an object file """
    def run(self):
        arch = self.get_argument('arch')
        source = self.open_file_set(self.arguments['source'])
        opt = int(self.get_argument('optimize', default='0'))

        if 'report' in self.arguments:
            report_file = self.relpath(self.arguments['report'])
            reporter = HtmlReportGenerator(open(report_file, 'wt', encoding='utf8'))
        else:
            reporter = DummyReportGenerator()

        self.logger.debug('loading %s', source[0])
        with reporter:
            with open(source[0], 'rb') as f:
                obj = api.wasmcompile(
                    f, arch, opt_level=opt, reporter=reporter)
        self.store_object(obj)


@register_task
class LinkTask(OutputtingTask):
    """ Link together a collection of object files """
    def run(self):
        if 'layout' in self.arguments:
            layout = self.relpath(self.get_argument('layout'))
        else:
            layout = None
        objects = self.open_file_set(self.get_argument('objects'))
        debug = bool(self.get_argument('debug', default=False))
        partial = bool(self.get_argument('partial', default=False))

        try:
            obj = api.link(
                objects, layout=layout, use_runtime=True,
                partial_link=partial, debug=debug)
        except CompilerError as err:
            raise TaskError(err.msg)

        self.store_object(obj)


@register_task
class ObjCopyTask(Task):
    """ Binary move parts of object code. """
    def run(self):
        image_name = self.get_argument('imagename')
        output_filename = self.relpath(self.get_argument('output'))
        object_filename = self.relpath(self.get_argument('objectfile'))
        fmt = self.get_argument('format')

        api.objcopy(object_filename, image_name, fmt, output_filename)
