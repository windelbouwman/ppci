from qtwrapper import QtWidgets


class DebugToolbar(QtWidgets.QToolBar):
    def __init__(self, debugger):
        super().__init__()
        self.debugger = debugger
        self.debugger.connection_event.subscribe(self.onConnection)

        def genAction(name, callback):
            a = QtWidgets.QAction(name, self)
            a.triggered.connect(callback)
            self.addAction(a)
            return a
        self.runAction = genAction('Run', self.doRun)
        self.stopAction = genAction('Stop', self.doStop)
        self.stepAction = genAction('Step', self.doStep)
        self.resetAction = genAction('Reset', self.doReset)
        self.updateEnables()

    def onConnection(self):
        self.updateEnables()

    def updateEnables(self):
        if self.debugger.is_connected:
            self.resetAction.setEnabled(True)
            running = self.debugger.is_running
            self.runAction.setEnabled(not running)
            self.stepAction.setEnabled(not running)
            self.stopAction.setEnabled(running)
        else:
            self.resetAction.setEnabled(False)
            self.runAction.setEnabled(False)
            self.stepAction.setEnabled(False)
            self.stopAction.setEnabled(False)

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
        # self.device.iface.reset()
        # TODO!
        self.updateEnables()
