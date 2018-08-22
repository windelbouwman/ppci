""" Widget that provides raw gdb interaction.

Possible use cases:

- connect / disconnect
- send raw command over RSP

"""

from qtwrapper import QtWidgets


class GdbConsole(QtWidgets.QWidget):
    def __init__(self, qdebugger):
        super().__init__()
        self.qdebugger = qdebugger

        # Layout widgets:
        l = QtWidgets.QVBoxLayout(self)
        l2 = QtWidgets.QHBoxLayout()
        l2.addWidget(QtWidgets.QLabel('Raw GDB RSP command:'))
        self.gdb_command = QtWidgets.QLineEdit()
        l2.addWidget(self.gdb_command)
        l.addLayout(l2)

        # Hook up signals:
        self.gdb_command.returnPressed.connect(self.send_command)

    def send_command(self):
        command = self.gdb_command.text()
        self.qdebugger.debugger.driver.sendpkt(command)
        self.gdb_command.clear()
