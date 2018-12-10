""" Module to load class/jar files. """

import logging
import zipfile
import io
from ...format.io import BaseIoReader

logger = logging.getLogger('jvm.io')


def read_jar(filename):
    """ Take a stroll through a java jar file. """
    logger.info('Reading jar: %s', filename)
    with zipfile.ZipFile(filename) as f:
        with f.open('META-INF/MANIFEST.MF') as manifest_file:
            read_manifest(io.TextIOWrapper(manifest_file))

        # Load some random classes:
        class_files = []
        for name in f.namelist():
            print(name)
            if name.endswith('.class'):
                with f.open(name, 'r') as class_file:
                    class_file = read_class_file(class_file)
                class_files.append(class_file)
        logger.debug('Loaded %s class files', len(class_files))


def read_manifest(f):
    """ Read a jarfile manifest. """
    logger.debug('Reading manifest')
    properties = {}
    for line in f:
        line = line.strip()
        if line:
            key, value = map(str.strip, line.split(':', 1))
            if key in properties:
                logger.warning('Duplicate key in manifest file: %s', key)
            properties[key] = value.strip()
    logger.debug('Read manifest: %s', properties)
    return properties


class JavaFileReader(BaseIoReader):
    """ Java class file reader.
    """
    def __init__(self, f, verbose=False):
        super().__init__(f)
        self.verbose = verbose

    def read_class_file(self):
        """ Read a class file. """
        magic = self.read_u32()
        logger.debug('Read magic header value 0x%X', magic)
        assert magic == 0xCAFEBABE
        minor_version = self.read_u16()
        major_version = self.read_u16()
        logger.debug('Version %s.%s', major_version, minor_version)
        constant_pool = self.read_constant_pool()
        access_flags = self.read_u16()
        this_class = self.read_u16()
        super_class = self.read_u16()

        interfaces_count = self.read_u16()
        interfaces = []
        for _ in range(interfaces_count):
            idx = self.read_u16()
            interfaces.append(idx)
        logger.debug('Loaded interfaces: %s', interfaces)

        fields_count = self.read_u16()
        fields = []
        for _ in range(fields_count):
            field = self.read_field_info()
            fields.append(field)
        logger.debug('Loaded %s fields', len(fields))

        methods_count = self.read_u16()
        methods = []
        for _ in range(methods_count):
            method = self.read_method_info()
            methods.append(method)
        logger.debug('Loaded %s methods', len(methods))

        attributes = self.read_attributes()
        class_file = ClassFile(
            major_version=major_version, minor_version=minor_version,
            constant_pool=constant_pool,
            access_flags=access_flags,
            this_class=this_class, super_class=super_class,
            interfaces=interfaces,
            fields=fields,
            methods=methods,
            attributes=attributes
        )
        return class_file

    def read_constant_pool(self):
        """ Read the constant pool. """
        constant_pool_count = self.read_u16()
        constant_pool = [None]  # Start with a dummy at position 0.
        if constant_pool_count > 0:
            skip_next = False
            for idx in range(constant_pool_count - 1):
                if skip_next:
                    const_info = None
                    skip_next = False
                else:
                    const_info, skip_next = self.read_cp_info()
                    if self.verbose:
                        logger.debug('constant #%s: %s', idx+1, const_info)
                constant_pool.append(const_info)
        logger.debug('Read constant pool with %s items', len(constant_pool))
        return constant_pool

    def read_cp_info(self):
        tag = self.read_u8()
        skip_next = False
        if tag == 7:
            name_index = self.read_u16()
            info = (7, name_index)
        elif tag == 9 or tag == 10 or tag == 11:
            class_index = self.read_u16()
            name_and_type_index = self.read_u16()
            info = (tag, class_index, name_and_type_index)
        elif tag == 1:  # Utf8 modified text.
            length = self.read_u16()
            data = self.read_data(length)
            text = decode_modified_utf8(data)
            info = (1, text)
        elif tag == 5:
            value = self.read_u64()
            info = (5, value)
            skip_next = True
        elif tag == 6:
            value = self.read_f64()
            info = (6, value)
            skip_next = True
        elif tag == 3:
            value = self.read_u32()
            info = (3, value)
        elif tag == 8:
            string_index = self.read_u16()
            info = (8, string_index)
        elif tag == 12:
            name_index = self.read_u16()
            descriptor_index = self.read_u16()
            info = (tag, name_index, descriptor_index)
        elif tag == 18:  # Invoke dynamic
            bootstrap_method_attr_index = self.read_u16()
            name_and_type_index = self.read_u16()
            info = (tag, bootstrap_method_attr_index, name_and_type_index)
        elif tag == 15:  # Method handle
            reference_kind = self.read_u8()
            reference_index = self.read_u16()
            info = (tag, reference_kind, reference_index)
        elif tag == 16:  # Method type
            descriptor_index = self.read_u16()
            info = (tag, descriptor_index)
        elif tag == 4:  # Float
            value = self.read_f32()
            info = (tag, value)
        else:
            raise NotImplementedError(str(tag))
        # logger.debug('Read constant pool info %s', info)
        return info, skip_next

    def read_field_info(self):
        access_flags = self.read_u16()
        name_index = self.read_u16()
        descriptor_index = self.read_u16()
        attributes = self.read_attributes()
        return (access_flags, name_index, descriptor_index, attributes)

    def read_method_info(self):
        """ Read method info structure """
        access_flags = self.read_u16()
        name_index = self.read_u16()
        descriptor_index = self.read_u16()
        attributes = self.read_attributes()
        return Method(access_flags, name_index, descriptor_index, attributes)

    def read_attributes(self):
        attributes_count = self.read_u16()
        attributes = []
        for _ in range(attributes_count):
            attribute = self.read_attribute_info()
            attributes.append(attribute)
        return attributes

    def read_attribute_info(self):
        attribute_name_index = self.read_u16()
        attribute_length = self.read_u32()
        info = self.read_data(attribute_length)
        return Attribute(attribute_name_index, info)

    def read_f32(self):
        return self.read_fmt('f')

    def read_f64(self):
        return self.read_fmt('d')

    def read_u64(self):
        return self.read_fmt('>Q')

    def read_u32(self):
        return self.read_fmt('>I')

    def read_u16(self):
        return self.read_fmt('>H')

    def read_u8(self):
        data = self.read_data(1)
        return data[0]


def decode_modified_utf8(data):
    # TODO: decode custom utf-8..
    return data.decode('utf8')


def read_class_file(f, verbose=False):
    """ Read a class file.
    """
    logger.debug('Reading classfile %s', f)
    reader = JavaFileReader(f, verbose=verbose)
    return reader.read_class_file()


class Code:
    def __init__(self, max_stack, max_locals, code, attributes):
        self.max_stack = max_stack
        self.max_locals = max_locals
        self.code = code
        self.attributes = attributes


def load_code(data):
    reader = JavaFileReader(io.BytesIO(data))
    max_stack = reader.read_u16()
    max_locals = reader.read_u16()
    code_length = reader.read_u32()
    code = reader.read_data(code_length)
    attributes = reader.read_attributes()
    return Code(max_stack, max_locals, code, attributes)


class ClassFile:
    def __init__(
            self, major_version=None, minor_version=None,
            constant_pool=None,
            access_flags=None, this_class=None, super_class=None,
            interfaces=None, fields=None, methods=None,
            attributes=None):
        self.major_version = major_version
        self.minor_version = minor_version
        self.constant_pool = constant_pool
        self.access_flags = access_flags
        self.this_class = this_class
        self.super_class = super_class
        self.interfaces = interfaces
        self.fields = fields
        self.methods = methods
        self.attributes = attributes

    def get_constant(self, index):
        return self.constant_pool[index]

    def get_name(self, index):
        """ Get a name given by an index. """
        constant = self.get_constant(index)
        assert constant[0] == 1
        return constant[1]


class Method:
    def __init__(self, access_flags, name_index, descriptor_index, attributes):
        self.access_flags = access_flags
        self.name_index = name_index
        self.descriptor_index = descriptor_index
        self.attributes = attributes


class Attribute:
    def __init__(self, name_index, data):
        self.name_index = name_index
        self.data = data

    def __repr__(self):
        return 'Attribute(name_index={}, data={})'.format(
            self.name_index, self.data)


class Manifest:
    pass
