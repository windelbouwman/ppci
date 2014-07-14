#!/usr/bin/python3

import os
import xml.dom.minidom

from .tasks import Project, Target


class RecipeLoader:
    """ Loads a recipe into a runner from a dictionary or file """
    def load_file(self, recipe_file):
        """ Loads a build configuration from file """
        recipe_dir = os.path.abspath(os.path.dirname(recipe_file))
        dom = xml.dom.minidom.parse(recipe_file)
        project = self.load_project(dom)
        project.set_property('basedir', recipe_dir)
        return project

    def load_project(self, elem):
        elem = elem.getElementsByTagName("project")[0]
        name = elem.getAttribute('name')
        project = Project(name)
        if elem.hasAttribute('default'):
            project.default = elem.getAttribute('default')
        else:
            project.default = None

        for pe in elem.getElementsByTagName("property"):
            name = pe.getAttribute('name')
            value = pe.getAttribute('value')
            project.set_property(name, value)
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
                # print(cn, type(cn))
                if type(cn) is xml.dom.minidom.Element:
                    task_name = cn.tagName
                    task_props = {}
                    for i in range(cn.attributes.length):
                        atr = cn.attributes.item(i)
                        #print(atr, atr.name, atr.value)
                        task_props[atr.name] = atr.value
                    target.add_task((task_name, task_props))
        return project

