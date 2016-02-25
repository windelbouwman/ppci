from qtwrapper import QtGui, QtCore, QtWidgets, pyqtSignal, get_icon


class RegisterModel(QtCore.QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.regCount = 15
        self.device = None

    def rowCount(self, parent):
        if parent.isValid():
         return 0
        if self.device:
         return 21 # TODO make variable
        else:
         return 0

    def setDevice(self, dev):
        self.device = dev
        self.modelReset.emit()

    def columnCount(self, parent):
        if parent.isValid():
         return 0
        return 2

    def data(self, index, role):
      if index.isValid():
         row, col = index.row(), index.column()
         if role == Qt.DisplayRole:
            if col == 0:
                if row == 15:
                    return 'PC'
                elif row == 14:
                    return 'LR'
                elif row == 13:
                    return 'SP'
                else:
                    return 'R{0}'.format(row)
            elif col == 1:
               v = self.device.iface.read_reg(row)
               return '0x{0:X}'.format(v)

    def setData(self, index, value, role):
      if index.isValid():
         row = index.row()
         col = index.column()
         if role == Qt.EditRole and col == 1:
            value = int(value, 16)
            self.device.iface.write_reg(row, value)
            return True
      return False

    def flags(self, index):
      if index.isValid():
         row = index.row()
         col = index.column()
         if col == 1:
            return super().flags(index) | Qt.ItemIsEditable
      return super().flags(index)

    def refresh(self):
        if self.device:
         fromIndex = self.index(0, 1)
         toIndex = self.index(21, 1)
         self.dataChanged.emit(fromIndex, toIndex)


class RegisterView(QtWidgets.QTableView):
    def __init__(self):
        super().__init__()
        self.mdl = RegisterModel()
        self.setModel(self.mdl)

    def refresh(self):
        if self.mdl.device:
         self.setEnabled(not self.mdl.device.Running)
        self.mdl.refresh()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    ce = RegisterView()
    ce.show()
    ce.resize(600, 800)
    app.exec()
