# WIP
from ... import ir


class IrToWasmConvertor:
    def __init__(self):
        pass

    def do(self, module):
        for function in module.functions:
            self.do_function(function)

    def do_function(self, function):
        """ Generate WASM for a single function """
        for block in function:
            # TODO!
            pass

    def do_block(self, block):
        if op == '+':
            # push
            # push
            instructions.append(('f64.add', ))
            # pop
        else:
            raise NotImplementedError()

