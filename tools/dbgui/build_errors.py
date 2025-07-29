from qtwrapper import QtGui, QtWidgets, pyqtSignal, get_icon


class BuildErrors(QtWidgets.QTreeView):
    sigErrorSelected = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        model = QtGui.QStandardItemModel()
        self.setModel(model)
        self.clicked.connect(self.itemSelected)
        self.errorIcon = get_icon("error.png")
        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Message", "Row", "Column"])
        self.header().setStretchLastSection(True)
        self.setModel(self.model)

    def setErrorList(self, errorlist):
        c = self.model.rowCount()
        self.model.removeRows(0, c)
        for e in errorlist:
            item = QtGui.QStandardItem(self.errorIcon, str(e.msg))
            item.setData(e)
            row = str(e.loc.row) if e.loc else ""
            irow = QtGui.QStandardItem(row)
            irow.setData(e)
            col = str(e.loc.col) if e.loc else ""
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
