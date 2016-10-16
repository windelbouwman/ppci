import unittest
import io
import os
from ppci.lang.llvmir import LlvmIrFrontend
from ppci.common import CompilerError
from util import relpath, source_files


def create_test_function(source):
    """ Create a test function for a source file """
    with open(source) as f:
        snippet = f.read()

    def tst_func(slf):
        slf.do(snippet)
    return tst_func


def add_samples(*folders):
    """ Create a decorator function that adds tests in the given folders """
    def deco(cls):
        for folder in folders:
            for source in source_files(relpath('data', folder), '.ll'):
                tf = create_test_function(source)
                basename = os.path.basename(source)
                func_name = 'test_' + os.path.splitext(basename)[0]
                assert not hasattr(cls, func_name)
                setattr(cls, func_name, tf)
        return cls
    return deco


@add_samples('llvm')
class LlvmIrFrontendTestCase(unittest.TestCase):
    def do(self, src):
        f = io.StringIO(src)
        try:
            LlvmIrFrontend().compile(f)
        except CompilerError as e:
            lines = src.split('\n')
            e.render(lines)
            raise

