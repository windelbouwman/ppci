from ... import ir, irutils
from ...common import CompilerError
from . import nodes


class CCodeGenerator:
    def __init__(self, coptions):
        self.coptions = coptions
        self.builder = None

    def gen_code(self, compile_unit):
        self.builder = irutils.Builder()
        ir_mod = ir.Module('c_compilation_unit')
        self.builder.module = ir_mod
        for declaration in compile_unit.decls:
            assert isinstance(declaration, nodes.Declaration)
            continue
            # TODO: fix below!
            if declaration.is_function:
                self.gen_function(declaration)
            else:
                pass
        return ir_mod

    def emit(self, instruction):
        """ Helper function to emit a single instruction """
        self.builder.emit(instruction)

    def gen_variable(self, var_decl):
        # var_decl.typ
        # TODO: map types?
        size = 16  # FIXME
        ir_var = ir.Variable(var_decl.name, size)
        self.builder.module.add_variable(ir_var)

    def gen_function(self, function):
        if function.typ.return_type.is_void:
            ir_function = self.builder.new_procedure(function.name)
        else:
            return_type = self.get_ir_type(function.typ.return_type)
            ir_function = self.builder.new_function(function.name, return_type)
        self.builder.set_function(ir_function)
        first_block = self.builder.new_block()
        self.builder.set_block(first_block)
        ir_function.entry = first_block

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
                    raise CompilerError(
                        'Function does not return a value', loc=function.loc)

        ir_function.delete_unreachable()
        self.builder.set_function(None)

    def gen_stmt(self, statement):
        if isinstance(statement, nodes.If):
            self.gen_if(statement)
        elif isinstance(statement, nodes.While):
            self.gen_while(statement)
        elif isinstance(statement, nodes.Compound):
            for inner_statement in statement.statements:
                self.gen_stmt(inner_statement)
        else:
            raise NotImplementedError(str(statement))

    def gen_if(self, stmt: nodes.If):
        self.gen_expr(stmt.condition)
        self.gen_stmt(stmt.yes)
        self.gen_stmt(stmt.no)

    def gen_while(self, stmt: nodes.While):
        self.gen_stmt(stmt.body)

    def gen_expr(self, expr):
        if isinstance(expr, nodes.Binop):
            lhs = self.gen_expr(expr.a)
            rhs = self.gen_expr(expr.b)
            if expr.op == '+':
                self.emit(ir.Binop(lhs, '+', rhs, 'add', ir.i32))
            elif expr.op == '-':
                self.emit(ir.Binop(lhs, '-', rhs, 'sub', ir.i32))
            else:
                raise NotImplementedError(str(expr.op))
        else:
            raise NotImplementedError(str(expr))

    def get_ir_type(self, typ):
        """ Given a C type, get the fitting ir type """
        if isinstance(typ, nodes.IntegerType):
            assert typ.name == 'int'
            return ir.i32
        else:
            raise NotImplementedError(str(typ))
