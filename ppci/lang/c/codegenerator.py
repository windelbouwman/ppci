import logging
from ... import ir, irutils
from ...common import CompilerError
from . import nodes
from .scope import Scope


class CCodeGenerator:
    """ Converts parsed C code to ir-code """
    logger = logging.getLogger('ccodegen')

    def __init__(self, coptions, march):
        self.coptions = coptions
        self.march = march
        self.builder = None
        self.scope = None
        self.ir_var_map = {}

    def gen_code(self, compile_unit):
        """ Initial entry point for the code generator """
        self.builder = irutils.Builder()
        type_scope = Scope(None)
        type_scope.var_map.update(compile_unit.type_table)
        self.scope = Scope(type_scope)
        self.ir_var_map = {}
        self.logger.debug('Generating IR-code')
        ir_mod = ir.Module('c_compilation_unit')
        self.builder.module = ir_mod
        for declaration in compile_unit.declarations:
            assert isinstance(declaration, nodes.Declaration)
            # Insert into the current scope:
            if self.scope.is_defined(declaration.name):
                sym = self.scope.get(declaration.name)
                # The symbol might be a forward declaration:
                if self.equal_types(sym.typ, declaration.typ) and \
                        declaration.is_function:
                    self.logger.debug('okay, forward declaration implemented')
                    pass
                else:
                    self.info('First defined here', sym)
                    self.error("Invalid redefinition", declaration)
            else:
                self.scope.insert(declaration)

            # Generate code:
            if declaration.is_function:
                self.gen_function(declaration)
            else:
                self.gen_global_variable(declaration)
        self.logger.debug('Finished code generation')
        return ir_mod

    def emit(self, instruction):
        """ Helper function to emit a single instruction """
        return self.builder.emit(instruction)

    def info(self, message, node):
        """ Generate information message at the given node """
        node.loc.print_message(message)

    def error(self, message, node):
        """ Trigger an error at the given node """
        raise CompilerError(message, loc=node.loc)

    def gen_global_variable(self, var_decl):
        size = self.sizeof(var_decl.typ)
        ir_var = ir.Variable(var_decl.name, size)
        self.builder.module.add_variable(ir_var)
        self.ir_var_map[var_decl] = ir_var

    def gen_function(self, function):
        """ Generate code for a function """
        if not function.body:
            return

        if function.typ.return_type.is_void:
            ir_function = self.builder.new_procedure(function.name)
        else:
            return_type = self.get_ir_type(function.typ.return_type)
            ir_function = self.builder.new_function(function.name, return_type)

        # Nice clean slate:
        self.scope = Scope(self.scope)

        # Create entry code:
        self.builder.set_function(ir_function)
        first_block = self.builder.new_block()
        self.builder.set_block(first_block)
        ir_function.entry = first_block

        # Add arguments (create memory space for them!):
        for argument in function.arguments:
            arg_name = argument.name
            if arg_name is None:
                arg_name = 'no_name'
            else:
                if self.scope.is_defined(arg_name, all_scopes=False):
                    self.error('Illegal redefine', argument)
            self.scope.insert(argument)

            ir_typ = self.get_ir_type(argument.typ)
            ir_argument = ir.Parameter(arg_name, ir_typ)
            ir_function.add_parameter(ir_argument)
            size = self.sizeof(argument.typ)
            ir_var = self.emit(ir.Alloc(arg_name + '_alloc', size))
            self.emit(ir.Store(ir_argument, ir_var))
            self.ir_var_map[argument] = ir_var

        # Generate code for body:
        self.gen_stmt(function.body)

        if not self.builder.block.is_closed:
            # In case of void function, introduce exit instruction:
            if function.typ.return_type.is_void:
                self.emit(ir.Exit())
            else:
                if self.builder.block.is_empty:
                    last_block = self.builder.block
                    self.builder.set_block(None)
                    ir_function.delete_unreachable()
                    assert not last_block.is_used
                    assert last_block not in ir_function
                else:
                    self.error(
                        'Function does not return an {}'.format(
                            function.typ.return_type),
                        function)

        ir_function.delete_unreachable()
        self.builder.set_function(None)
        self.scope = self.scope.parent

    def gen_stmt(self, statement):
        # fn_map = {
        #    nodes.If: self.gen_if, nodes.While: self.gen_while,
        #    nodes.Return: self.gen_return
        # }
        if isinstance(statement, nodes.If):
            self.gen_if(statement)
        elif isinstance(statement, nodes.While):
            self.gen_while(statement)
        elif isinstance(statement, nodes.DoWhile):
            self.gen_do_while(statement)
        elif isinstance(statement, nodes.For):
            self.gen_for(statement)
        elif isinstance(statement, nodes.Return):
            self.gen_return(statement)
        elif isinstance(statement, nodes.Compound):
            for inner_statement in statement.statements:
                self.gen_stmt(inner_statement)
        elif isinstance(statement, nodes.Empty):
            pass
        elif isinstance(statement, nodes.Expression):
            self.gen_expr(statement)
        elif isinstance(statement, nodes.VariableDeclaration):
            self.gen_local_var(statement)
        else:  # pragma: no cover
            raise NotImplementedError(str(statement))

    def gen_if(self, stmt: nodes.If):
        """ Generate if-statement code """
        yes_block = self.builder.new_block()
        no_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.gen_condition(stmt.condition, yes_block, no_block)
        self.builder.set_block(yes_block)
        self.gen_stmt(stmt.yes)
        self.emit(ir.Jump(final_block))
        self.builder.set_block(no_block)
        self.gen_stmt(stmt.no)
        self.emit(ir.Jump(final_block))
        self.builder.set_block(final_block)

    def gen_while(self, stmt: nodes.While):
        """ Generate while statement code """
        condition_block = self.builder.new_block()
        body_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.emit(ir.Jump(condition_block))
        self.builder.set_block(condition_block)
        self.gen_condition(stmt.condition, body_block, final_block)
        self.builder.set_block(body_block)
        self.gen_stmt(stmt.body)
        self.emit(ir.Jump(condition_block))
        self.builder.set_block(final_block)

    def gen_do_while(self, stmt: nodes.DoWhile):
        """ Generate do-while-statement code """
        body_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.emit(ir.Jump(body_block))
        self.builder.set_block(body_block)
        self.gen_stmt(stmt.body)
        self.gen_condition(stmt.condition, body_block, final_block)
        self.builder.set_block(final_block)

    def gen_for(self, stmt: nodes.For):
        """ Generate code for for-statement """
        condition_block = self.builder.new_block()
        body_block = self.builder.new_block()
        final_block = self.builder.new_block()
        self.gen_stmt(stmt.init)
        self.emit(ir.Jump(condition_block))
        self.builder.set_block(condition_block)
        self.gen_condition(stmt.condition, body_block, final_block)
        self.builder.set_block(body_block)
        self.gen_stmt(stmt.body)
        self.gen_stmt(stmt.post)
        self.emit(ir.Jump(condition_block))
        self.builder.set_block(final_block)

    def gen_condition(self, condition: nodes.Expression, yes_block, no_block):
        """ Generate switch based on condition """
        if isinstance(condition, nodes.Binop):
            if condition.op == '||':
                condition.typ = self.get_type(['int'])
                middle_block = self.builder.new_block()
                self.gen_condition(condition.a, yes_block, middle_block)
                self.builder.set_block(middle_block)
                self.gen_condition(condition.b, yes_block, no_block)
            elif condition.op == '&&':
                condition.typ = self.get_type(['int'])
                middle_block = self.builder.new_block()
                self.gen_condition(condition.a, middle_block, no_block)
                self.builder.set_block(middle_block)
                self.gen_condition(condition.b, yes_block, no_block)
            elif condition.op in ['<', '>', '==', '!=', '<=', '>=']:
                lhs = self.gen_expr(condition.a, rvalue=True)
                rhs = self.gen_expr(condition.b, rvalue=True)
                op_map = {
                    '>': '>', '<': '<',
                    '==': '==', '!=': '!=',
                    '<=': '<=', '>=': '>='
                }
                condition.typ = self.get_type(['int'])
                op = op_map[condition.op]
                self.emit(ir.CJump(lhs, op, rhs, yes_block, no_block))
            else:
                self.check_non_zero(condition, yes_block, no_block)
        else:
            self.check_non_zero(condition, yes_block, no_block)

    def check_non_zero(self, expr, yes_block, no_block):
        """ Check an expression for being non-zero """
        expr_value = self.gen_expr(expr)
        ir_typ = self.get_ir_type(expr.typ)
        zero = self.emit(ir.Const(0, 'zero', ir_typ))
        self.emit(ir.CJump(expr_value, '==', zero, no_block, yes_block))

    def gen_return(self, stmt: nodes.Return):
        """ Generate return statement code """
        if stmt.value:
            return_value = self.gen_expr(stmt.value, rvalue=True)
            self.emit(ir.Return(return_value))
        else:
            self.emit(ir.Exit())

    def gen_local_var(self, variable: nodes.VariableDeclaration):
        """ Generate a local variable """
        if self.scope.is_defined(variable.name, all_scopes=False):
            self.error('Illegal redefine', variable)
        self.scope.insert(variable)

        name = variable.name
        size = self.sizeof(variable.typ)
        ir_addr = self.emit(ir.Alloc(name + '_alloc', size))
        self.ir_var_map[variable] = ir_addr

    def gen_expr(self, expr, rvalue=False):
        if isinstance(expr, nodes.Unop):
            if expr.op in ['++', '--']:
                ir_a = self.gen_expr(expr.a, rvalue=False)
                if not expr.a.lvalue:
                    self.error('Expected lvalue', expr.a)
                expr.typ = expr.a.typ

                op = expr.op[0]
                ir_typ = self.get_ir_type(expr.typ)
                loaded = self.emit(ir.Load(ir_a, 'loaded', ir_typ))
                one = self.emit(ir.Const(1, 'one', ir_typ))
                ir_value = self.emit(ir.Binop(
                    loaded, op, one, 'inc', ir_typ))
                self.emit(ir.Store(ir_value, ir_a))
            else:
                raise NotImplementedError(str(expr.op))
        elif isinstance(expr, nodes.Binop):
            if expr.op in ['+', '-', '*', '/', '%', '|', '&', '>>', '<<']:
                lhs = self.gen_expr(expr.a, rvalue=True)
                rhs = self.gen_expr(expr.b, rvalue=True)
                op = expr.op

                if not self.equal_types(expr.a.typ, expr.b.typ):
                    self.error(
                        'Mismatch {} != {}'.format(expr.a.typ, expr.b.typ),
                        expr)

                expr.typ = expr.a.typ

                # TODO: coerce!
                ir_typ = self.get_ir_type(expr.typ)
                ir_value = self.emit(ir.Binop(lhs, op, rhs, 'op', ir_typ))
                expr.lvalue = False
            elif expr.op == ',':
                # Handle the comma operator by returning the second result
                lhs = self.gen_expr(expr.a, rvalue=True)
                rhs = self.gen_expr(expr.b, rvalue=True)
                expr.typ = expr.b.typ
                ir_value = rhs
            elif expr.op in ['<', '>', '==', '!=', '<=', '>=', '||', '&&']:
                ir_typ = self.get_ir_type(expr.typ)
                yes_block = self.builder.new_block()
                no_block = self.builder.new_block()
                end_block = self.builder.new_block()
                self.gen_condition(expr, yes_block, no_block)
                self.builder.set_block(yes_block)
                yes_value = self.emit(ir.Const(1, 'one', ir_typ))
                self.emit(ir.Jump(end_block))
                self.builder.set_block(no_block)
                no_value = self.emit(ir.Const(0, 'zero', ir_typ))
                self.emit(ir.Jump(end_block))
                self.builder.set_block(end_block)
                phi = self.emit(ir.Phi('phi', ir_typ))
                phi.set_incoming(yes_block, yes_value)
                phi.set_incoming(no_block, no_value)
                ir_value = phi
                expr.lvalue = False
            elif expr.op in ['=', '+=', '-=', '*=']:
                lhs = self.gen_expr(expr.a, rvalue=False)
                ir_value = self.gen_expr(expr.b, rvalue=True)
                expr.lvalue = False
                if not self.equal_types(expr.a.typ, expr.b.typ):
                    self.error(
                        'Mismatch {} != {}'.format(expr.a.typ, expr.b.typ),
                        expr)

                expr.typ = expr.a.typ

                if not expr.a.lvalue:
                    self.error('Expected lvalue', expr.a)
                # Handle '+=' and friends:
                if expr.op != '=':
                    op = expr.op[:-1]
                    ir_typ = self.get_ir_type(expr.typ)
                    loaded = self.emit(ir.Load(lhs, 'lhs', ir_typ))
                    ir_value = self.emit(ir.Binop(
                        loaded, op, ir_value, 'assign', ir_typ))
                self.emit(ir.Store(ir_value, lhs))
            else:  # pragma: no cover
                raise NotImplementedError(str(expr.op))
        elif isinstance(expr, nodes.VariableAccess):
            if not self.scope.is_defined(expr.name):
                self.error('Who is this?', expr)
            variable = self.scope.get(expr.name)
            expr.lvalue = True
            expr.typ = variable.typ
            ir_value = self.ir_var_map[variable]
        elif isinstance(expr, nodes.FunctionCall):
            # Lookup the function:
            if not self.scope.is_defined(expr.name):
                self.error('Who is this?', expr)
            function = self.scope.get(expr.name)
            if not isinstance(function, nodes.FunctionDeclaration):
                self.error('Calling a non-function', expr)
            expr.lvalue = False
            expr.typ = function.typ.return_type
            if len(expr.args) != len(function.typ.arg_types):
                self.error('Expected {} arguments, but got {}'.format(
                    len(function.typ.arg_types), len(expr.args)), expr)
            ir_arguments = []
            for argument in expr.args:
                ir_arguments.append(self.gen_expr(argument, rvalue=True))

            if function.typ.return_type.is_void:
                self.emit(ir.ProcedureCall(function.name, ir_arguments))
                ir_value = None
            else:
                ir_typ = self.get_ir_type(expr.typ)
                ir_value = self.emit(ir.FunctionCall(
                    function.name, ir_arguments, 'result', ir_typ))
        elif isinstance(expr, nodes.Constant):
            v = int(expr.value)
            expr.typ = self.get_type(['int'])
            expr.lvalue = False
            ir_typ = self.get_ir_type(expr.typ)
            ir_value = self.emit(ir.Const(v, 'constant', ir_typ))
        elif isinstance(expr, nodes.Cast):
            # TODO: is the cast valid?
            a = self.gen_expr(expr.expr, rvalue=True)
            expr.typ = expr.to_typ
            expr.lvalue = False  # or expr.expr.lvalue?
            ir_typ = self.get_ir_type(expr.typ)
            ir_value = self.emit(ir.Cast(a, 'typecast', ir_typ))
        elif isinstance(expr, nodes.Sizeof):
            expr.typ = self.get_type(['int'])
            expr.lvalue = False
            v = self.sizeof(expr.sizeof_typ)
            ir_typ = self.get_ir_type(expr.typ)
            ir_value = self.emit(ir.Const(v, 'type_size', ir_typ))
        else:  # pragma: no cover
            raise NotImplementedError(str(expr))

        assert isinstance(expr.typ, nodes.CType)

        # If we need an rvalue, load it!
        if rvalue and expr.lvalue:
            ir_typ = self.get_ir_type(expr.typ)
            ir_value = self.emit(ir.Load(ir_value, 'load', ir_typ))
        return ir_value

    def get_type(self, names):
        """ Retrieve a type by name """
        assert isinstance(names, list)
        return nodes.IdentifierType(names)
        return nodes.IntegerType('int')
        # TODO: retrieve a nice type somehow?
        for type_specifier in names:
            if type_specifier == 'int':
                typ = nodes.IntegerType('int')
            elif type_specifier == 'void':
                typ = nodes.VoidType()
            elif type_specifier == 'char':
                typ = nodes.IntegerType('char')
            elif type_specifier == 'float':
                typ = nodes.FloatingPointType('float')
            elif type_specifier == 'double':
                typ = nodes.FloatingPointType('double')
            elif type_specifier == 'unsigned':
                typ = nodes.IntegerType('int')
            elif type_specifier == 'signed':
                typ = nodes.IntegerType('int')
            elif type_specifier == 'short':
                typ = nodes.IntegerType('int')
            elif type_specifier == 'long':
                typ = nodes.IntegerType('int')
            else:
                raise NotImplementedError(str(type_specifier))
        print(typ)

    def get_ir_type(self, typ: nodes.CType):
        """ Given a C type, get the fitting ir type """
        assert isinstance(typ, nodes.CType)

        if isinstance(typ, nodes.IdentifierType):
            if len(typ.names) == 1 and self.scope.is_defined(typ.names[0]):
                # Typedef type!
                deftyp = self.scope.get(typ.names[0])
                return self.get_ir_type(deftyp)
            else:
                if 'int' in typ.names:
                    return ir.i64
                elif 'char' in typ.names:
                    return ir.i8
                else:
                    return ir.i64
                    raise NotImplementedError(typ.names)
        elif isinstance(typ, nodes.PointerType):
            return ir.ptr
        elif isinstance(typ, nodes.FloatingPointType):
            # TODO handle float and double?
            return ir.f64
        else:
            raise NotImplementedError(str(typ))

    def equal_types(self, typ1, typ2):
        """ Check for type equality """
        # TODO: enhance!
        if typ1 is typ2:
            return True
        elif isinstance(typ1, nodes.IdentifierType):
            if isinstance(typ2, nodes.IdentifierType):
                return typ1.names == typ2.names
        elif isinstance(typ1, nodes.FunctionType):
            if isinstance(typ2, nodes.FunctionType):
                return len(typ1.arg_types) == len(typ2.arg_types) and \
                    self.equal_types(typ1.return_type, typ2.return_type) and \
                    all(self.equal_types(a1, a2) for a1, a2 in zip(
                        typ1.arg_types, typ2.arg_types))
        elif isinstance(typ1, nodes.PointerType):
            if isinstance(typ2, nodes.PointerType):
                return self.equal_types(typ1.pointed_type, typ2.pointed_type)
        else:
            raise NotImplementedError(str(typ1))
        return False

    def sizeof(self, typ: nodes.CType):
        assert isinstance(typ, nodes.CType)
        # TODO: determine based on cpu
        return 8
