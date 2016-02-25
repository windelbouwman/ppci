#!/usr/bin/python

"""
    Debug user interface for debugging.
"""

import sys
import os
import logging

from qtwrapper import QtGui, QtCore, QtWidgets, pyqtSignal, get_icon
from qtwrapper import abspath, Qt

import ppci.api
import ppci.common
from ppci.dbg import Debugger

from codeedit import CodeEdit
from logview import LogView as BuildOutput
from regview import RegisterView
from memview import MemoryView
from dbgtoolbar import DebugToolbar
from connectiontoolbar import ConnectionToolbar


class BuildErrors(QtWidgets.QTreeView):
    sigErrorSelected = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        model = QtGui.QStandardItemModel()
        self.setModel(model)
        self.clicked.connect(self.itemSelected)
        self.errorIcon = get_icon('error.png')
        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Message', 'Row', 'Column'])
        self.header().setStretchLastSection(True)
        self.setModel(self.model)

    def setErrorList(self, errorlist):
        c = self.model.rowCount()
        self.model.removeRows(0, c)
        for e in errorlist:
            item = QtGui.QStandardItem(self.errorIcon, str(e.msg))
            item.setData(e)
            row = str(e.loc.row) if e.loc else ''
            irow = QtGui.QStandardItem(row)
            irow.setData(e)
            col = str(e.loc.col) if e.loc else ''
            icol = QtGui.QStandardItem(col)
            icol.setData(e)
            self.model.appendRow([item, irow, icol])
        for i in range(3):
            self.resizeColumnToContents(i)

    def itemSelected(self, index):
        if not index.isValid():
            return
        item = self.model.itemFromIndex(index)
        err = item.data()
        self.sigErrorSelected.emit(err)


class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('About')
        l = QtWidgets.QVBoxLayout(self)
        txt = QtWidgets.QTextEdit(self)
        txt.setReadOnly(True)
        with open(abspath(os.path.join('..', '..', 'readme.rst')), 'r') as f:
            aboutText = f.read()
        txt.append(aboutText)
        l.addWidget(txt)
        but = QtWidgets.QPushButton('OK')
        but.setDefault(True)
        but.clicked.connect(self.close)
        l.addWidget(but)


class Ide(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(Ide, self).__init__(parent)
        self.to_open_files = []
        self.logger = logging.getLogger('ide')
        self.debugger = Debugger()

        self.setWindowTitle('LCFOS IDE')

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
        #self.astViewer = addComponent('AST viewer', AstViewer())
        #self.astViewer.sigNodeSelected.connect(lambda node: self.showLoc(node.loc))
        self.builderrors = addComponent('Build errors', BuildErrors())
        self.builderrors.sigErrorSelected.connect(lambda err: self.showLoc(err.loc))
        # self.devxplr = addComponent('Device explorer', stutil.DeviceExplorer())
        self.regview = addComponent('Registers', RegisterView())
        self.memview = addComponent('Memory', MemoryView())
        #self.disasm = addComponent('Disasm', Disassembly())
        self.connectionToolbar = ConnectionToolbar(self.debugger)
        self.addToolBar(self.connectionToolbar)
        self.ctrlToolbar = DebugToolbar(self.debugger)
        self.addToolBar(self.ctrlToolbar)
        #self.ctrlToolbar.setObjectName('debugToolbar')
        #self.devxplr.deviceSelected.connect(self.regview.mdl.setDevice)
        #self.ctrlToolbar.statusChange.connect(self.memview.refresh)
        #self.devxplr.deviceSelected.connect(self.memview.setDevice)
        #self.devxplr.deviceSelected.connect(self.ctrlToolbar.setDevice)
        #self.ctrlToolbar.statusChange.connect(self.regview.refresh)
        #self.ctrlToolbar.codePosition.connect(self.pointCode)

        # About dialog:
        self.aboutDialog = AboutDialog()

        # Create actions:
        def addMenuEntry(name, menu, callback, shortcut=None):
            a = QtWidgets.QAction(name, self)
            menu.addAction(a)
            a.triggered.connect(callback)
            if shortcut:
                a.setShortcut(QtGui.QKeySequence(shortcut))

        addMenuEntry("New", self.fileMenu, self.newFile, shortcut=QtGui.QKeySequence.New)
        addMenuEntry("Open", self.fileMenu, self.openFile, shortcut=QtGui.QKeySequence.Open)
        addMenuEntry("Save", self.fileMenu, self.saveFile, shortcut=QtGui.QKeySequence.Save)
        # addMenuEntry("Build", self.fileMenu, self.buildFile, shortcut="F7")
        # addMenuEntry("Build and flash", self.fileMenu, self.buildFileAndFlash, shortcut="F8")

        self.helpAction = QtWidgets.QAction('Help', self)
        self.helpAction.setShortcut(QtGui.QKeySequence('F1'))
        self.helpMenu.addAction(self.helpAction)
        addMenuEntry('About', self.helpMenu, self.aboutDialog.open)

        addMenuEntry('Cascade windows', self.viewMenu, self.mdiArea.cascadeSubWindows)
        addMenuEntry('Tile windows', self.viewMenu, self.mdiArea.tileSubWindows)
        sb = self.statusBar()

        # Load settings:
        self.settings = QtCore.QSettings('windelsoft', 'lcfoside')
        self.loadSettings()
        #self.diag = ppci.DiagnosticsManager()

    # File handling:
    def newFile(self):
        self.newCodeEdit()

    def openFile(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "Open C3 file...", "*.c3",
                    "C3 source files (*.c3)")
        if filename:
            self.loadFile(filename[0])

    def saveFile(self):
        ac = self.activeMdiChild()
        if ac:
            ac.save()

    def loadFile(self, filename):
        ce = self.newCodeEdit()
        try:
            with open(filename) as f:
                ce.Source = f.read()
                ce.FileName = filename
        except Exception as e:
            print('exception opening file:', e)

    # MDI:
    def newCodeEdit(self):
        ce = CodeEdit()
        ce.textChanged.connect(self.parseFile)
        w = self.mdiArea.addSubWindow(ce)
        self.mdiArea.setActiveSubWindow(w)
        ce.showMaximized()
        return ce

    def activeMdiChild(self):
        aw = self.mdiArea.activeSubWindow()
        if aw:
            return aw.widget()

    def findMdiChild(self, filename):
        for wid in self.allChildren():
            if wid.filename == filename:
                return wid

    def allChildren(self):
        return [w.widget() for w in self.mdiArea.subWindowList()]

    # Settings:
    def loadSettings(self):
        if self.settings.contains('mainwindowstate'):
            self.restoreState(self.settings.value('mainwindowstate'))
        if self.settings.contains('mainwindowgeometry'):
            self.restoreGeometry(self.settings.value('mainwindowgeometry'))
        if self.settings.contains('lastfiles'):
            lfs = self.settings.value('lastfiles')
            if lfs:
                self.to_open_files.extend(lfs)

    def showEvent(self, ev):
        super().showEvent(ev)
        while self.to_open_files:
            fn = self.to_open_files.pop(0)
            self.loadFile(fn)

    def closeEvent(self, ev):
        self.settings.setValue('mainwindowstate', self.saveState())
        self.settings.setValue('mainwindowgeometry', self.saveGeometry())
        ac = self.activeMdiChild()
        lfs = [ce.FileName for ce in self.allChildren() if ce.FileName]
        self.settings.setValue('lastfiles', lfs)
        ev.accept()

    # Error handling:
    def nodeSelected(self, node):
        self.showLoc(node.loc)

    def showLoc(self, loc):
        ce = self.activeMdiChild()
        if not ce:
            return
        if loc:
            ce.setRowCol(loc.row, loc.col)
            ce.setFocus()

    def pointCode(self, p):
        # Lookup pc in debug infos:
        loc = None
        print(p)
        self.disasm.showPos(p)
        if hasattr(self, 'debugInfo'):
            for di in self.debugInfo:
                if di.address > p:
                    loc = di.info
                    break
        if loc:
            ce = self.activeMdiChild()
            if ce:
                ce.ic.arrow = loc
            self.showLoc(loc)

    # Build recepy:
    def parseFile(self):
        self.logger.info('Parsing!')

    def doBuild(self):
        ce = self.activeMdiChild()
        if not ce:
            return
        fn = ce.FileName
        self.diag.clear()
        outs = BinaryOutputStream()
        imps = [open(ce.FileName, 'r') for ce in self.allChildren() if ce.FileName and ce.FileName != fn]
        if not zcc.zcc([open(fn, 'r')], imps, thumb_target, outs, self.diag):
            # Set errors:
            self.builderrors.setErrorList(self.diag.diags)
            ce.setErrors(self.diag.diags)
            return
        return outs

    def buildFile(self):
        self.doBuild()

    def buildFileAndFlash(self):
        outs = self.doBuild()
        if not outs:
            return

        code_s = outs.getSection('code')
        self.disasm.dm.setInstructions(code_s.instructions)
        self.debugInfo = code_s.debugInfos()
        if self.ctrlToolbar.device:
            logging.info('Flashing stm32f4 discovery')
            bts = code_s.to_bytes()
            self.ctrlToolbar.device.writeFlash(0x08000000, bts)
            stl = self.ctrlToolbar.device.iface
            stl.reset()
            stl.halt()
            stl.run()
            logging.info('Done!')
        else:
            self.logger.warning('Not connected to device, skipping flash')


if __name__ == '__main__':
    logging.basicConfig(format=ppci.common.logformat, level=logging.DEBUG)
    app = QtWidgets.QApplication(sys.argv)
    ide = Ide()
    ide.show()
    ide.logger.info('IDE started')
    app.exec_()
