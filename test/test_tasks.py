import io
import unittest

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from ppci.buildfunctions import construct
from ppci.buildtasks import EmptyTask
from ppci.tasks import TaskRunner, TaskError, Project, Target


class TaskTestCase(unittest.TestCase):
    def test_circular(self):
        proj = Project('testproject')
        t1 = Target('t1', proj)
        t2 = Target('t2', proj)
        proj.add_target(t1)
        proj.add_target(t2)
        t1.add_dependency(t2.name)
        t2.add_dependency(t1.name)
        with self.assertRaisesRegex(TaskError, "Dependency loop"):
            proj.check_target(t1.name)

    def test_circular_deeper(self):
        proj = Project('testproject')
        t1 = Target('t1', proj)
        t2 = Target('t2', proj)
        t3 = Target('t3', proj)
        proj.add_target(t1)
        proj.add_target(t2)
        proj.add_target(t3)
        t1.add_dependency(t2.name)
        t2.add_dependency(t3.name)
        t3.add_dependency(t1.name)
        with self.assertRaisesRegex(TaskError, "Dependency loop"):
            proj.check_target(t1.name)

    def test_targets_same_name(self):
        """ Test two target with the same name """
        proj = Project('testproject')
        t1 = Target('compile', proj)
        t2 = Target('compile', proj)
        proj.add_target(t1)
        with self.assertRaisesRegex(TaskError, "Duplicate"):
            proj.add_target(t2)

    def test_sort(self):
        proj = Project('testproject')
        t1 = Target('t1', proj)
        t2 = Target('t2', proj)
        t1.add_dependency(t2.name)
        proj.add_target(t1)
        proj.add_target(t2)
        runner = TaskRunner()
        runner.run(proj, ['t1'])


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
