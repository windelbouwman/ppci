#!/usr/bin/python

"""
    Debug user interface for debugging.
"""

import logging
from qtwrapper import QtGui, QtCore, QtWidgets
from qtwrapper import Qt
from codeedit import CodeEdit
from logview import LogView as BuildOutput
from regview import RegisterView
from memview import MemoryView
from varview import VariablesView, LocalsView
from disasm import Disassembly
from aboutdialog import AboutDialog
from build_errors import BuildErrors
from dbgtoolbar import DebugToolbar
from qdebugger import QDebugger
from gdbconsole import GdbConsole


class DebugUi(QtWidgets.QMainWindow):
    """ Provide a nice gui for this debugger """
    def __init__(self, debugger, parent=None):
        super().__init__(parent)
        self.qdebugger = QDebugger(debugger)
        self.qdebugger.stopped.connect(self.on_stopped)
        self.logger = logging.getLogger('dbgui')
        self.setWindowTitle('PPCI DBGUI')

        # Create menus:
        mb = self.menuBar()
        self.fileMenu = mb.addMenu('File')
        self.viewMenu = mb.addMenu('View')
        self.helpMenu = mb.addMenu('Help')

        # Create mdi area:
        self.mdiArea = QtWidgets.QMdiArea()
        self.mdiArea.setViewMode(QtWidgets.QMdiArea.TabbedView)
        self.mdiArea.setTabsClosable(True)
        self.mdiArea.setTabsMovable(True)
        self.setCentralWidget(self.mdiArea)

        # Create components:
        def addComponent(name, widget):
            dw = QtWidgets.QDockWidget(name)
            dw.setWidget(widget)
            dw.setObjectName(name)
            self.addDockWidget(Qt.RightDockWidgetArea, dw)
            self.viewMenu.addAction(dw.toggleViewAction())
            return widget

        self.buildOutput = addComponent('Build output', BuildOutput())
        self.builderrors = addComponent('Build errors', BuildErrors())
        self.regview = addComponent('Registers', RegisterView(self.qdebugger))
        self.memview = addComponent('Memory', MemoryView(self.qdebugger))
        self.disasm = addComponent('Disasm', Disassembly(self.qdebugger))
        self.variables = addComponent('Variables', VariablesView(self.qdebugger))
        self.locals = addComponent('Locals', LocalsView(self.qdebugger))
        self.gdb_console = addComponent('Gdb', GdbConsole(self.qdebugger))
        self.ctrlToolbar = DebugToolbar(self.qdebugger)
        self.addToolBar(self.ctrlToolbar)
        self.ctrlToolbar.setObjectName('debugToolbar')
        self.aboutDialog = AboutDialog()

        # Create actions:
        def addMenuEntry(name, menu, callback, shortcut=None):
            a = QtWidgets.QAction(name, self)
            menu.addAction(a)
            a.triggered.connect(callback)
            if shortcut:
                a.setShortcut(QtGui.QKeySequence(shortcut))

        addMenuEntry(
            "Open", self.fileMenu, self.openFile,
            shortcut=QtGui.QKeySequence.Open)

        self.helpAction = QtWidgets.QAction('Help', self)
        self.helpAction.setShortcut(QtGui.QKeySequence('F1'))
        self.helpMenu.addAction(self.helpAction)
        addMenuEntry('About', self.helpMenu, self.aboutDialog.open)

        addMenuEntry(
            'Cascade windows', self.viewMenu, self.mdiArea.cascadeSubWindows)
        addMenuEntry(
            'Tile windows', self.viewMenu, self.mdiArea.tileSubWindows)
        self.statusBar()

        # Load settings:
        self.settings = QtCore.QSettings('windelsoft', 'lcfoside')
        self.loadSettings()

    # File handling:
    def openFile(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open C3 file...", "*.c3",
            "C3 source files (*.c3)")
        if filename:
            self.load_file(filename[0])

    def load_file(self, filename):
        print(filename)
        ce = self.new_code_edit()
        try:
            with open(filename) as f:
                ce.Source = f.read()
                ce.FileName = filename
                possible_breakpoints = self.qdebugger.debugger.get_possible_breakpoints(
                    filename)
                ce.set_possible_breakpoints(possible_breakpoints)
            return ce
        except Exception as e:
            print('exception opening file:', e)

    # MDI:
    def new_code_edit(self):
        ce = CodeEdit()
        ce.breakpointChanged.connect(self.toggle_breakpoint)
        w = self.mdiArea.addSubWindow(ce)
        self.mdiArea.setActiveSubWindow(w)
        ce.showMaximized()
        return ce

    def activeMdiChild(self):
        aw = self.mdiArea.activeSubWindow()
        if aw:
            return aw.widget()

    def find_mdi_child(self, filename):
        for sub_window in self.mdiArea.subWindowList():
            wid = sub_window.widget()
            if wid.filename == filename:
                self.mdiArea.setActiveSubWindow(sub_window)
                return wid

    def open_all_source_files(self):
        """ Open all debugged source files """
        for location in self.qdebugger.debugger.debug_info.locations:
            filename = location.loc.filename
            if not self.find_mdi_child(filename):
                self.load_file(filename)

    # Settings:
    def loadSettings(self):
        if self.settings.contains('mainwindowstate'):
            self.restoreState(self.settings.value('mainwindowstate'))
        if self.settings.contains('mainwindowgeometry'):
            self.restoreGeometry(self.settings.value('mainwindowgeometry'))

    def closeEvent(self, ev):
        self.settings.setValue('mainwindowstate', self.saveState())
        self.settings.setValue('mainwindowgeometry', self.saveGeometry())

    def toggle_breakpoint(self, filename, row, state):
        if state:
            self.qdebugger.debugger.set_breakpoint(filename, row)
        else:
            self.qdebugger.debugger.clear_breakpoint(filename, row)

    # Error handling:
    def show_loc(self, filename, row, col):
        """ Show a location in some source file """
        # Activate, or load file:
        ce = self.find_mdi_child(filename)
        if not ce:
            ce = self.load_file(filename)
        if not ce:
            print('fail to load ', filename)
            return
        ce.set_current_row(row)
        ce.setFocus()

    def on_stopped(self):
        """ When the debugger is halted """
        res = self.qdebugger.debugger.find_pc()
        if res:
            filename, row = res
            self.show_loc(filename, row, 1)
