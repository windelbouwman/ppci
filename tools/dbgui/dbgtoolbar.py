from qtwrapper import QtWidgets, Qt


class DebugToolbar(QtWidgets.QToolBar):
    def __init__(self, debugger):
        super().__init__()
        self.debugger = debugger

        def genAction(name, callback, shortcut=None):
            a = QtWidgets.QAction(name, self)
            a.triggered.connect(callback)
            if shortcut:
                a.setShortcut(shortcut)
            self.addAction(a)
            return a
        self.runAction = genAction('Run', self.doRun, Qt.Key_F5)
        self.stopAction = genAction('Stop', self.doStop)
        self.stepAction = genAction('Step', self.doStep, Qt.Key_F10)
        self.resetAction = genAction('Reset', self.doReset)
        self.updateEnables()

    def updateEnables(self):
        self.resetAction.setEnabled(True)
        running = self.debugger.is_running
        self.runAction.setEnabled(not running)
        self.stepAction.setEnabled(not running)
        self.stopAction.setEnabled(running)

    def doRun(self):
        self.debugger.run()
        self.updateEnables()

    def doStop(self):
        self.debugger.stop()
        self.updateEnables()

    def doStep(self):
        self.debugger.step()
        self.updateEnables()

    def doReset(self):
        self.debugger.restart()
        self.updateEnables()
