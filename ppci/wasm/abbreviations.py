"""
This module provides functions to normalize S-expressions that describe
a WASM module:

* All definitions are named. A definition is a toplevel element in a WASM module,
  like a type/func/import/etc.
* Abbreviations are resolved. An abbreviation is an alternative (usually shorter)
  way to write WASM text constructs. Dealing with all these possible variations
  would be very painful; we chose to normalize these at the start.
  (Note that we do make use of a few specific abbreviations, such as compacting
  the notation of a series of params of the same type).

"""

# Notes:
#
# - The number of actual functions is fixed.
# - We may get new toplevel type fields (i.e. function signatures)
# - We may get new toplevel imports and exports.

import struct

from .util import datastring2bytes



def normalize_wasm_s_expression(t, SECTION_IDS):
    """ Normalize a given WASM S-expression (in the form of a tuple structure),
    so that it is in a predictable shape.
    """

    # How many (toplevel) elements we have of each of these, for assigning indices
    # Note that the index that we assign with this does not match the actual
    # index in binary wasm, because imports also contribute (and offet the indices
    # of the actual funcs/memories/globals).
    counts = {'type': 0, 'func': 0, 'table': 0, 'memory': 0, 'global': 0}

    # Basic validation and convert to list so that funcs can work in-place
    assert isinstance(t, tuple)
    t = list(t)

    # Allow having implicit first "module" element
    if t and t[0] == 'module':
        t.pop(0)

    initial_checkup(t, counts, SECTION_IDS)
    resolve_type(t, counts)
    resolve_inline_imports(t, counts)
    resolve_inline_exports(t, counts)
    resolve_table(t, counts)
    resolve_memory(t, counts)

    # Sort the toplevel fields (we may have added fields)
    t.sort(key=lambda x: (isinstance(x, tuple), SECTION_IDS.get(x[0], 99)))

    t.insert(0, 'module')
    return tuple(t)


def initial_checkup(t, counts, SECTION_IDS):

    # - Do basic validation of the tuple structure
    # - Init counts dict
    # - Ensure that all func, table, memory, global expressions have an id

    for i in range(len(t)):
        expr = t[i]
        assert isinstance(expr, tuple)
        defname = expr[0]
        assert isinstance(defname, str) and defname in SECTION_IDS
        if defname in counts:
            id = '$' + str(counts[defname])
            counts[defname] += 1
            # Ensure id
            expr = list(expr)
            if isinstance(expr[1], str) and expr[1] not in ('anyfunc', ):
                assert expr[1].startswith('$'), 'named variables must start with $'
            elif not isinstance(expr[1], int):
                expr.insert(1, id)
            t[i] = tuple(expr)


def resolve_type(t, counts):

    # - Move function signatures inside imports to toplevel
    # - Move function signatures inside funcs to toplevel

    for i in range(len(t)):
        expr, defname = t[i], t[i][0]

        if defname == 'import':
            if expr[3][0] == 'func' and not (isinstance(expr[3][-1], tuple) and
                                                expr[3][-1][0] == 'type'):
                # (import "foo" "bar" (func [$id] ..))
                # this bit looks like a sig     /\ instead of an id
                expr = list(expr)
                sig_expr = ['func'] + [x for x in expr[3] if isinstance(x, tuple)]
                sig_expr = ['type', tuple(sig_expr)]
                assert not isinstance(expr[3][1], int)  # todo: test no-args
                if isinstance(expr[3][1], str):  # had id
                    id = expr[3][1]
                else:
                    id = '$' + str(counts['type'])
                expr[3] = ('func', id, ('type', id))  # we use the same id, but ns is different
                sig_expr.insert(1, id)
                counts['type'] += 1
                # Update
                t.append(tuple(sig_expr))
                t[i] = tuple(expr)

        elif defname == 'func':
            new_expr = []
            type_expr = []
            for subexpr in expr:
                if isinstance(subexpr, tuple):
                    if subexpr[0] in ('param', 'result'):
                        type_expr.append(subexpr)
                        continue
                    elif subexpr[0] == 'type':
                        type_expr = None  # we dont expect param or result
                new_expr.append(subexpr)
            # Update, maybe add new toplevel type expression
            if type_expr is not None:
                id = '$' + str(counts['type'])
                t.append(('type', id, tuple(['func'] + type_expr)))
                new_expr.insert(2, ('type', id))
                counts['type'] += 1
            t[i] = tuple(new_expr)


def resolve_inline_imports(t, counts):

    # Resolve abbreviated imports of memory, function, gobal, table.
    # These expressions are written as func/table/memory/global, but
    # are really an import; the expression is modified.

    for i in range(len(t)):
        expr, defname = t[i], t[i][0]

        if defname in ('func', 'table', 'memory', 'global'):
            expr = list(expr)
            if len(expr) > 2 and \
                    isinstance(expr[2], tuple) and \
                    expr[2][0] == 'import':
                new_expr = list(expr.pop(2))
                new_expr.append(tuple(expr))
                t[i] = tuple(new_expr)


def resolve_inline_exports(t, counts):

    # Resolve abbreviated exports of memory, function, gobal, table.
    # These expressions are written as func/table/memory/global, and
    # are marked as exported; export expressions are added.

    for i in range(len(t)):
        expr, defname = t[i], t[i][0]

        if defname in ('func', 'table', 'memory', 'global'):
            expr = list(expr)
            to_pop = []
            for j in range(2, len(expr)):
                subexpr = expr[j]
                if not isinstance(subexpr, tuple):
                    break
                elif subexpr[0] == 'type':
                    pass  # allow type refs in funcs to come first
                elif subexpr[0] == 'export':
                    new_expr = list(expr[j])
                    new_expr.append(tuple(expr[:2]))  # kind and id
                    t.append(tuple(new_expr))
                    to_pop.append(j)
                else:
                    break
            # If we found any export expressions, simplify this definition
            if to_pop:
                for j in reversed(to_pop):
                    expr.pop(j)
                t[i] = tuple(expr)


def resolve_table(t, counts):

    # - Resolve inline elements

    for i in range(len(t)):
        expr, defname = t[i], t[i][0]

        if defname == 'table':
            expr = list(expr)

            # Inline data
            elem_expr = None
            for j in range(2, len(expr)):
                subexpr = expr[j]
                if isinstance(subexpr, tuple):
                    if subexpr[0] == 'elem':
                        refs = subexpr[1:]
                        elem_expr = ('elem', expr[1], ('i32.const', 0)) + tuple(refs)
                        expr.pop(j)
                        kind = expr.pop(-1)
                        expr.extend([len(refs), len(refs), kind])
                        break
            # Update
            if elem_expr:
                t[i] = tuple(expr)
                t.append(tuple(elem_expr))
                continue


def resolve_memory(t, counts):

    # - Resolve inline data

    for i in range(len(t)):
        expr, defname = t[i], t[i][0]

        if defname == 'memory':
            expr = list(expr)

            # Inline data
            data_expr = None
            for j in range(2, len(expr)):
                subexpr = expr[j]
                if isinstance(subexpr, tuple):
                    if subexpr[0] == 'data':
                        data_str = subexpr[1]
                        data_len = len(datastring2bytes(data_str))
                        npages = int(data_len/65536) + 1
                        data_expr = 'data', expr[1], ('i32.const', 0), data_str
                        expr.pop(j)
                        expr.extend([npages, npages])
                        break
            # Update
            if data_expr:
                t[i] = tuple(expr)
                t.append(tuple(data_expr))
                continue
