import os
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import pyqtSignal, Qt


def abspath(filename):
    script_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(script_path, filename)


def get_icon(filename):
    return QtGui.QPixmap(abspath(os.path.join('icons', filename)))
