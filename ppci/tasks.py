"""
    This module defines tasks and a runner for these tasks. Tasks can
    have dependencies and it can be determined if they need to be run.
"""

import logging
import re
import os
import glob


task_map = {}


def register_task(cls):
    """ Decorator that registers a task class under its logical name """
    assert isinstance(cls, type)
    fullname = cls.__name__.lower()
    assert fullname.endswith('task')
    name = fullname[:-4]
    assert name
    task_map[name] = cls
    return cls


class TaskError(Exception):
    """ When a task fails, this exception is raised """
    def __init__(self, msg):
        self.msg = msg


class Project:
    """ A project contains a set of named targets that can depend upon
        eachother """
    def __init__(self, name):
        self.name = name
        self.targets = {}
        self.properties = {}
        self.macro_regex = re.compile('\$\{([^\}]+)\}')

    def set_property(self, name, value):
        """ Set a property in this project """
        self.properties[name] = value

    def get_property(self, name):
        """ Get a property in this project """
        if name not in self.properties:
            raise TaskError('Property "{}" not found'.format(name))
        return self.properties[name]

    def add_target(self, target):
        """ Add a target to the project """
        if target.name in self.targets:
            raise TaskError("Duplicate target '{}'".format(target.name))
        self.targets[target.name] = target

    def get_target(self, target_name):
        assert isinstance(target_name, str)
        if target_name not in self.targets:
            raise TaskError('target "{}" not found'.format(target_name))
        return self.targets[target_name]

    def expand_macros(self, txt):
        """ Replace all macros in txt with the correct properties """
        while True:
            mo = self.macro_regex.search(txt)
            if not mo:
                break
            propname = mo.group(1)
            propval = self.get_property(propname)
            txt = txt[:mo.start()] + propval + txt[mo.end():]
        return txt

    def dfs(self, target_name, state):
        state.add(target_name)
        target = self.get_target(target_name)
        for dep in target.dependencies:
            if dep in state:
                raise TaskError('Dependency loop detected {} -> {}'
                                .format(target_name, dep))
            self.dfs(dep, state)

    def check_target(self, target_name):
        state = set()
        self.dfs(target_name, state)

    def dependencies(self, target_name):
        assert type(target_name) is str
        target = self.get_target(target_name)
        cdst = list(self.dependencies(dep) for dep in target.dependencies)
        cdst.append(target.dependencies)
        return set.union(*cdst)


class Target:
    """ Defines a target that has a name and a list of tasks to execute """
    def __init__(self, name, project):
        self.name = name
        self.project = project
        self.tasks = []
        self.dependencies = set()

    def add_task(self, task):
        self.tasks.append(task)

    def add_dependency(self, target_name):
        """ Add another task as a dependency for this task """
        self.dependencies.add(target_name)

    def __gt__(self, other):
        return other.name in self.project.dependencies(self.name)

    def __repr__(self):
        return 'Target "{}"'.format(self.name)


class Task:
    """ Task that can run, and depend on other tasks """
    def __init__(self, target, kwargs, sub_elements=[]):
        self.logger = logging.getLogger('task')
        self.target = target
        self.name = self.__class__.__name__
        self.arguments = kwargs

    def get_argument(self, name, default=None):
        if name not in self.arguments:
            if default is not None:
                return default
            else:
                raise TaskError('attribute "{}" not specified'.format(name))
        return self.arguments[name]

    def get_property(self, name):
        return self.target.project.get_property(name)

    def relpath(self, filename):
        basedir = self.get_property('basedir')
        return os.path.join(basedir, filename)

    def ensure_path(self, filename):
        """ Make sure that the path to a filename exists """
        directory_name = os.path.dirname(filename)
        if not os.path.exists(directory_name):
            os.makedirs(directory_name)

    def open_file_set(self, s):
        """ Creates a list of open file handles. s can be one of these:
            - A string like "a.c3"
            - A string like "*.c3"
            - A string like "a.c3;src/*.c3"
        """
        assert type(s) is str
        file_names = []
        for part in s.split(';'):
            new_files = glob.glob(self.relpath(part))
            if not new_files:
                raise TaskError('{} not found'.format(part))
            for filename in new_files:
                file_names.append(os.path.normpath(filename))
        return file_names

    def run(self):  # pragma: no cover
        """ Implement this method when creating a custom task """
        raise NotImplementedError("Implement this abstract method!")

    def __repr__(self):
        return 'Task "{}"'.format(self.name)


class TaskRunner:
    """ Basic task runner that can run some tasks in sequence """
    def __init__(self):
        self.logger = logging.getLogger('taskrunner')

    def get_task(self, name):
        """ Tries to load the task type """
        if name in task_map:
            return task_map[name]
        else:
            raise TaskError('Task "{}" could not be found'.format(name))

    def run(self, project, targets=[]):
        """ Try to run a project """
        # Determine what targets to run:
        if targets:
            target_list = targets
        else:
            if project.default:
                target_list = [project.default]
            else:
                target_list = []

        if not target_list:
            self.logger.info('No targets to run!')
            return

        # Check for loops:
        for target in target_list:
            project.check_target(target)

        # Calculate all dependencies:
        # TODO: make this understandable:
        target_list = set.union(
            *[project.dependencies(t) for t in target_list])\
            .union(set(target_list))

        # Lookup actual targets:
        target_list = [project.get_target(target_name)
                       for target_name in target_list]
        target_list.sort()

        self.logger.info('Target sequence: {}'.format(target_list))

        # Run tasks:
        for target in target_list:
            self.logger.info('Target {} Started'.format(target.name))
            for tname, props in target.tasks:
                for arg in props:
                    props[arg] = project.expand_macros(props[arg])
                task = self.get_task(tname)(target, props)
                self.logger.info('Running {}'.format(task))
                task.run()
            self.logger.info('Target {} Ready'.format(target.name))
        self.logger.info('All targets done!')
