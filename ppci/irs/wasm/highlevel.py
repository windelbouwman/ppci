""" High level api functions.

These functions serve as a convenience layer over the low level wasm
components.

"""

from . import components


def make_module(functions):
    """ Construct a wasm module from the given objects. """
    builder = WasmModuleBuilder()

    # Process imported functions
    for func in functions:
        if isinstance(func, ImportedFuncion):
            type_id = builder.get_type_id(func.params, func.returns)
            builder.add_import(
                func.modname, func.fieldname, 'func', type_id,
                export=func.export)

    # Process defined functions
    for func in functions:
        if isinstance(func, Function):
            type_id = builder.get_type_id(func.params, func.returns)
            func_id = builder.declare_function(
                func.idname, type_id, export=func.export)
            builder.define_function(func.locals, func.instructions)

            if func.idname == '$main':
                builder.set_start(func_id)

    return builder.finish()


class WasmModuleBuilder:
    """ Use this class to construct a wasm module in a more convenient way.

    The purpose of this builder is to administer the type indices and keep
    track of the function id's.
    """
    def __init__(self):
        self.types = []
        self.imports = []
        self.exports = []
        self.functions = []
        self.function_defs = []
        self.auto_start = None
        self._type_ids = {}
        self._function_ids = {}

    def get_type_id(self, arg_types, ret_types):
        """ Get wasm type id and create a signature if required! """
        # Get type signature!
        arg_types = tuple(arg_types)
        ret_types = tuple(ret_types)
        key = (arg_types, ret_types)
        if key not in self._type_ids:
            # Store it in type map!
            self._type_ids[key] = len(self.types)
            self.types.append(components.FunctionSig(arg_types, ret_types))
        return self._type_ids[key]

    def add_import(self, modname, name, kind, type_id, export=False):
        """ Add an import """
        if self.functions:
            raise ValueError(
                'Cannot add imports after functions have been added')
        self.imports.append(components.Import(
            modname, name, kind, type_id))
        func_id = len(self._function_ids)
        self._function_ids[name] = func_id
        if export:
            self.add_export(name, kind, func_id)
        return func_id

    def add_export(self, function_name, kind, func_nr):
        self.exports.append(components.Export(
            function_name, kind, func_nr))

    def has_function(self, name):
        """ Check if a function is present with the given name """
        return name in self._function_ids

    def get_function_id(self, name):
        return self._function_ids[name]

    def declare_function(self, name, type_id, export=False):
        """ Declare a function with the given type id """
        func_id = len(self._function_ids)
        self._function_ids[name] = func_id

        # Add function type-id:
        self.functions.append(type_id)

        if export:
            self.add_export(name, 'func', func_id)
        return func_id

    def define_function(self, local_vars, instructions):
        """ Define the implementation of a function """
        self.function_defs.append(components.FunctionDef(
            local_vars,
            instructions))

    def set_start(self, function_id):
        """ Mark function as auto start """
        if self.auto_start is None:
            self.auto_start = components.StartSection(function_id)

    def finish(self):
        """ Put all sections into a module """
        sections = []

        # Insert function sigs and defs
        sections.append(components.TypeSection(self.types))
        sections.append(components.FunctionSection(self.functions))
        sections.append(components.CodeSection(self.function_defs))

        # Insert imports
        if self.imports:
            import_section = components.ImportSection(self.imports)
            sections.append(import_section)

        # Insert auto-generated exports
        if self.exports:
            export_section = components.ExportSection(self.exports)
            sections.append(export_section)

        # Insert start section
        if self.auto_start is not None:
            sections.append(self.auto_start)
        return components.Module(sections)


class Function:
    """ High-level description of a function.
    """

    __slots__ = [
        'idname', 'params', 'returns', 'locals', 'instructions', 'export']

    def __init__(
            self, idname, params=None, returns=None, locals=None,
            instructions=None, export=False):
        assert isinstance(idname, str)
        assert isinstance(params, (tuple, list))
        assert isinstance(returns, (tuple, list))
        assert isinstance(locals, (tuple, list))
        assert isinstance(instructions, (tuple, list))
        self.idname = idname
        self.params = params
        self.returns = returns
        self.locals = locals
        self.instructions = instructions
        self.export = bool(export)


class ImportedFuncion:
    """ High-level description of an imported function.
    """

    __slots__ = [
        'idname', 'params', 'returns', 'modname', 'fieldname', 'export']

    def __init__(
            self, idname, params, returns, modname, fieldname, export=False):
        assert isinstance(idname, str)
        assert isinstance(params, (tuple, list))
        assert isinstance(returns, (tuple, list))
        assert isinstance(modname, str)
        assert isinstance(fieldname, str)
        self.idname = idname
        self.params = params
        self.returns = returns
        self.modname = modname
        self.fieldname = fieldname
        self.export = bool(export)
