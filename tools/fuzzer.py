#!/usr/bin/python

"""
Tool that randomly generates code and feeds it through the code generator.
"""

import random
import io
from ppci.api import ir_to_object
from ppci import ir
from ppci.irutils import Builder, Writer, Verifier


class Generator:
    def __init__(self):
        self.builder = Builder()
        self.verifier = Verifier()

    def gen_module(self):
        module = ir.Module("fuzz")
        self.builder.module = module

        # Generate some functions
        for i in range(random.randrange(6, 20)):
            self.gen_function("fzfnc{}".format(i))

        f = io.StringIO()
        self.verifier.verify(module)
        writer = Writer(f)
        writer.write(module)
        print(f.getvalue())
        return module

    def gen_function(self, name):
        function = self.builder.new_procedure(name)
        self.builder.set_function(function)
        first_block = self.builder.new_block()
        function.entry = first_block
        self.builder.set_block(first_block)

        for i in range(random.randrange(10, 80)):
            self.gen_ins(i)

        self.builder.emit(ir.Exit())

    def gen_ins(self, i):
        c1 = self.builder.emit(ir.Const(i, "cnsta{}".format(i), ir.i32))
        c2 = self.builder.emit(ir.Const(i + 2, "cnstb{}".format(i), ir.i32))
        self.builder.emit(ir.Binop(c1, "+", c2, "op{}".format(i), ir.i32))


def go():
    generator = Generator()
    module = generator.gen_module()

    obj = ir_to_object([module], "arm")
    print(obj)


if __name__ == "__main__":
    go()
