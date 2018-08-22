
import logging
from qtwrapper import QtCore, QtWidgets
from qtwrapper import Qt
from ppci.binutils.debuginfo import DebugBaseType, DebugArrayType
from ppci.binutils.debuginfo import DebugStructType, DebugPointerType


class PartialVariable:
    def __init__(self, name, typ, address, row, parent):
        self.name = name
        self.typ = typ
        self.address = address
        self.row = row
        self.parent = parent
        self._children = None

    def __repr__(self):
        return '{} @ 0x{:016X}'.format(self.name, self.address)

    @property
    def children(self):
        if self._children is None:
            self._children = []
            if isinstance(self.typ, DebugBaseType):
                pass
            elif isinstance(self.typ, DebugArrayType):
                for row in range(self.typ.size):
                    name = '[{}]'.format(row)
                    offset = row * self.typ.element_type.sizeof()
                    addr = self.address + offset
                    pv = PartialVariable(
                        name, self.typ.element_type, addr, row, self)
                    self._children.append(pv)
            elif isinstance(self.typ, DebugStructType):
                for row, field in enumerate(self.typ.fields):
                    name = '{}'.format(field.name)
                    addr = self.address + field.offset
                    pv = PartialVariable(name, field.typ, addr, row, self)
                    self._children.append(pv)
            elif isinstance(self.typ, DebugPointerType):
                name = '*{}'.format(self.name)
                typ = self.typ.pointed_type
                addr = 0  # TODO load self.address
                pv = PartialVariable(name, typ, addr, 0, self)
                self._children.append(pv)
            else:
                raise NotImplementedError(str(self.typ))
        return self._children

    def refresh(self, debugger):
        pass


class VariableModel(QtCore.QAbstractItemModel):
    """ Model that contains a view on the current values of variables """
    def __init__(self, qdebugger, roots):
        super().__init__()
        self.qdebugger = qdebugger
        self.qdebugger.stopped.connect(self.on_stopped)
        self.headers = ('Name', 'Value', 'Type', 'Address')
        self.roots = roots
        self._value_cache = {}

    def on_stopped(self):
        # Clear any cached values when target has stopped
        self._value_cache.clear()
        if len(self.roots) > 0:
            from_index = self.index(0, 1)
            to_index = self.index(len(self.roots) - 1, 1)
            self.dataChanged.emit(from_index, to_index)

    def load_value(self, address, typ):
        """ Load a value from memory, and cache the result """
        key = (address, typ)
        if key in self._value_cache:
            value = self._value_cache[key]
        else:
            value = self.qdebugger.debugger.load_value(address, typ)
            self._value_cache[key] = value
        return value

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]

    def rowCount(self, parent):
        if parent.isValid():
            # Child node
            node = parent.internalPointer()
            return len(node.children)
        else:
            # Root level:
            return len(self.roots)

    def columnCount(self, parent):
        return len(self.headers)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if parent.isValid():
            ppv = parent.internalPointer()
            pv = ppv.children[row]
            return self.createIndex(row, column, pv)
        else:
            # Root stuff:
            pv = self.roots[row]
            return self.createIndex(row, column, pv)

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        pv = index.internalPointer()
        if pv.parent is None:
            return QtCore.QModelIndex()
        return self.createIndex(pv.parent.row, 0, pv.parent)

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
                if isinstance(var.typ, DebugBaseType):
                    value = self.load_value(var.address, var.typ)
                    return str(value)
                elif isinstance(var.typ, DebugPointerType):
                    ptr = self.load_value(var.address, var.typ)
                    var.children[0].address = ptr
                    value = ptr
                # print('get it', addr)
            elif col == 2:
                return str(var.typ)
            elif col == 3:
                return '0x{:X}'.format(var.address)
            else:
                raise NotImplementedError()


def calc_roots(debugger, variables):
    roots = []
    for row, var in enumerate(variables):
        addr = debugger.calc_address(var.address)
        pv = PartialVariable(var.name, var.typ, addr, row, None)
        roots.append(pv)
    return roots


class VariablesView(QtWidgets.QTreeView):
    """ A widgets displaying current values of variables """
    def __init__(self, debugger):
        super().__init__()
        roots = calc_roots(debugger.debugger, debugger.debugger.obj.debug_info.variables)
        model = VariableModel(debugger, roots)
        self.setModel(model)


class LocalsView(QtWidgets.QTreeView):
    """ A widgets displaying current values of locals """
    def __init__(self, debugger):
        super().__init__()
        self._cur_func = None
        self.qdebugger = debugger
        self.qdebugger.stopped.connect(self.on_stopped)
        #model = VariableModel(debugger)
        #self.setModel(model)
        # TODO!

    def on_stopped(self):
        cur_func = self.qdebugger.debugger.current_function()
        self.set_current_function(cur_func)

    def set_current_function(self, cur_func):
        # if cur_func != self._cur_func:
        self._cur_func = cur_func
        if cur_func:
                logging.debug('Now in %s', cur_func)
                self.set_new_model(cur_func)

    def set_new_model(self, cur_func):
        roots = calc_roots(self.qdebugger.debugger, cur_func.variables)
        model = VariableModel(self.qdebugger, roots)
        self.setModel(model)
        # TODO: cleanup old model?
