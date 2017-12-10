""" Web assembly text format utilities """

from .components import ExportSection, TypeSection, FunctionSection
from .components import CodeSection


def wasm_to_wat(module, f):
    """ Translate a wasm module into textual format. """
    print('(module', file=f)
    exports = []
    functions = []
    function_defs = []
    for section in module.sections:
        if section.id == TypeSection.id:
            for idx, t in enumerate(section.functionsigs):
                params = 'param ' + ' '.join(t.params)
                returns = 'result ' + ' '.join(t.returns)
                print(
                    '  (type {} (func ({}) ({}) ))'.format(
                        idx, params, returns),
                    file=f)
        elif section.id == FunctionSection.id:
            functions.extend(section.indices)
        elif section.id == ExportSection.id:
            exports.extend(section.exports)
        elif section.id == CodeSection.id:
            function_defs.extend(section.functiondefs)
        else:
            raise NotImplementedError('Section {}'.format(section.id))

    # Printout functions:
    for function_typ, function_def in zip(functions, function_defs):
        print('  (func (type {})'.format(function_typ), file=f)
        for i in function_def.instructions:
            args = ' '.join(map(str, i.args))
            print('    {} {}'.format(i.type, args), file=f)
        print('  )', file=f)

    # Printout exports:
    for export in exports:
        print(
            '  (export "{}" ({} {}))'.format(
                export.name, export.kind, export.index),
            file=f)
    print(')', file=f)
