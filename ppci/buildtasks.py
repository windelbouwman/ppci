
"""
Defines task classes that can compile, link etc..
Task can depend upon one another.
These task are wrappers around the functions provided in the buildfunctions
module
"""

from .tasks import Task, TaskError, register_task
from .buildfunctions import c3compile, link, assemble, construct
from .buildfunctions import objcopy
from .pyyacc import ParserException
from . import CompilerError


@register_task("empty")
class EmptyTask(Task):
    """ Basic task that does nothing """
    def run(self):
        pass


@register_task("echo")
class EchoTask(Task):
    """ Simple task that echoes a message """
    def run(self):
        message = self.arguments['message']
        print(message)


@register_task("property")
class Property(Task):
    """ Sets a property to a value """
    def run(self):
        name = self.arguments['name']
        value = self.arguments['value']
        self.target.project.set_property(name, value)


@register_task("build")
class ConstructTask(Task):
    """ Builds another build description file (build.xml) """
    def run(self):
        project = self.get_argument('file')
        construct(project)


@register_task("assemble")
class AssembleTask(Task):
    """ Task that can runs the assembler over the source and enters the
        output into an object file """

    def run(self):
        target = self.get_argument('target')
        source = self.relpath(self.get_argument('source'))
        output_filename = self.relpath(self.get_argument('output'))

        try:
            output = assemble(source, target)
        except ParserException as err:
            raise TaskError('Error during assembly:' + str(err))
        except CompilerError as err:
            raise TaskError('Error during assembly:' + str(err))
        except OSError as err:
            raise TaskError('Error:' + str(err))
        with open(output_filename, 'w') as output_file:
            output.save(output_file)
        self.logger.debug('Assembling finished')


@register_task("compile")
class C3cTask(Task):
    """ Task that compiles C3 source for some target into an object file """
    def run(self):
        target = self.get_argument('target')
        sources = self.open_file_set(self.arguments['sources'])
        output_filename = self.relpath(self.get_argument('output'))
        if 'includes' in self.arguments:
            includes = self.open_file_set(self.arguments['includes'])
        else:
            includes = []
        if 'listing' in self.arguments:
            lst_file = self.relpath(self.arguments['listing'])
            lst_file = open(lst_file, 'w')
        else:
            lst_file = None

        output = c3compile(sources, includes, target, lst_file=lst_file)
        if lst_file is not None:
            lst_file.close()

        # Store output:
        with open(output_filename, 'w') as output_file:
            output.save(output_file)


@register_task("link")
class LinkTask(Task):
    """ Link together a collection of object files """
    def run(self):
        layout = self.relpath(self.get_argument('layout'))
        target = self.get_argument('target')
        objects = self.open_file_set(self.get_argument('objects'))
        output_filename = self.relpath(self.get_argument('output'))

        try:
            output_obj = link(objects, layout, target)
        except CompilerError as err:
            raise TaskError(err.msg)

        # Store output:
        with open(output_filename, 'w') as output_file:
            output_obj.save(output_file)


@register_task("objcopy")
class ObjCopyTask(Task):
    """ Binary move parts of object code. """
    def run(self):
        image_name = self.get_argument('imagename')
        output_filename = self.relpath(self.get_argument('output'))
        object_filename = self.relpath(self.get_argument('objectfile'))
        fmt = self.get_argument('format')

        objcopy(object_filename, image_name, fmt, output_filename)
