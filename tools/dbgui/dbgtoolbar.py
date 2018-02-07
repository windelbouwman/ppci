from qtwrapper import QtWidgets, Qt


class DebugToolbar(QtWidgets.QToolBar):
    def __init__(self, qdebugger):
        super().__init__()
        self.qdebugger = qdebugger

        def genAction(name, callback, shortcut=None):
            a = QtWidgets.QAction(name, self)
            a.triggered.connect(callback)
            if shortcut:
                a.setShortcut(shortcut)
            self.addAction(a)
            return a

        self.runAction = genAction('Run', self.qdebugger.run, Qt.Key_F5)
        self.stopAction = genAction('Stop', self.qdebugger.stop)
        self.stepAction = genAction('Step', self.qdebugger.step, Qt.Key_F10)
        self.resetAction = genAction('Reset', self.doReset)

        # Attach signals:
        self.qdebugger.halted.connect(self.runAction.setEnabled)
        self.qdebugger.halted.connect(self.stepAction.setEnabled)
        self.qdebugger.started.connect(self.updateEnables)
        self.qdebugger.stopped.connect(self.updateEnables)
        self.updateEnables()

    def updateEnables(self):
        self.resetAction.setEnabled(True)
        running = self.qdebugger.debugger.is_running
        self.stopAction.setEnabled(running)

    def doReset(self):
        self.qdebugger.debugger.restart()
        self.updateEnables()
