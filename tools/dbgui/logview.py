#!/usr/bin/python

"""
    A widget to log a python logger.
"""

import sys
import logging
import datetime

from qtwrapper import QtCore, QtWidgets, Qt


def formatTime(t):
    t2 = datetime.datetime.fromtimestamp(t)
    return t2.strftime('%H:%M:%S')


class LogModel(QtCore.QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.entries = []
        self.headers = ['Time', 'Level', 'Logger', 'Message']
        self.txts = []
        self.txts.append(lambda e: str(formatTime(e.created)))
        self.txts.append(lambda e: str(e.levelname))
        self.txts.append(lambda e: str(e.name))
        self.txts.append(lambda e: str(e.msg))

    def rowCount(self, parent):
        return len(self.entries)

    def columnCount(self, parent):
        return len(self.headers)

    def data(self, index, role):
        if not index.isValid():
            return
        row, col = index.row(), index.column()
        if role == Qt.DisplayRole:
            le = self.entries[row]
            return self.txts[col](le)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]

    def newLog(self, x):
        self.entries.append(x)
        self.modelReset.emit()


class LogView(QtWidgets.QWidget):
    """ Log view component """
    def __init__(self, parent=None):
        super().__init__(parent)
        l = QtWidgets.QVBoxLayout(self)
        self.tv = QtWidgets.QTableView(self)
        self.tv.horizontalHeader().setStretchLastSection(True)
        l.addWidget(self.tv)
        self.lm = LogModel()
        self.tv.setModel(self.lm)

        class MyHandler(logging.Handler):
            def emit(self2, x):
                self.lm.newLog(x)
                self.tv.scrollToBottom()
                for i in range(3):
                    self.tv.resizeColumnToContents(i)

        logging.getLogger().addHandler(MyHandler())


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    lv = LogView()
    lv.show()
    lv.resize(600, 200)
    logging.error('Error!!!')
    logging.warn('Warn here!')
    app.exec_()
