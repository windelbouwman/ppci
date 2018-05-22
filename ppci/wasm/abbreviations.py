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
from .opcodes import OPERANDS, OPCODES


def normalize_wasm_s_expression(t, SECTION_IDS):
    """ Normalize a given WASM S-expression (in the form of a tuple structure),
    so that it is in a predictable shape.
    """
    resolver = AbbreviationResolver(t, SECTION_IDS)
    return resolver.resolve()


class AbbreviationResolver:
    
    def __init__(self, t, section_ids):
        
        # Check t
        assert isinstance(t, tuple)
        t = list(t)
        if t and t[0] == 'module':  # Allow having implicit first "module" element
            t.pop(0)
        
        self._t = t
        self._t_extra = []
        self._section_ids = section_ids
        
        # How many (toplevel) elements we have of each of these, for assigning indices
        # Note that the index that we assign with this does not match the actual
        # index in binary wasm, because imports also contribute (and offet the indices
        # of the actual funcs/memories/globals).
        self._counts =  {'type': 0, 'func': 0, 'table': 0, 'memory': 0, 'global': 0}
        
        self.initial_checkup()
    
    def add_root_expression(self, expr):
        assert isinstance(expr, tuple)
        defname = expr[0]
        if defname in self._counts:
            self._counts[defname] += 1
        self._t_extra.append(expr)
    
    def get_implicit_id(self, defname):
        return '$' + str(self._counts[defname])
    
    def initial_checkup(self):
        
        # - Do basic validation of the tuple structure
        # - Init counts dict
        # - Ensure that all func, table, memory, global expressions have an id
        
        t = self._t
        
        string_but_not_id = 'anyfunc', 'i32', 'i64', 'f32', 'f64'
        
        for i in range(len(t)):
            expr = t[i]
            assert isinstance(expr, tuple)
            defname = expr[0]
            assert isinstance(defname, str) and defname in self._section_ids
            if defname in self._counts:
                id = self.get_implicit_id(defname)
                self._counts[defname] += 1
                # Ensure id
                expr = list(expr)
                if len(expr) == 1:
                    expr.append(id)
                elif isinstance(expr[1], str) and expr[1] not in string_but_not_id:
                    assert expr[1].startswith('$'), 'named variables must start with $'
                elif not isinstance(expr[1], int):
                    expr.insert(1, id)
                t[i] = tuple(expr)
    
    def resolve(self):
        
        for resolver in (self.resolve_type,
                         self.resolve_inline_imports,
                         self.resolve_inline_exports,
                         self.resolve_table,
                         self.resolve_memory,
                         self.resolve_data_elem_offset,
                         self.resolve_instructions,
                         ):
            
            for i in range(len(self._t)):
                expr = self._t[i]
                new_expr = resolver(expr)
                if new_expr is not None and new_expr is not expr:
                    assert isinstance(new_expr, tuple)
                    self._t[i] = new_expr
        
        t = self._t + self._t_extra
        t.sort(key=lambda x: (isinstance(x, tuple), self._section_ids.get(x[0], 99)))
        t.insert(0, 'module')
        return tuple(t)
    
    ##
    
    def resolve_type(self, expr):
    
        # - Move function signatures inside imports to toplevel
        # - Move function signatures inside funcs to toplevel
        
        if expr[0] == 'import':
            if expr[3][0] == 'func' and not (isinstance(expr[3][-1], tuple) and
                                                expr[3][-1][0] == 'type'):
                # (import "foo" "bar" (func [$id] ..))
                # this bit looks like a sig     /\ instead of an id
                expr = list(expr)
                sig_expr = ['func'] + [x for x in expr[3] if isinstance(x, tuple)]
                sig_expr = ['type', tuple(sig_expr)]
                assert not (len(expr[3]) > 1 and isinstance(expr[3][1], int))  # todo: test no-args
                if len(expr[3]) > 1 and isinstance(expr[3][1], str):  # had id
                    id = expr[3][1]
                else:
                    id = self.get_implicit_id('type')
                expr[3] = ('func', id, ('type', id))  # we use the same id, but ns is different
                sig_expr.insert(1, id)
                # Update
                self.add_root_expression(tuple(sig_expr))
                return tuple(expr)

        elif expr[0] == 'func':
            new_expr = list(expr[:2])
            type_expr = []
            for i in range(2, len(expr)):
                subexpr = expr[i]
                if isinstance(subexpr, tuple):
                    if subexpr[0] in ('param', 'result'):
                        if type_expr is not None:
                            # Apparently, one can do (spec\test\core\func.wast):
                            #   (func (type $sig-3) (param i32))
                            type_expr.append(subexpr)
                        continue
                    elif subexpr[0] in ('local', 'type', 'import', 'export'):
                        if subexpr[0] == 'type':
                            type_expr = None  # we dont expect param or result
                        new_expr.append(subexpr)
                        continue
                new_expr.extend(expr[i:])
                break
            # Update, maybe add new toplevel type expression
            if type_expr is not None:
                id = self.get_implicit_id('type')
                self.add_root_expression(('type', id, tuple(['func'] + type_expr)))
                new_expr.insert(2, ('type', id))
            return tuple(new_expr)

    def resolve_inline_imports(self, expr):
        
        # Resolve abbreviated imports of memory, function, gobal, table.
        # These expressions are written as func/table/memory/global, but
        # are really an import; the expression is modified.

        if expr[0] in ('func', 'table', 'memory', 'global'):
            expr = list(expr)
            for j in range(2, len(expr)):
                subexpr = expr[j]
                if not isinstance(subexpr, tuple):
                    break
                elif subexpr[0] in ('type', 'export'):
                    pass  # allow type and export in funcs to come first
                elif subexpr[0] == 'import':
                    new_expr = list(expr.pop(j))
                    new_expr.append(tuple(expr))
                    return tuple(new_expr)
                else:
                    break  # We wont iterate over all instructions of a func
    
    def resolve_inline_exports(self, expr):
        
        # Resolve abbreviated exports of memory, function, gobal, table.
        # These expressions are written as func/table/memory/global, and
        # are marked as exported; export expressions are added.
        
        if expr[0] in ('func', 'table', 'memory', 'global'):
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
                    self.add_root_expression(tuple(new_expr))
                    to_pop.append(j)
                else:
                    break  # We wont iterate over all instructions of a func
            # If we found any export expressions, simplify this definition
            if to_pop:
                for j in reversed(to_pop):
                    expr.pop(j)
                return tuple(expr)
    
        # Deal with  ('import', 'spectest', 'print_i32',
        #               ('func', '$2', ('type', '$14'), ('export', 'p1')))
        
        elif expr[0] == 'import' and len(expr) >= 4:
            import_expr = list(expr)
            expr = list(import_expr[-1])
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
                    self.add_root_expression(tuple(new_expr))
                    to_pop.append(j)
                else:
                    break  # We wont iterate over all instructions of a func
            # If we found any export expressions, simplify this definition
            if to_pop:
                for j in reversed(to_pop):
                    expr.pop(j)
                import_expr[-1] = tuple(expr)
                return tuple(import_expr)

    def resolve_table(self, expr):
        
        # - Resolve inline elements

        if expr[0] == 'table':
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
                self.add_root_expression(tuple(elem_expr))
                return tuple(expr)

    def resolve_memory(self, expr):
    
        # - Resolve inline data

        if expr[0] == 'memory':
            expr = list(expr)

            # Inline data
            data_expr = None
            for j in range(2, len(expr)):
                subexpr = expr[j]
                if isinstance(subexpr, tuple):
                    if len(subexpr) > 1 and  subexpr[0] == 'data':
                        data_str = subexpr[1]
                        data_len = len(datastring2bytes(data_str))
                        npages = int(data_len/65536) + 1
                        data_expr = 'data', expr[1], ('i32.const', 0), data_str
                        expr.pop(j)
                        expr.extend([npages, npages])
                        break
            # Update
            if data_expr:
                self.add_root_expression(tuple(data_expr))
                return tuple(expr)
    
    def resolve_data_elem_offset(self, expr):
        
        # - Resolve data with explicit offset tuple
        
        if expr[0] in ('data', 'elem'):
            for i in (1, 2):
                if i < len(expr) and isinstance(expr[i], tuple) and expr[i][0] == 'offset':
                    expr = list(expr)
                    assert len(expr[i]) == 2
                    expr[i] = expr[i][1]
                    return tuple(expr)

    def resolve_instructions(self, expr):
        
        # - Flatten instructions
        # - Move function signatures inside call_indirect to toplevel
        
        if expr[0] == 'func':
            # Get instructions
            new_expr = list(expr[:2])
            instructions = []
            for i in range(2, len(expr)):
                subexpr = expr[i]
                if isinstance(subexpr, tuple):
                    if subexpr[0] in ('param', 'local', 'result', 'type',
                                      'import', 'export'):
                        new_expr.append(subexpr)
                        continue
                instructions = expr[i:]
                break
            
            # Flatten
            instructions = flatten_instructions(instructions)
            
            # Resolve stuff per-instruction
            for i, instr in enumerate(instructions):
                if instr[0] == 'call_indirect':
                    # call_indirect can have embedded type def
                    in_type_expr = []
                    for j in range(1, len(instr)):
                        subexpr = instr[j] 
                        if (isinstance(subexpr, tuple) and
                                subexpr[0] in ('param', 'result')):
                            in_type_expr.append(j)
                    if in_type_expr:
                        id = self.get_implicit_id('type')
                        type_expr = tuple(instr[j] for j in in_type_expr)
                        type_expr = ('type', id, (('func',) + type_expr))
                        self.add_root_expression(type_expr)
                        instr =list(instr)
                        for j in reversed(in_type_expr):
                            instr.pop(j)
                        instructions[i] = tuple(instr)
            
            return tuple(new_expr + instructions)


def flatten_instructions(t):
    """ Normalize a list of instructions, so that each instruction is
    a tuple. Instructions can be tuples or strings, and can be nested.
    Or they can just be a series of instructions and we need to pack
    them into tuples.
    Resulting block instructions will look like (opcode, id, result).
    """ 
    instructions = []
    while t:
        opcode_or_tuple = t[0]
        if isinstance(opcode_or_tuple, tuple):
            # Recurse
            instructions += flatten_instruction(opcode_or_tuple)
            t = t[1:]
        elif opcode_or_tuple == 'call_indirect':
            i = 1
            type_tuples = ('type', 'param', 'result')
            while i < len(t):
                if not (isinstance(t[i], tuple) and t[i][0] in type_tuples):
                    break
                i += 1
            sub, t = t[:i], t[i:]
            instructions += flatten_instruction(sub)
        elif opcode_or_tuple in ('block', 'loop', 'if'):
            i = 1
            if isinstance(t[i], str) and t[i].startswith('$'):
                i += 1
            if isinstance(t[i], tuple) and t[i][0] == 'result':
                i += 1
            sub, t = t[:i], t[i:]
            instructions += flatten_instruction(sub)
        elif opcode_or_tuple in ('else', 'end'):  # these can have a label too
            if isinstance(t[1], str) and t[1].startswith('$'):
                sub, t = t[:2], t[2:]
            else:
                sub, t = t[:1], t[1:]
            instructions.append(sub)
        else:
            # Get info on this opcode
            opcode = opcode_or_tuple
            operands = OPERANDS[opcode]
            split = len(operands) + 1
            args = t[1:split]
            t = t[split:]
            instructions.append((opcode, ) + tuple(args))
    return instructions


def flatten_instruction(t):
    """ Collect an instruction provided as a tuple. May return multiple
    instructions if instructions are nested.
    """
    instructions = []
    opcode = t[0]
    operands = OPERANDS[opcode]
    args = t[1:]
    # Is this a block?
    if opcode in ('block', 'loop', 'if'):
        id = None
        result = 'emptyblock'
        # Get control id and return type (if present)
        if args and args[-1] == 'emptyblock':
            args = args[:-1]
        if args:
            if args[0] is None:
                id, args = args[0], args[1:]
            elif isinstance(args[0], str) and args[0].startswith('$'):
                id, args = args[0], args[1:]
        if args and isinstance(args[0], tuple) and args[0][0] == 'result':
            result, args = args[0][1], args[1:]
        # Constuct Instruction
        if opcode == 'if' and len(args) > 0:
            # If consumes one value from the stack, so if this if-instruction
            # has nested instructions, the first is the test.
            if args and args[0][0] != 'then':
                instructions += flatten_instruction(args[0])
                args = args[1:]
            if args and args[0][0] == 'then':
                args = args[0][1:] + args[1:]
        instructions.append((opcode, id, result))  # block instruction
        instructions += flatten_instructions(args)
        if args:
            instructions.append(('end', ))  # implicit end
    elif opcode in ('else', ):
        instructions.append((opcode, ))
        instructions += flatten_instructions(args)
    else:
        # br_table special case for number of operands:
        if opcode in ('br_table', 'memory.grow', 'memory.size'):
            num_operands = 0
            for x in args:
                if isinstance(x, tuple):
                    break
                num_operands += 1
        elif opcode == 'call_indirect':
            num_operands = 0
            type_tuples = ('type', 'param', 'result')
            for x in args:
                if isinstance(x, tuple) and x[0] not in type_tuples:
                    break
                num_operands += 1
        else:
            num_operands = len(operands)
        # Normal instruction
        # Deal with nested instructions; these come first
        args, nested_instructions = args[:num_operands], args[num_operands:]
        assert all(isinstance(i, tuple) for i in nested_instructions)
        # todo: if we knew how much each instruction popped/pushed,
        # we can do more validation
        # assert len(args) == len(operands), ('Number of arguments does not '
        #                                     'match operands for %s' % opcode)
        args_after_all = []
        for i in nested_instructions:  # unnest, but order is ok
            if args_after_all is None:
                pass
            elif isinstance(i, tuple) and i[0] not in OPCODES:
                args_after_all.append(i)
                continue
            else:
                args = args + tuple(args_after_all)
                args_after_all = None
            instructions += flatten_instruction(i)
        instructions.append((opcode, ) + args)
    return instructions
