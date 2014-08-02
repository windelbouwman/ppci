import unittest
import os

from ppci.objectfile import ObjectFile
import ppci
from ppci import commands
from ppci.target import target_list

# Store testdir for safe switch back to directory:
testdir = os.path.dirname(os.path.abspath(__file__))

def relpath(*args):
    return os.path.join(testdir, *args)


class ZccBaseTestCase(unittest.TestCase):
    def callZcc(self, arg_list):
        parser = commands.make_parser()
        arg_list = ['--log', 'warn'] + arg_list
        args = parser.parse_args(arg_list)
        self.assertEqual(0, commands.main(args))

    def buildRecipe(self, recipe, targetlist=[]):
        arg_list = ['--buildfile', recipe] + targetlist
        self.callZcc(arg_list)


class ZccTestCase(ZccBaseTestCase):
    """ Tests the compiler driver """
    def setUp(self):
        self.skipTest('TODO')
        os.chdir(testdir)

    def tearDown(self):
        os.chdir(testdir)

    def do(self, filenames, imps=[], extra_args=[]):
        return
        basedir = relpath('..', 'examples', 'c3')
        arg_list = ['compile']
        arg_list += [os.path.join(basedir, fn) for fn in filenames]
        for fn in imps:
            arg_list.append('-i')
            arg_list.append(os.path.join(basedir, fn))
        arg_list.append('--target')
        arg_list.append('thumb')
        arg_list += extra_args
        self.callZcc(arg_list)

    @unittest.skip('Api change')
    def testDumpIr(self):
        basedir = relpath('..', 'examples', 'c3', 'comments.c3')
        arg_list = ['compile', basedir]
        arg_list.append('--target')
        arg_list.append('thumb')
        self.callZcc(arg_list)

    def testBurn2(self):
        recipe = relpath('..', 'examples', 'c3', 'build.xml')
        self.buildRecipe(recipe)

    def test_hello_A9_c3_recipe(self):
        recipe = relpath('data', 'realview-pb-a8', 'build.xml')
        self.buildRecipe(recipe)

    @unittest.skip('Skip because of logfile')
    def testBurn2WithLogging(self):
        self.do(['burn2.c3'], ['stm32f4xx.c3'], extra_args=['--report', 'x.rst'])

    def testCommentsExample(self):
        self.do(['comments.c3'])

    def testCast(self):
        self.do(['cast.c3'])

    def testFunctions(self):
        self.do(['functions.c3'])


if __name__ == '__main__':
    unittest.main()
