
import logging
from . import nodes
from ... import ir


class CodeGenerator:
    logger = logging.getLogger('llvm-gen')

    def generate(self, module):
        """ Convert LLVM IR-module to ppci IR-module """
        assert isinstance(module, nodes.Module)
        self.logger.debug('generating ir-code from llvm ir-code')
        self.logger.warning('ir code generation not functional yet')
        m = ir.Module('TODO')
        for function in module.functions:
            self.gen_function(function)
        return m

    def gen_function(self, function):
        for basic_block in function:
            for instruction in basic_block:
                self.gen_instruction()

    def gen_instruction(self, instruction):
        pass
