
from qtwrapper import QtGui, QtCore, QtWidgets, pyqtSignal, get_icon
from qtwrapper import Qt
from ppci.binutils import debuginfo
from ppci.binutils.debuginfo import DebugBaseType


class VariableModel(QtCore.QAbstractItemModel):
    """ Model that contains a view on the current values of variables """
    def __init__(self, debugger):
        super().__init__()
        self.debugger = debugger
        self.debugger.state_event.subscribe(self.on_state_changed)
        print(self.debugger.obj)
        self.headers = ('Name', 'Value', 'Type')

    def on_state_changed(self):
        if self.debugger.is_halted:
            from_index = self.index(0, 1)
            variables = self.debugger.obj.debug_info.variables
            to_index = self.index(len(variables) - 1, 1)
            self.dataChanged.emit(from_index, to_index)

    def rowCount(self, parent):
        variables = self.debugger.obj.debug_info.variables
        if not parent.isValid():
            # Root level:
            return len(variables)
        node = parent.internalPointer()
        print(node)
        if isinstance(node, debuginfo.DebugVariable):
            pass
        return 0

    def columnCount(self, parent):
        if parent.isValid():
            return 0
        return len(self.headers)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        variables = self.debugger.obj.debug_info.variables
        if not parent.isValid():
            # Root stuff:
            var = variables[row]
            return self.createIndex(row, column, var)
        raise RuntimeError('Not possible!')

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        return QtCore.QModelIndex()

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]

    def data(self, index, role):
        if not index.isValid():
            return
        col = index.column()
        var = index.internalPointer()
        if role == Qt.DisplayRole:
            if col == 0:
                return var.name
            elif col == 1:
                # Get the value of the variable
                addr = self.debugger.calc_address(var.address)
                if isinstance(var.typ, DebugBaseType):
                    value = self.debugger.load_value(addr, var.typ)
                    return str(value)
                # print('get it', addr)
            elif col == 2:
                return str(var.typ)
            else:
                raise NotImplementedError()


class VariablesView(QtWidgets.QTreeView):
    """ A widgets displaying current values of variables """
    def __init__(self, debugger):
        super().__init__()
        model = VariableModel(debugger)
        self.setModel(model)
