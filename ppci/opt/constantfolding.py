import operator
from .transform import BlockPass
from .. import ir


def correct(value, ty):
    """ Correct a value to the given bits """
    bits = ty.bits
    signed = ty.signed
    base = 1 << bits
    value %= base
    return value - base if signed and value.bit_length() == bits else value


def enhance(f):
    """ Create a new enhanced method that corrects for the given type """
    return lambda ty, a, b: correct(f(a, b), ty)


class ConstantFolder(BlockPass):
    """ Try to fold common constant expressions """
    def __init__(self, debug_db):
        super().__init__(debug_db)
        self.ops = {
            '+': enhance(operator.add),
            '-': enhance(operator.sub),
            '*': enhance(operator.mul),
            '%': enhance(operator.mod),
            '<<': enhance(operator.lshift),
            '>>': enhance(operator.rshift),
            }

    def is_const(self, value):
        """ Determine if a value can be evaluated as a constant value """
        if isinstance(value, ir.Const):
            return True
        elif isinstance(value, ir.Cast) and value.ty.is_integer:
            return self.is_const(value.src)
        elif isinstance(value, ir.Binop):
            return value.operation in self.ops and value.ty.is_integer and \
                self.is_const(value.a) and self.is_const(value.b)
        else:
            return False

    def eval_const(self, value):
        """ Evaluate expression, and return a new const instance """
        if isinstance(value, ir.Const):
            return value
        elif isinstance(value, ir.Binop):
            a = self.eval_const(value.a)
            b = self.eval_const(value.b)
            assert a.ty is b.ty
            assert a.ty is value.ty
            res = self.ops[value.operation](value.ty, a.value, b.value)
            return ir.Const(res, 'new_fold', a.ty)
        elif isinstance(value, ir.Cast):
            c_val = self.eval_const(value.src)
            return ir.Const(correct(c_val.value, value.ty), 'casted', value.ty)
        else:  # pragma: no cover
            raise NotImplementedError(str(value))

    def on_block(self, block):
        instructions = list(block)
        count = 0
        for instruction in instructions:
            if not isinstance(instruction, ir.Const) and \
                    self.is_const(instruction):
                # Now we can replace x = (4+5) with x = 9
                cnst = self.eval_const(instruction)
                block.insert_instruction(cnst, before_instruction=instruction)
                instruction.replace_by(cnst)
                count += 1
            else:
                if isinstance(instruction, ir.Binop) and \
                        isinstance(instruction.a, ir.Binop) and \
                        instruction.a.operation == '+' and \
                        self.is_const(instruction.a.b) and \
                        (instruction.operation == '+') and \
                        self.is_const(instruction.b):
                    # Now we can replace x = (y+5)+5 with x = y + 10
                    a = self.eval_const(instruction.a.b)
                    b = self.eval_const(instruction.b)
                    assert a.ty is b.ty
                    cn = ir.Const(a.value + b.value, 'new_fold', a.ty)
                    block.insert_instruction(
                        cn, before_instruction=instruction)
                    instruction.a = instruction.a.a
                    instruction.b = cn
                    assert instruction.ty is cn.ty
                    assert instruction.ty is instruction.a.ty
                    count += 1
                elif isinstance(instruction, ir.Binop) and \
                        isinstance(instruction.a, ir.Binop) and \
                        instruction.a.operation == '-' and \
                        self.is_const(instruction.a.b) and \
                        instruction.operation == '-' and \
                        self.is_const(instruction.b):
                    # Now we can replace x = (y-5)-5 with x = y - 10
                    a = self.eval_const(instruction.a.b)
                    b = self.eval_const(instruction.b)
                    assert a.ty is b.ty
                    cn = ir.Const(a.value + b.value, 'new_fold', a.ty)
                    block.insert_instruction(
                        cn, before_instruction=instruction)
                    instruction.a = instruction.a.a
                    instruction.b = cn
                    assert instruction.ty is cn.ty
                    assert instruction.ty is instruction.a.ty
                    count += 1
        if count > 0:
            self.logger.debug('Folded %i expressions', count)
