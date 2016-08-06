from qtwrapper import QtCore, QtWidgets, Qt
from ppci.binutils.dbg import Debugger


class RegisterModel(QtCore.QAbstractTableModel):
    def __init__(self, debugger):
        super().__init__()
        self.debugger = debugger
        self._registers = self.debugger.registers
        self.debugger.state_event.subscribe(self.on_state_changed)
        self.headers = ('Register', 'Value')
        self.on_state_changed()

    def on_state_changed(self):
        if self.debugger.is_halted:
            from_index = self.index(0, 1)
            to_index = self.index(len(self._registers) - 1, 1)
            self.dataChanged.emit(from_index, to_index)

    def rowCount(self, parent):
        if parent.isValid():
            return 0
        return len(self._registers)

    def columnCount(self, parent):
        if parent.isValid():
            return 0
        return 2

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]

    def data(self, index, role):
        if index.isValid():
            row, col = index.row(), index.column()
            if role == Qt.DisplayRole:
                reg = self._registers[row]
                if col == 0:
                    return reg.name
                elif col == 1:
                    register_value = self.debugger.register_values[reg]
                    return '0x{0:X}'.format(register_value)

    def setData(self, index, value, role):
        if index.isValid():
            row = index.row()
            col = index.column()
            if role == Qt.EditRole and col == 1:
                value = int(value, 16)
                register = self._registers[row]
                self.debugger.set_register(register, value)
                return True
        return False

    def flags(self, index):
        if index.isValid():
            col = index.column()
            if col == 1:
                return super().flags(index) | Qt.ItemIsEditable
        return super().flags(index)


class RegisterView(QtWidgets.QTableView):
    def __init__(self, debugger):
        super().__init__()
        self.mdl = RegisterModel(debugger)
        self.setModel(self.mdl)
        self.debugger = debugger
        self.debugger.state_event.subscribe(self.update_state)
        self.update_state()
        self.horizontalHeader().setStretchLastSection(True)

    def update_state(self):
        running = self.debugger.is_running
        self.setEnabled(not running)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    rv = RegisterView(Debugger('arm', 0))
    rv.show()
    rv.resize(600, 800)
    app.exec()
