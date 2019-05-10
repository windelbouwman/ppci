""" Methods to load classes easily.
"""

import os
from .jarfile import JarFile


class ClassLoader:
    def __init__(self):
        self.class_paths = []
        self.add_class_path("/usr/lib/jvm/default/jre/lib/rt.jar")

    def add_class_path(self, path):
        """ Add a jar or directory to the class path. """
        self.class_paths.append(path)

    def load(self, name):
        # Start search!
        for class_path in self.class_paths:
            if os.path.isdir(class_path):
                pass
            elif os.path.isfile(class_path):
                pass
            else:
                pass
