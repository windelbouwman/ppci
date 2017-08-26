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
        self.formatter = logging.Formatter()

    def rowCount(self, parent):
        return len(self.entries)

    def columnCount(self, parent):
        return len(self.headers)

    def data(self, index, role):
        if not index.isValid():
            return
        row, col = index.row(), index.column()
        if role == Qt.DisplayRole:
            return self.entries[row][col]

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]

    def new_log(self, record):
        txts = []
        txts.append(lambda e: str(formatTime(e.created)))
        txts.append(lambda e: str(e.levelname))
        txts.append(lambda e: str(e.name))
        txts.append(self.formatter.format)
        self.entries.append([txt(record) for txt in txts])
        self.modelReset.emit()


class MyHandler(logging.Handler):
    """ Custom log handler that appends log messages to logview """
    def __init__(self, tv, log_model):
        super().__init__()
        self.tv = tv
        self.log_model = log_model

    def emit(self, record):
        self.log_model.new_log(record)
        self.tv.scrollToBottom()
        for i in range(3):
            self.tv.resizeColumnToContents(i)


class LogView(QtWidgets.QWidget):
    """ Log view component """
    def __init__(self, parent=None):
        super().__init__(parent)
        l = QtWidgets.QVBoxLayout(self)
        self.tv = QtWidgets.QTableView(self)
        self.tv.horizontalHeader().setStretchLastSection(True)
        l.addWidget(self.tv)
        self.log_model = LogModel()
        self.tv.setModel(self.log_model)
        logging.getLogger().addHandler(MyHandler(self.tv, self.log_model))


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    lv = LogView()
    lv.show()
    lv.resize(600, 200)
    logging.error('Error!!!')
    logging.warn('Warn here!')
    logging.error('formatted output: %s %i', 'wow', 13)
    app.exec_()
