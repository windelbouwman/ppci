""" Transform ocaml bytecode into ir-code.

Following the same line as described here:
https://www.irif.fr/~balat/publications/vouillon_balat-js_of_ocaml.pdf

"""

import logging
from ... import ir
from .opcodes import Opcode


logger = logging.getLogger("ocaml")


def ocaml_to_ir(module):
    """ Transform ocaml bytecode into ir-code. """
    # Detect blocks first:
    instructions = module["CODE"]

    g = Gen()
    return g.gen(instructions)


class Gen:
    def __init__(self):
        self._accumulator = None
        self._stack = []
        self._pc = 0
        self._callstack = []
        self._blocks = {}

    def gen(self, instructions):
        """ Generate code from instruction stream. """
        self.instructions = instructions
        self.indirect = {i.label: i for i in instructions}

        self.make_blocks()

        self.ir_module = ir.Module("fubar")

        self.walk_program()
        # for instruction in instructions:
        #    self.gen_ins(instruction)

        return self.ir_module

    def create_block(self, label):
        # print('Create block', label)
        if label not in self.indirect:
            raise ValueError("Invalid label targetting no instruction")

        if label in self._blocks:
            block = self._blocks[label]
        else:
            name = "block{}".format(label)
            block = ir.Block(name)
            self._blocks[label] = block
        return block

    def make_blocks(self):
        """ Determine basic blocks of instruction sequence """
        logger.debug("Splitting bytecode into blocks")

        conditional_branches = [
            Opcode.BEQ,
            Opcode.BNEQ,
            Opcode.BLTINT,
            Opcode.BLEINT,
            Opcode.BGTINT,
            Opcode.BGEINT,
            Opcode.BULTINT,
            Opcode.BUGEINT,
        ]
        branches = [Opcode.BRANCH, Opcode.BRANCHIF, Opcode.BRANCHIFNOT]

        # First instruction is header of a new block:
        new_block = True
        for instruction in self.instructions:
            # print(instruction.label, instruction)
            # Get label and opcode:
            label = instruction.label
            opcode = instruction.opcode

            # If we start at a new block, add block start:
            if new_block:
                self.create_block(label)
                new_block = False

            # Determine by opcode if block is begin or end?
            if opcode == Opcode.RETURN:
                new_block = True
            elif opcode in conditional_branches:
                target = label + instruction.args[1] + 2
                self.create_block(target)
                # Fall through next block:
                new_block = True
            elif opcode in branches:
                target = label + instruction.args[0] + 1
                self.create_block(target)
                new_block = True

        # print(self._blocks)

    def fetch(self):
        ins = self.indirect[self._pc]
        self._pc += 1
        return ins

    def walk_program(self):
        """ Recursively visit the whole bytecode program. """
        logger.debug("Taking a stroll through the bytecode")
        self.visited = set()
        while True:
            ins = self.fetch()
            if ins in self.visited:
                pass
            else:
                self.visited.add(ins)
                self.gen_ins(ins)

    def visit_blocks(self):
        """ Visit all instructions to determine stack size at entry.
        """
        self.visited.add(i)

    def gen_ins(self, instruction):
        """ Generate instruction code """
        logger.debug("%s: %s", instruction.label, instruction)
        # label = instruction.label
        opcode = instruction.opcode
        if opcode == Opcode.ACC0:
            self.do_acc(0)
        elif opcode == Opcode.ACC1:
            self.do_acc(1)
        elif opcode == Opcode.ACC2:
            self.do_acc(2)
        elif opcode == Opcode.ACC3:
            self.do_acc(3)
        elif opcode == Opcode.ACC4:
            self.do_acc(4)
        elif opcode == Opcode.ACC5:
            self.do_acc(5)
        elif opcode == Opcode.ACC6:
            self.do_acc(6)
        elif opcode == Opcode.ACC7:
            self.do_acc(7)
        elif opcode == Opcode.ACC:
            n = instruction.args[0]
            self.do_acc(n)
        elif opcode == Opcode.PUSH:
            self.do_push()
        elif opcode == Opcode.PUSHACC0:
            self.do_push()
            self.do_acc(0)
        elif opcode == Opcode.PUSHACC1:
            self.do_push()
            self.do_acc(1)
        elif opcode == Opcode.PUSHACC2:
            self.do_push()
            self.do_acc(2)
        elif opcode == Opcode.PUSHACC3:
            self.do_push()
            self.do_acc(3)
        elif opcode == Opcode.PUSHACC4:
            self.do_push()
            self.do_acc(4)
        elif opcode == Opcode.PUSHACC5:
            self.do_push()
            self.do_acc(5)
        elif opcode == Opcode.PUSHACC6:
            self.do_push()
            self.do_acc(6)
        elif opcode == Opcode.PUSHACC7:
            self.do_push()
            self.do_acc(7)
        elif opcode == Opcode.PUSHACC:
            n = instruction.args[0]
            self.do_push()
            self.do_acc(n)
        elif opcode == Opcode.POP:
            n = instruction.args[0]
            for _ in range(n):
                self._stack.pop()
        elif opcode == Opcode.ASSIGN:
            n = instruction.args[0]
            self._stack[n] = self._accumulator
            self._accumulator = None
        elif opcode == Opcode.ENVACC1:
            self.do_envacc(1)
        elif opcode == Opcode.ENVACC2:
            self.do_envacc(2)
        elif opcode == Opcode.ENVACC3:
            self.do_envacc(3)
        elif opcode == Opcode.ENVACC4:
            self.do_envacc(4)
        elif opcode == Opcode.ENVACC:
            n = instruction.args[0]
            self.do_envacc(n)
        elif opcode == Opcode.PUSHENVACC1:
            self.do_push()
            self.do_envacc(1)
        elif opcode == Opcode.PUSHENVACC2:
            self.do_push()
            self.do_envacc(2)
        elif opcode == Opcode.PUSHENVACC3:
            self.do_push()
            self.do_envacc(3)
        elif opcode == Opcode.PUSHENVACC4:
            self.do_push()
            self.do_envacc(4)
        elif opcode == Opcode.PUSHENVACC:
            n = instruction.args[0]
            self.do_push()
            self.do_envacc(n)
        # TODO: push-retaddr
        elif opcode == Opcode.APPLY:
            raise NotImplementedError()
        elif opcode == Opcode.APPLY1:
            raise NotImplementedError()
        elif opcode == Opcode.GETGLOBAL:
            n = instruction.args[0]
            self.do_getglobal(n)
        elif opcode == Opcode.PUSHGETGLOBAL:
            self.do_push()
            n = instruction.args[0]
            self.do_getglobal(n)
        elif opcode == Opcode.ATOM0:
            self.do_atom(0)
        elif opcode == Opcode.ATOM:
            n = instruction.args[0]
            self.do_atom(n)
        elif opcode == Opcode.PUSHATOM0:
            self.do_push()
            self.do_atom(0)
        elif opcode == Opcode.PUSHATOM:
            n = instruction.args[0]
            self.do_push()
            self.do_atom(n)
        elif opcode == Opcode.MAKEBLOCK:
            n = instruction.args[0]
            t = instruction.args[1]
            self.do_makeblock(n, t)
        elif opcode == Opcode.MAKEBLOCK1:
            t = instruction.args[0]
            self.do_makeblock(1, t)
        elif opcode == Opcode.MAKEBLOCK2:
            t = instruction.args[0]
            self.do_makeblock(2, t)
        elif opcode == Opcode.MAKEBLOCK3:
            t = instruction.args[0]
            self.do_makeblock(3, t)
        elif opcode == Opcode.GETFIELD0:
            self.do_getfield(0)
        elif opcode == Opcode.GETFIELD1:
            self.do_getfield(1)
        elif opcode == Opcode.GETFIELD2:
            self.do_getfield(2)
        elif opcode == Opcode.GETFIELD3:
            self.do_getfield(3)
        elif opcode == Opcode.GETFIELD:
            n = instruction.args[0]
            self.do_getfield(n)
        elif opcode == Opcode.BRANCH:
            ofs = instruction.args[0]
            target = self.create_block(instruction.label + ofs + 1)
            self.emit(ir.Jump(target))
        elif opcode == Opcode.CONST0:
            self.do_const(0)
        elif opcode == Opcode.CONST1:
            self.do_const(1)
        elif opcode == Opcode.CONST2:
            self.do_const(2)
        elif opcode == Opcode.CONST3:
            self.do_const(3)
        elif opcode == Opcode.CONSTINT:
            n = instruction.args[0]
            self.do_const(n)
        elif opcode == Opcode.PUSHCONST0:
            self.do_push()
            self.do_const(0)
        elif opcode == Opcode.PUSHCONST1:
            self.do_push()
            self.do_const(1)
        elif opcode == Opcode.PUSHCONST2:
            self.do_push()
            self.do_const(2)
        elif opcode == Opcode.PUSHCONST3:
            self.do_push()
            self.do_const(3)
        elif opcode == Opcode.PUSHCONSTINT:
            n = instruction.args[0]
            self.do_push()
            self.do_const(n)
        elif opcode == Opcode.ADDINT:
            self.do_binop("+")
        elif opcode == Opcode.SUBINT:
            self.do_binop("-")
        elif opcode == Opcode.MULINT:
            self.do_binop("*")
        elif opcode == Opcode.DIVINT:
            self.do_binop("/")
        elif opcode == Opcode.ANDINT:
            self.do_binop("&")
        elif opcode == Opcode.ORINT:
            self.do_binop("|")
        elif opcode == Opcode.XORINT:
            self.do_binop("^")
        elif opcode == Opcode.STOP:
            pass
        else:  # pragma: no cover
            raise NotImplementedError()

    def do_acc(self, n):
        self._accumulator = self._stack[n]

    def do_push(self):
        self._stack.append(self._accumulator)

    def do_const(self, value):
        self._accumulator = self.emit(ir.Const(value, "const", ir.i32))

    def do_makeblock(self, n, t):
        """ Create a block from accumulator and stack content """
        # block = ?
        self._accumulator = block

    def do_getfield(self, n):
        block = self._accumulator
        self._accumulator = block[n]

    def do_binop(self, op):
        a = self._accumulator
        b = self._stack.pop()
        self._accumulator = self.emit(ir.Binop(a, op, b, "binop", ir.i32))

    def emit(self, inst):
        """ Emit an ir instruction """
        print(inst)
        return inst
