""" Functions to print class contents in a verbose way.
"""


def print_class_file(class_file):
    """ Dump a class file. """
    ClassFilePrinter(class_file)


class ClassFilePrinter:
    def __init__(self, class_file):
        self.class_file = class_file
        class_info = class_file.get_constant(class_file.this_class)
        class_name = class_file.get_name(class_info.value)
        print("class {}".format(class_name))
        print("  minor version:", class_file.minor_version)
        print("  major version:", class_file.major_version)
        print("  flags:", class_file.access_flags)

        print("Constant pool:")
        for i, value in enumerate(class_file.constant_pool):
            if not value:
                continue
            print("  #{} = {}  {}".format(i, value.tag.name, value.value))

        print("{")

        for field in class_file.fields:
            print(field)
            self.print_attributes("  ", field.attributes)

        for method in class_file.methods:
            print("  {};".format(method.name))
            print("    descriptor:", method.descriptor)
            print("    flags:", method.access_flags)
            self.print_attributes("    ", method.attributes)

        print("}")
        self.print_attributes("", class_file.attributes)

    def print_attributes(self, indent, attributes):
        for attribute in attributes:
            name = attribute.name
            value = attribute
            print("{}{}: {}".format(indent, name, value))
