import binascii
from qtwrapper import QtGui, QtCore, QtWidgets, Qt


class DisAsmModel(QtCore.QAbstractTableModel):
    def __init__(self, debugger):
        super().__init__()
        self.debugger = debugger
        self.debugger.stopped.connect(self.on_stopped)
        self.instructions = []
        self.headers = ['Address', 'Bytes', 'Instruction']
        self.txts = []
        self.txts.append(lambda i: '0x{:08x}'.format(getattr(i, 'address', 0)))
        self.txts.append(lambda i: binascii.hexlify(i.encode()).decode('ascii'))
        self.txts.append(lambda i: str(i))
        # self.on_state_changed()

    def on_stopped(self):
        ins = self.debugger.debugger.get_disasm()
        self.instructions = ins
        self.modelReset.emit()

    def rowCount(self, parent):
        return len(self.instructions)

    def columnCount(self, parent):
        return len(self.headers)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]

    def data(self, index, role):
        if not index.isValid():
            return
        row, col = index.row(), index.column()
        if role == Qt.DisplayRole:
            i = self.instructions[row]
            return self.txts[col](i)


class Disassembly(QtWidgets.QTableView):
    def __init__(self, debugger):
        super().__init__()
        self.dm = DisAsmModel(debugger)
        self.setModel(self.dm)
        self.horizontalHeader().setStretchLastSection(True)

    def showPos(self, p):
        for i in self.dm.instructions:
            if i.address == p:
                row = self.dm.instructions.index(i)
                self.selectRow(row)
