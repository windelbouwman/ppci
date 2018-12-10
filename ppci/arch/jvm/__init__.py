
""" Java virtual machine (JVM).

This module supports loading and saving of java bytecode.

See also:

https://en.wikipedia.org/wiki/Java_bytecode_instruction_listings
"""

from .io import read_jar, read_class_file
from .class2ir import class_to_ir
from .dynload import load_class


def print_class_file(class_file):
    """ Dump a class file. """
    ClassFilePrinter(class_file)


class ClassFilePrinter:
    def __init__(self, class_file):
        self.class_file = class_file
        class_info = class_file.get_constant(class_file.this_class)
        class_name = class_file.get_name(class_info.value)
        print('class {}'.format(class_name))
        print('  minor version:', class_file.minor_version)
        print('  major version:', class_file.major_version)
        print('  flags:', class_file.access_flags)

        print('Constant pool:')
        for i, value in enumerate(class_file.constant_pool):
            if not value:
                continue
            print('  #{} = {}  {}'.format(i, value.tag, value.value))

        print('{')

        for field in class_file.fields:
            print(field)
            self.print_attributes('  ', field.attributes)

        for method in class_file.methods:
            name = class_file.get_name(method.name_index)
            descriptor = class_file.get_name(method.descriptor_index)
            print('  {};'.format(name))
            print('    descriptor:', descriptor)
            print('    flags:', method.access_flags)
            self.print_attributes('    ', method.attributes)

        print('}')
        self.print_attributes('', class_file.attributes)

    def print_attributes(self, indent, attributes):
        for attribute in attributes:
            name = self.class_file.get_name(attribute.name_index)
            value = attribute
            print('{}{}: {}'.format(indent, name, value))


__all__ = ['class_to_ir', 'read_class_file', 'read_jar']
