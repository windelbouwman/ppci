from qtwrapper import QtGui, QtCore, QtWidgets, pyqtSignal, get_icon


class DebugToolbar(QtWidgets.QToolBar):
    statusChange = pyqtSignal()
    codePosition = pyqtSignal(int)

    def __init__(self, debugger):
        super().__init__()
        self.debugger = debugger
        # generate actions:
        def genAction(name, callback):
            a = QtWidgets.QAction(name, self)
            a.triggered.connect(callback)
            self.addAction(a)
            return a
        self.stepAction = genAction('Step', self.doStep)
        self.runAction = genAction('Run', self.doRun)
        self.stopAction = genAction('Stop', self.doHalt)
        self.resetAction = genAction('Reset', self.doReset)
        self.enableTraceAction = genAction('Enable trace', self.doEnableTrace)
        self.updateEnables()

    def updateEnables(self):
        if self.debugger.is_connected:
            self.resetAction.setEnabled(True)
            self.enableTraceAction.setEnabled(True)
            self.runAction.setEnabled(not self.device.Running)
            self.stepAction.setEnabled(not self.device.Running)
            self.stopAction.setEnabled(self.device.Running)
            self.statusChange.emit()
            if not self.device.Running:
                PC = 15
                v = self.device.iface.read_reg(PC)
                self.codePosition.emit(v)
        else:
            self.resetAction.setEnabled(False)
            self.enableTraceAction.setEnabled(False)
            self.runAction.setEnabled(False)
            self.stepAction.setEnabled(False)
            self.stopAction.setEnabled(False)

    def doStep(self):
        self.device.iface.step()
        self.updateEnables()

    def doReset(self):
        self.device.iface.reset()
        self.updateEnables()

    def doRun(self):
        self.debugger.run()
        self.updateEnables()

    def doHalt(self):
        self.debugger.stop()
        self.updateEnables()

    def doEnableTrace(self):
        self.device.iface.traceEnable()
        self.updateEnables()
