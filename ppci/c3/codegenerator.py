import logging
import struct
from .. import ir
from .. import irutils
from . import astnodes as ast


class SemanticError(Exception):
    """ Error thrown when a semantic issue is observed """
    def __init__(self, msg, loc):
        super().__init__()
        self.msg = msg
        self.loc = loc


def pack_string(txt):
    """ Pack a string using 4 bytes length followed by text data """
    length = struct.pack('<I', len(txt))
    data = txt.encode('ascii')
    return length + data


class CodeGenerator:
    """
      Generates intermediate (IR) code from a package. The entry function is
      'genModule'. The main task of this part is to rewrite complex control
      structures, such as while and for loops into simple conditional
      jump statements. Also complex conditional statements are simplified.
      Such as 'and' and 'or' statements are rewritten in conditional jumps.
      And structured datatypes are rewritten.

      Type checking is done in one run with code generation.
    """
    def __init__(self, diag):
        self.logger = logging.getLogger('c3cgen')
        self.builder = irutils.Builder()
        self.diag = diag

    def emit(self, instruction):
        """
            Emits the given instruction to the builder. Can be muted for constants
        """
        self.builder.emit(instruction)
        return instruction

    def gencode(self, pkg):
        """ Generate code for a single module """
        self.builder.prepare()
        assert type(pkg) is ast.Package
        self.pkg = pkg
        self.intType = pkg.scope['int']
        self.boolType = pkg.scope['bool']
        self.pointerSize = 4
        self.logger.debug('Generating ir-code for {}'.format(pkg.name))
        self.varMap = {}    # Maps variables to storage locations.
        self.constMap = {}
        self.const_workset = set()
        self.builder.m = ir.Module(pkg.name)
        try:
            for typ in pkg.Types:
                self.check_type(typ)
            # Only generate function if function contains a body:
            real_functions = list(filter(
                lambda f: f.body, pkg.Functions))
            for v in pkg.innerScope.Variables:
                v2 = ir.Variable(v.name, ir.i32)
                self.varMap[v] = v2
                if not v.isLocal:
                    self.builder.m.add_variable(v2)
                else:
                    raise NotImplementedError('TODO')
            for s in real_functions:
                self.gen_function(s)
        except SemanticError as e:
            self.error(e.msg, e.loc)
        if self.pkg.ok:
            return self.builder.m

    def error(self, msg, loc=None):
        self.pkg.ok = False
        self.diag.error(msg, loc)

    def gen_function(self, fn):
        # TODO: handle arguments
        ir_function = self.builder.new_function(fn.name)
        self.builder.setFunction(ir_function)
        l2 = self.builder.newBlock()
        self.emit(ir.Jump(l2))
        self.builder.setBlock(l2)

        # generate room for locals:
        for sym in fn.innerScope:
            self.check_type(sym.typ)
            if sym.isParameter:
                # For paramaters, allocate space and copy the value into
                # memory. Later, the mem2reg pass will extract these values.
                parameter = ir.Parameter(sym.name, ir.i32)
                variable = ir.Alloc(sym.name + '_copy', ir.i32)
                self.emit(variable)
                ir_function.add_parameter(parameter)
                # Move parameter into local copy:
                self.emit(ir.Store(parameter, variable))
            elif sym.isLocal or isinstance(sym, ast.Variable):
                # TODO: allocate space for variables
                variable = ir.Alloc(sym.name, ir.i32)
                self.emit(variable)
            else:
                raise NotImplementedError('{}'.format(sym))
            self.varMap[sym] = variable

        self.gen_stmt(fn.body)
        # self.emit(ir.Move(f.return_value, ir.Const(0)))
        self.emit(ir.Jump(ir_function.epiloog))
        self.builder.setBlock(ir_function.epiloog)
        self.builder.setFunction(None)

    def gen_stmt(self, code):
        """ Generate code for a statement """
        try:
            assert isinstance(code, ast.Statement)
            self.builder.setLoc(code.loc)
            if type(code) is ast.Compound:
                for s in code.statements:
                    self.gen_stmt(s)
            elif type(code) is ast.Empty:
                pass
            elif type(code) is ast.Assignment:
                self.gen_assignment_stmt(code)
            elif type(code) is ast.ExpressionStatement:
                self.gen_expr_code(code.ex)
            elif type(code) is ast.If:
                self.gen_if_stmt(code)
            elif type(code) is ast.Return:
                self.gen_return_stmt(code)
            elif type(code) is ast.While:
                self.gen_while(code)
            elif type(code) is ast.For:
                self.gen_for_stmt(code)
            elif type(code) is ast.Switch:
                raise NotImplementedError('Unknown stmt {}'.format(code))
            else:
                raise NotImplementedError('Unknown stmt {}'.format(code))
        except SemanticError as exc:
            self.error(exc.msg, exc.loc)

    def gen_return_stmt(self, code):
        """ Generate code for return statement """
        re = self.gen_expr_code(code.expr)
        self.emit(ir.Return(re))
        block = self.builder.newBlock()
        self.builder.setBlock(block)

    def gen_assignment_stmt(self, code):
        """ Generate code for assignment statement """
        lval = self.gen_expr_code(code.lval)
        rval = self.make_rvalue_expr(code.rval)
        if not self.equal_types(code.lval.typ, code.rval.typ):
            raise SemanticError('Cannot assign {} to {}'
                                .format(code.rval.typ, code.lval.typ),
                                code.loc)
        if not code.lval.lvalue:
            raise SemanticError('No valid lvalue {}'.format(code.lval),
                                code.lval.loc)
        # TODO: for now treat all stores as volatile..
        # TODO: determine volatile properties from type??
        volatile = True
        store_ins = ir.Store(rval, lval, volatile=volatile)
        self.emit(store_ins)

    def gen_if_stmt(self, code):
        """ Generate code for if statement """
        true_block = self.builder.newBlock()
        bbfalse = self.builder.newBlock()
        final_block = self.builder.newBlock()
        self.gen_cond_code(code.condition, true_block, bbfalse)
        self.builder.setBlock(true_block)
        self.gen_stmt(code.truestatement)
        self.emit(ir.Jump(final_block))
        self.builder.setBlock(bbfalse)
        self.gen_stmt(code.falsestatement)
        self.emit(ir.Jump(final_block))
        self.builder.setBlock(final_block)

    def gen_while(self, code):
        """ Generate code for while statement """
        bbdo = self.builder.newBlock()
        test_block = self.builder.newBlock()
        final_block = self.builder.newBlock()
        self.emit(ir.Jump(test_block))
        self.builder.setBlock(test_block)
        self.gen_cond_code(code.condition, bbdo, final_block)
        self.builder.setBlock(bbdo)
        self.gen_stmt(code.statement)
        self.emit(ir.Jump(test_block))
        self.builder.setBlock(final_block)

    def gen_for_stmt(self, code):
        """ Generate for statement code """
        bbdo = self.builder.newBlock()
        test_block = self.builder.newBlock()
        final_block = self.builder.newBlock()
        self.gen_stmt(code.init)
        self.emit(ir.Jump(test_block))
        self.builder.setBlock(test_block)
        self.gen_cond_code(code.condition, bbdo, final_block)
        self.builder.setBlock(bbdo)
        self.gen_stmt(code.statement)
        self.gen_stmt(code.final)
        self.emit(ir.Jump(test_block))
        self.builder.setBlock(final_block)

    def gen_cond_code(self, expr, bbtrue, bbfalse):
        """ Generate conditional logic.
            Implement sequential logical operators. """
        if type(expr) is ast.Binop:
            if expr.op == 'or':
                l2 = self.builder.newBlock()
                self.gen_cond_code(expr.a, bbtrue, l2)
                if not self.equal_types(expr.a.typ, self.boolType):
                    raise SemanticError('Must be boolean', expr.a.loc)
                self.builder.setBlock(l2)
                self.gen_cond_code(expr.b, bbtrue, bbfalse)
                if not self.equal_types(expr.b.typ, self.boolType):
                    raise SemanticError('Must be boolean', expr.b.loc)
            elif expr.op == 'and':
                l2 = self.builder.newBlock()
                self.gen_cond_code(expr.a, l2, bbfalse)
                if not self.equal_types(expr.a.typ, self.boolType):
                    self.error('Must be boolean', expr.a.loc)
                self.builder.setBlock(l2)
                self.gen_cond_code(expr.b, bbtrue, bbfalse)
                if not self.equal_types(expr.b.typ, self.boolType):
                    raise SemanticError('Must be boolean', expr.b.loc)
            elif expr.op in ['==', '>', '<', '!=', '<=', '>=']:
                ta = self.make_rvalue_expr(expr.a)
                tb = self.make_rvalue_expr(expr.b)
                if not self.equal_types(expr.a.typ, expr.b.typ):
                    raise SemanticError('Types unequal {} != {}'
                                        .format(expr.a.typ, expr.b.typ),
                                        expr.loc)
                self.emit(ir.CJump(ta, expr.op, tb, bbtrue, bbfalse))
            else:
                raise SemanticError('non-bool: {}'.format(expr.op), expr.loc)
            expr.typ = self.boolType
        elif type(expr) is ast.Literal:
            self.gen_expr_code(expr)
            if expr.val:
                self.emit(ir.Jump(bbtrue))
            else:
                self.emit(ir.Jump(bbfalse))
        else:
            raise NotImplementedError('Unknown cond {}'.format(expr))

        # Check that the condition is a boolean value:
        if not self.equal_types(expr.typ, self.boolType):
            self.error('Condition must be boolean', expr.loc)

    def make_rvalue_expr(self, expr):
        """ Generate expression code and insert an extra load instruction
            when required
        """
        x = self.gen_expr_code(expr)
        if expr.lvalue:
            load_ins = ir.Load(x, 'loaded', ir.i32)
            self.emit(load_ins)
            return load_ins
        else:
            return x

    def gen_expr_code(self, expr):
        """ Generate code for an expression. Return the generated ir-value """
        assert isinstance(expr, ast.Expression)
        if type(expr) is ast.Binop:
            expr.lvalue = False
            if expr.op in ['+', '-', '*', '/', '<<', '>>', '|', '&']:
                a_val = self.make_rvalue_expr(expr.a)
                b_val = self.make_rvalue_expr(expr.b)
                if self.equal_types(expr.a.typ, self.intType) and \
                        self.equal_types(expr.b.typ, self.intType):
                    expr.typ = expr.a.typ
                elif self.equal_types(expr.b.typ, self.intType) and \
                        type(expr.a.typ) is ast.PointerType:
                    # Special case for pointer arithmatic TODO: coerce!
                    expr.typ = expr.a.typ
                else:
                    raise SemanticError('Can only add integers', expr.loc)
            else:
                raise NotImplementedError("Cannot use equality as expressions")
            return self.emit(ir.Binop(a_val, expr.op, b_val, "op", ir.i32))
        elif type(expr) is ast.Unop:
            if expr.op == '&':
                ra = self.gen_expr_code(expr.a)
                expr.typ = ast.PointerType(expr.a.typ)
                if not expr.a.lvalue:
                    raise SemanticError('No valid lvalue', expr.a.loc)
                expr.lvalue = False
                return ra
            else:
                raise NotImplementedError('Unknown unop {0}'.format(expr.op))
        elif type(expr) is ast.Identifier:
            # Generate code for this identifier.
            tg = self.resolve_symbol(expr)
            expr.kind = type(tg)
            expr.typ = tg.typ

            # This returns the dereferenced variable.
            if isinstance(tg, ast.Variable):
                expr.lvalue = True
                return self.varMap[tg]
            elif isinstance(tg, ast.Constant):
                expr.lvalue = False
                c_val = self.get_constant_value(tg)
                return self.emit(ir.Const(c_val, tg.name, ir.i32))
            else:
                raise NotImplementedError(str(tg))
        elif type(expr) is ast.Deref:
            # dereference pointer type:
            addr = self.gen_expr_code(expr.ptr)
            ptr_typ = self.the_type(expr.ptr.typ)
            expr.lvalue = True
            if type(ptr_typ) is not ast.PointerType:
                raise SemanticError('Cannot deref non-pointer', expr.loc)
            expr.typ = ptr_typ.ptype
            return self.emit(ir.Load(addr, 'loaded', ir.i32))
        elif type(expr) is ast.Member:
            return self.gen_member_expr(expr)
        elif type(expr) is ast.Index:
            return self.gen_index_expr(expr)
        elif type(expr) is ast.Literal:
            return self.gen_literal_expr(expr)
        elif type(expr) is ast.TypeCast:
            return self.gen_type_cast(expr)
        elif type(expr) is ast.Sizeof:
            # The type of this expression is int:
            expr.lvalue = False  # This is not a location value..
            expr.typ = self.intType
            self.check_type(expr.query_typ)
            type_size = self.size_of(expr.query_typ)
            return self.emit(ir.Const(type_size, 'sizeof', ir.i32))
        elif type(expr) is ast.FunctionCall:
            return self.gen_function_call(expr)
        else:
            raise NotImplementedError('Unknown expr {}'.format(expr))

    def get_constant_value(self, c):
        """ Get the constant value, calculate if required """
        assert isinstance(c, ast.Constant)
        if c not in self.constMap:
            if c in self.const_workset:
                varnames = ', '.join(wc.name for wc in self.const_workset)
                msg = 'Constant loop detected involving: {}'.format(varnames)
                raise SemanticError(msg, c.loc)
            self.const_workset.add(c)
            c_val = self.gen_expr_code(c.value)
            self.constMap[c] = self.eval_constant(c_val)
            self.const_workset.remove(c)
        return self.constMap[c]

    def gen_member_expr(self, expr):
        """ Generate code for member expression such as struc.mem = 2 """
        base = self.gen_expr_code(expr.base)
        expr.lvalue = expr.base.lvalue
        basetype = self.the_type(expr.base.typ)
        if type(basetype) is ast.StructureType:
            if basetype.hasField(expr.field):
                expr.typ = basetype.fieldType(expr.field)
            else:
                raise SemanticError('{} does not contain field {}'
                                    .format(basetype, expr.field),
                                    expr.loc)
        else:
            raise SemanticError('Cannot select {} of non-structure type {}'
                                .format(expr.field, basetype), expr.loc)

        # expr must be lvalue because we handle with addresses of variables
        assert expr.lvalue

        # assert type(base) is ir.Mem, type(base)
        # Calculate offset into struct:
        bt = self.the_type(expr.base.typ)
        offset = ir.Const(bt.fieldOffset(expr.field), 'offset', ir.i32)
        self.emit(offset)

        # Calculate memory address of field:
        addr_ins = ir.Add(base, offset, "mem_addr", ir.i32)
        self.emit(addr_ins)
        # TODO: Load value when its an l value
        return addr_ins

    def gen_index_expr(self, expr):
        """ Array indexing """
        base = self.gen_expr_code(expr.base)
        idx = self.make_rvalue_expr(expr.i)

        base_typ = self.the_type(expr.base.typ)
        if not isinstance(base_typ, ast.ArrayType):
            raise SemanticError('Cannot index non-array type {}'
                                .format(base_typ),
                                expr.base.loc)
        idx_type = self.the_type(expr.i.typ)
        if not self.equal_types(idx_type, self.intType):
            raise SemanticError('Index must be int not {}'
                                .format(idx_type), expr.i.loc)

        # Base address must be a location value:
        assert expr.base.lvalue
        element_type = self.the_type(base_typ.element_type)
        element_size = self.size_of(element_type)
        expr.typ = base_typ.element_type
        expr.lvalue = True

        # Generate constant:
        e_size = ir.Const(element_size, 'element_size', ir.i32)
        self.emit(e_size)

        # Calculate offset:
        offset = ir.Mul(idx, e_size, "element_offset", ir.i32)
        self.emit(offset)

        # Calculate address:
        addr = ir.Add(base, offset, "element_address", ir.i32)
        self.emit(addr)
        return addr

    def gen_literal_expr(self, expr):
        """ Generate code for literal """
        expr.lvalue = False
        typemap = {int: 'int',
                   float: 'double',
                   bool: 'bool',
                   str: 'string'}
        if type(expr.val) in typemap:
            expr.typ = self.pkg.scope[typemap[type(expr.val)]]
        else:
            raise SemanticError('Unknown literal type {}'
                                .format(expr.val), expr.loc)
        # Construct correct const value:
        if type(expr.val) is str:
            cval = pack_string(expr.val)
            txt_content = ir.Const(cval, 'strval', ir.i32)
            self.emit(txt_content)
            value = ir.Addr(txt_content, 'addroftxt', ir.i32)
        else:
            value = ir.Const(expr.val, 'cnst', ir.i32)
        self.emit(value)
        return value

    def gen_type_cast(self, expr):
        """ Generate code for type casting """
        ar = self.gen_expr_code(expr.a)

        # Retain lvalue property, TBD is this correct???:
        expr.lvalue = expr.a.lvalue

        from_type = self.the_type(expr.a.typ)
        to_type = self.the_type(expr.to_type)
        if isinstance(from_type, ast.PointerType) and \
                isinstance(to_type, ast.PointerType):
            expr.typ = expr.to_type
            return ar
        elif self.equal_types(self.intType, from_type) and \
                isinstance(to_type, ast.PointerType):
            expr.typ = expr.to_type
            return ar
        elif self.equal_types(self.intType, to_type) \
                and isinstance(from_type, ast.PointerType):
            expr.typ = expr.to_type
            return ar
        elif type(from_type) is ast.BaseType and from_type.name == 'byte' and \
                type(to_type) is ast.BaseType and to_type.name == 'int':
            expr.typ = expr.to_type
            return ar
        else:
            raise SemanticError('Cannot cast {} to {}'
                                .format(from_type, to_type), expr.loc)

    def gen_function_call(self, expr):
        """ Generate code for a function call """
        # Evaluate the arguments:
        args = [self.make_rvalue_expr(argument) for argument in expr.args]

        # Check arguments:
        tg = self.resolve_symbol(expr.proc)
        if type(tg) is not ast.Function:
            raise SemanticError('cannot call {}'.format(tg))
        ftyp = tg.typ
        fname = tg.package.name + '_' + tg.name
        ptypes = ftyp.parametertypes
        if len(expr.args) != len(ptypes):
            raise SemanticError('{} requires {} arguments, {} given'
                                .format(fname, len(ptypes), len(expr.args)),
                                expr.loc)
        for arg, at in zip(expr.args, ptypes):
            if not self.equal_types(arg.typ, at):
                raise SemanticError('Got {}, expected {}'
                                    .format(arg.typ, at), arg.loc)
        # determine return type:
        expr.typ = ftyp.returntype

        expr.lvalue = False
        call = ir.Call(fname, args, fname + '_rv', ir.i32)
        self.emit(call)
        return call

    def eval_constant(self, constant):
        """ Evaluates constant to its value """
        if isinstance(constant, ir.Const):
            return constant.value
        elif isinstance(constant, ir.Binop):
            a = self.eval_constant(constant.a)
            b = self.eval_constant(constant.b)
            if constant.operation == '+':
                return a + b
            elif constant.operation == '-':
                return a - b
            elif constant.operation == '*':
                return a * b
        raise SemanticError('Cannot evaluate constant {}'.format(constant), None)

    def resolve_symbol(self, sym):
        """ Find out what is designated with x """
        if type(sym) is ast.Member:
            base = self.resolve_symbol(sym.base)
            if type(base) is not ast.Package:
                raise SemanticError('Base is not a package', sym.loc)
            scope = base.innerScope
            name = sym.field
        elif type(sym) is ast.Identifier:
            scope = sym.scope
            name = sym.target
        else:
            raise NotImplementedError(str(sym))
        if name in scope:
            sym = scope[name]
        else:
            raise SemanticError('{} undefined'.format(name), sym.loc)
        assert isinstance(sym, ast.Symbol)
        return sym

    def size_of(self, typ):
        """ Determine the byte size of a type """
        typ = self.the_type(typ)
        if type(typ) is ast.BaseType:
            return typ.bytesize
        elif type(typ) is ast.StructureType:
            return sum(self.size_of(mem.typ) for mem in typ.mems)
        elif type(typ) is ast.ArrayType:
            return typ.size * self.size_of(typ.element_type)
        elif type(typ) is ast.PointerType:
            return self.pointerSize
        else:
            raise NotImplementedError(str(typ))

    def the_type(self, t, reveil_defined=True):
        """ Recurse until a 'real' type is found
            When reveil_defined is True, defined types are resolved to
            their backing types.
        """
        if type(t) is ast.DefinedType:
            if reveil_defined:
                t = self.the_type(t.typ)
        elif type(t) in [ast.Identifier, ast.Member]:
            t = self.the_type(self.resolve_symbol(t), reveil_defined)
        elif isinstance(t, ast.Type):
            pass
        else:
            raise NotImplementedError(str(t))
        assert isinstance(t, ast.Type)
        return t

    def equal_types(self, a, b, byname=False):
        """ Compare types a and b for structural equavalence.
            if byname is True stop on defined types.
        """
        # Recurse into named types:
        a = self.the_type(a, not byname)
        b = self.the_type(b, not byname)

        # Check types for sanity:
        self.check_type(a)
        self.check_type(b)

        # Do structural equivalence check:
        if type(a) is type(b):
            if type(a) is ast.BaseType:
                return a.name == b.name
            elif type(a) is ast.PointerType:
                # If a pointed type is detected, stop structural
                # equivalence:
                return self.equal_types(a.ptype, b.ptype, byname=True)
            elif type(a) is ast.StructureType:
                if len(a.mems) != len(b.mems):
                    return False
                return all(self.equal_types(am.typ, bm.typ) for am, bm in
                           zip(a.mems, b.mems))
            elif type(a) is ast.ArrayType:
                return self.equal_types(a.element_type, b.element_type)
            elif type(a) is ast.DefinedType:
                # Try by name in case of defined types:
                return a.name == b.name
            else:
                raise NotImplementedError('{} not implemented'.format(type(a)))
        return False

    def check_type(self, t, first=True, byname=False):
        """ Determine struct offsets and check for recursiveness by using
            mark and sweep algorithm.
            The calling function could call this function with first set
            to clear the marks.
        """

        # Reset the mark and sweep:
        if first:
            self.got_types = set()

        # Resolve the type:
        t = self.the_type(t, not byname)

        # Check for recursion:
        if t in self.got_types:
            raise SemanticError('Recursive data type {}'.format(t), None)

        if type(t) is ast.BaseType:
            pass
        elif type(t) is ast.PointerType:
            # If a pointed type is detected, stop structural
            # equivalence:
            self.check_type(t.ptype, first=False, byname=True)
        elif type(t) is ast.StructureType:
            self.got_types.add(t)
            # Setup offsets of fields. Is this the right place?:
            offset = 0
            for struct_member in t.mems:
                self.check_type(struct_member.typ, first=False)
                struct_member.offset = offset
                offset = offset + self.size_of(struct_member.typ)
        elif type(t) is ast.ArrayType:
            self.check_type(t.element_type, first=False)
        elif type(t) is ast.DefinedType:
            pass
        else:
            raise NotImplementedError('{} not implemented'.format(type(t)))
