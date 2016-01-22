import io
import os
import unittest
import tempfile

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from ppci.api import construct
import ppci.buildtasks
from ppci.tasks import TaskRunner, TaskError, Project, Target, Task


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

    def test_ensure_path(self):
        empty_dir = tempfile.mkdtemp()
        txt_filename = os.path.join('a', 'b', 'c.txt')
        full_path = os.path.join(empty_dir, txt_filename)
        task = Task(None, None)
        task.ensure_path(full_path)
        self.assertTrue(os.path.isdir(os.path.dirname(full_path)))

    def test_open_fileset(self):
        empty_dir = tempfile.mkdtemp()
        project = Project('a')
        project.set_property('basedir', empty_dir)
        target = Target('t1', project)
        task = Task(target, None)
        with self.assertRaisesRegex(TaskError, 'not found'):
            task.open_file_set('*.asm')


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


if __name__ == '__main__':
    unittest.main()
