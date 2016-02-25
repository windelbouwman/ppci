import logging
from qtwrapper import QtGui, QtCore, QtWidgets, pyqtSignal


class ConnectionToolbar(QtWidgets.QToolBar):
    statusChange = pyqtSignal()

    def __init__(self, debugger):
        super().__init__()
        self.logger = logging.getLogger('ide')
        self.debugger = debugger
        self.urlEdit = QtWidgets.QLineEdit()
        self.urlEdit.setText('http://localhost:8079')
        self.addWidget(self.urlEdit)

        def genAction(name, callback):
            a = QtWidgets.QAction(name, self)
            a.triggered.connect(callback)
            self.addAction(a)
            return a
        self.connectAction = genAction('Connect', self.doConnect)
        self.disconnectAction = genAction('Disconnect', self.doDisconnect)
        self.updateButtonStates()

    def updateButtonStates(self):
        connected = self.debugger.is_connected
        self.connectAction.setEnabled(not connected)
        self.disconnectAction.setEnabled(connected)

    def doConnect(self):
        uri = self.urlEdit.text()
        self.logger.info('Connecting to %s', uri)
        self.debugger.connect(uri)
        self.updateButtonStates()

    def doDisconnect(self):
        self.debugger.disconnect()
        self.updateButtonStates()
