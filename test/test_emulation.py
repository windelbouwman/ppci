import unittest
import os

from ppci.api import construct
from util import relpath, has_qemu, run_qemu, do_long_tests


EXAMPLE_DIR = relpath('..', 'examples')


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
class EmulationTestCase(unittest.TestCase):
    """ Tests the compiler driver """

    def test_m3_bare(self):
        """ Build bare m3 binary and emulate it """
        recipe = relpath('..', 'examples', 'lm3s6965evb', 'bare', 'build.xml')
        construct(recipe)
        if has_qemu():
            bin_file = relpath(
                '..', 'examples', 'lm3s6965evb', 'bare', 'bare.bin')
            data = run_qemu(bin_file)
            self.assertEqual('Hello worle', data)

    def test_a9_bare(self):
        """ Build vexpress cortex-A9 binary and emulate it """
        recipe = relpath('..', 'examples', 'realview-pb-a8', 'build.xml')
        construct(recipe)
        if has_qemu():
            bin_file = relpath('..', 'examples', 'realview-pb-a8', 'hello.bin')
            data = run_qemu(bin_file, machine='realview-pb-a8')
            self.assertEqual('Hello worle', data)


def add_test(cls, filename):
    """ Create a new test function and add it to the class """
    name2 = os.path.relpath(filename, EXAMPLE_DIR)
    test_name = 'test_' + ''.join(x if x.isalnum() else '_' for x in name2)

    def test_func(self):
        construct(filename)

    test_func.__doc__ = 'Try to build example {}'.format(name2)
    setattr(cls, test_name, test_func)


def add_examples(cls):
    """ Add all build.xml files as a test case to the class """
    for root, _, files in os.walk(EXAMPLE_DIR):
        for filename in files:
            if filename == 'build.xml':
                fullfilename = os.path.join(root, filename)
                add_test(cls, fullfilename)
    return cls


@unittest.skipUnless(do_long_tests(), 'skipping slow tests')
@add_examples
class ExampleProjectsTestCase(unittest.TestCase):
    """ Check whether the example projects work """
    pass


if __name__ == '__main__':
    unittest.main(verbosity=2)
