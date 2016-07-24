import unittest
import io
from ppci.api import construct, asm, c3c, objcopy, disasm, link

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from ppci.tasks import TaskError
import ppci.buildtasks


class ApiTestCase(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_disasm(self, mock_stdout):
        binary_file = io.BytesIO(bytes(range(10)))
        disasm(binary_file, 'riscv')

    def test_link_without_arguments(self):
        with self.assertRaises(ValueError):
            link([])


class RecipeTestCase(unittest.TestCase):
    def test_bad_xml(self):
        recipe = """<project>"""
        with self.assertRaisesRegex(TaskError, "Invalid xml"):
            construct(io.StringIO(recipe))

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_recipe(self, mock_stdout):
        recipe = """
        <project>
            <target name="init">
                <property name="a" value="Hello" />
                <empty />
                <echo message="${a}" />
            </target>
        </project>
        """

        construct(io.StringIO(recipe), ["init"])
        self.assertIn("Hello", mock_stdout.getvalue())

    def test_missing_property(self):
        recipe = """
        <project>
            <target name="init">
                <echo message="${nonexisting}" />
            </target>
        </project>
        """

        with self.assertRaisesRegex(TaskError, 'Property .* not found'):
            construct(io.StringIO(recipe), ["init"])

    def test_missing_argument(self):
        recipe = """
        <project>
            <target name="init">
                <echo />
            </target>
        </project>
        """

        with self.assertRaisesRegex(TaskError, 'attribute .* not'):
            construct(io.StringIO(recipe), ["init"])

    def test_unknown_task(self):
        recipe = """
        <project>
            <target name="init">
                <domagic />
            </target>
        </project>
        """

        with self.assertRaisesRegex(TaskError, 'Task .* not be found'):
            construct(io.StringIO(recipe), ["init"])

    def test_nonexisting_target(self):
        recipe = """
        <project>
        </project>
        """

        with self.assertRaisesRegex(TaskError, 'target .* not found'):
            construct(io.StringIO(recipe), ["init"])

    def test_no_targets(self):
        recipe = """
        <project>
        </project>
        """

        construct(io.StringIO(recipe))


class ObjcopyTestCase(unittest.TestCase):
    def test_wrong_format(self):
        with self.assertRaises(TaskError):
            objcopy(None, None, 'invalid_format', None)


if __name__ == '__main__':
    unittest.main()
