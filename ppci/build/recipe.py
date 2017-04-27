"""
    Module that can load a build definition from file.
"""

import os
import sys
import xml.dom.minidom

from .tasks import Project, Target


class RecipeLoader:
    """ Loads a recipe into a runner from a dictionary or file """
    def load_file(self, recipe_file):
        """ Loads a build configuration from file """
        assert hasattr(recipe_file, 'read')
        if hasattr(recipe_file, 'name'):
            recipe_filename = recipe_file.name
            recipe_dir = os.path.abspath(os.path.dirname(recipe_filename))
            # Allow loading of custom tasks:
            sys.path.insert(0, recipe_dir)
        else:
            recipe_dir = None

        # Load the recipe:
        dom = xml.dom.minidom.parse(recipe_file)
        project = self.load_project(dom)

        if recipe_dir:
            project.set_property('basedir', recipe_dir)
        return project

    def load_project(self, elem):
        """ Load a project from xml """
        elem = elem.getElementsByTagName("project")[0]
        name = elem.getAttribute('name')
        project = Project(name)
        if elem.hasAttribute('default'):
            project.default = elem.getAttribute('default')
        else:
            project.default = None

        # Load imports:
        for import_element in elem.getElementsByTagName("import"):
            name = import_element.getAttribute('name')
            __import__(name)

        # Load properties:
        for pe in elem.getElementsByTagName("property"):
            name = pe.getAttribute('name')
            value = pe.getAttribute('value')
            project.set_property(name, value)

        # Load targets:
        for te in elem.getElementsByTagName("target"):
            name = te.getAttribute('name')
            target = Target(name, project)
            if te.hasAttribute('depends'):
                dependencies = te.getAttribute('depends').split(',')
                for dep in dependencies:
                    target.add_dependency(dep)
            # print(name)
            project.add_target(target)
            for cn in te.childNodes:
                if type(cn) is xml.dom.minidom.Element:
                    task_name = cn.tagName
                    task_props = {}
                    for i in range(cn.attributes.length):
                        atr = cn.attributes.item(i)
                        task_props[atr.name] = atr.value
                    target.add_task((task_name, task_props))
        return project
