#!/usr/bin/python

import sys
from qtwrapper import QtGui, QtCore, QtWidgets, Qt, abspath, uic


BYTES_PER_LINE, GAP = 8, 12


def clamp(minimum, x, maximum):
    return max(minimum, min(x, maximum))


def asciiChar(v):
    if v < 0x20 or v > 0x7e:
        return '.'
    else:
        return chr(v)


class BinViewer(QtWidgets.QWidget):
    """ The view has an address, hex byte and ascii column """
    def __init__(self, scrollArea):
        super().__init__(scrollArea)
        self.scrollArea = scrollArea
        self.setFont(QtGui.QFont('Courier', 16))
        self.setFocusPolicy(Qt.StrongFocus)
        self.blinkcursor = False
        self.cursorX = self.cursorY = 0
        self.scrollArea = scrollArea
        self.data = bytearray()
        self.originalData = bytearray()
        self.Data = bytearray()
        self.Offset = 0
        t = QtCore.QTimer(self)
        t.timeout.connect(self.updateCursor)
        t.setInterval(500)
        t.start()

    def updateCursor(self):
        self.blinkcursor = not self.blinkcursor
        self.update(
            self.cursorX, self.cursorY, self.charWidth, self.charHeight)

    def setCursorPosition(self, position):
        position = clamp(0, int(position), len(self.Data) * 2 - 1)
        self.cursorPosition = position
        x = position % (2 * BYTES_PER_LINE)
        x = x + int(x / 2)  # Create a gap between hex values
        self.cursorX = self.xposHex + x * self.charWidth
        y = int(position / (2 * BYTES_PER_LINE))
        self.cursorY = y * self.charHeight + 2
        self.blinkcursor = True
        self.update()

    def getCursorPosition(self):
        return self.cursorPosition

    CursorPosition = property(getCursorPosition, setCursorPosition)

    def setOffset(self, off):
        self.offset = off
        self.update()

    Offset = property(lambda self: self.offset, setOffset)

    def paintEvent(self, event):
        # Helper variables:
        er = event.rect()
        chw, chh = self.charWidth, self.charHeight
        painter = QtGui.QPainter(self)

        # Background:
        painter.fillRect(er, self.palette().color(QtGui.QPalette.Base))
        painter.fillRect(
            QtCore.QRect(
                self.xposAddr, er.top(), 8 * chw, er.bottom() + 1), Qt.gray)
        painter.setPen(Qt.gray)
        x = self.xposAscii - (GAP / 2)
        painter.drawLine(x, er.top(), x, er.bottom())
        x = self.xposEnd - (GAP / 2)
        painter.drawLine(x, er.top(), x, er.bottom())

        # first and last index
        firstIndex = max((int(er.top() / chh) - chh) * BYTES_PER_LINE, 0)
        lastIndex = max((int(er.bottom() / chh) + chh) * BYTES_PER_LINE, 0)
        yposStart = int(firstIndex / BYTES_PER_LINE) * chh + chh

        # Draw contents:
        painter.setPen(Qt.black)
        ypos = yposStart
        for index in range(firstIndex, lastIndex, BYTES_PER_LINE):
            painter.setPen(Qt.black)
            painter.drawText(
                self.xposAddr, ypos, '{0:08X}'.format(index + self.Offset))
            xpos = self.xposHex
            xposAscii = self.xposAscii
            for colIndex in range(BYTES_PER_LINE):
                if index + colIndex < len(self.Data):
                    b = self.Data[index + colIndex]
                    bo = self.originalData[index + colIndex]
                    pen_color = Qt.black if b == bo else Qt.red
                    painter.setPen(pen_color)
                    painter.drawText(xpos, ypos, '{0:02X}'.format(b))
                    painter.drawText(xposAscii, ypos, asciiChar(b))
                    xpos += 3 * chw
                    xposAscii += chw
            ypos += chh

        # cursor
        if self.blinkcursor:
            painter.fillRect(
                self.cursorX, self.cursorY + chh - 2, chw, 2, Qt.black)

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.MoveToNextChar):
            self.CursorPosition += 1
        if event.matches(QtGui.QKeySequence.MoveToPreviousChar):
            self.CursorPosition -= 1
        if event.matches(QtGui.QKeySequence.MoveToNextLine):
            self.CursorPosition += 2 * BYTES_PER_LINE
        if event.matches(QtGui.QKeySequence.MoveToPreviousLine):
            self.CursorPosition -= 2 * BYTES_PER_LINE
        if event.matches(QtGui.QKeySequence.MoveToNextPage):
            rows = int(self.scrollArea.viewport().height() / self.charHeight)
            self.CursorPosition += (rows - 1) * 2 * BYTES_PER_LINE
        if event.matches(QtGui.QKeySequence.MoveToPreviousPage):
            rows = int(self.scrollArea.viewport().height() / self.charHeight)
            self.CursorPosition -= (rows - 1) * 2 * BYTES_PER_LINE
        char = event.text().lower()
        if char and char in '0123456789abcdef':
            i = int(self.CursorPosition / 2)
            hb = self.CursorPosition % 2
            v = int(char, 16)
            if hb == 0:
                # high half byte
                self.data[i] = (self.data[i] & 0xF) | (v << 4)
            else:
                self.data[i] = (self.data[i] & 0xF0) | v
            self.CursorPosition += 1
        self.scrollArea.ensureVisible(
            self.cursorX, self.cursorY + self.charHeight / 2,
            4, self.charHeight / 2 + 4)
        self.update()

    def setCursorPositionAt(self, pos):
        """ Calculate cursor position at a certain point """
        if pos.x() > self.xposHex and pos.x() < self.xposAscii:
            x = round((2 * (pos.x() - self.xposHex)) / (self.charWidth * 3))
            y = int(pos.y() / self.charHeight) * 2 * BYTES_PER_LINE
            self.setCursorPosition(x + y)

    def mousePressEvent(self, event):
        self.setCursorPositionAt(event.pos())

    def adjust(self):
        self.charHeight = self.fontMetrics().height()
        self.charWidth = self.fontMetrics().width('x')
        self.xposAddr = GAP
        self.xposHex = self.xposAddr + 8 * self.charWidth + GAP
        self.xposAscii = self.xposHex + (BYTES_PER_LINE * 3 - 1) * self.charWidth + GAP
        self.xposEnd = self.xposAscii + self.charWidth * BYTES_PER_LINE + GAP
        self.setMinimumWidth(self.xposEnd)
        if self.isVisible():
            sbw = self.scrollArea.verticalScrollBar().width()
            self.scrollArea.setMinimumWidth(self.xposEnd + sbw + 5)
        r = len(self.Data) % BYTES_PER_LINE
        r = 1 if r > 0 else 0
        self.setMinimumHeight((int(len(self.Data) / BYTES_PER_LINE) + r) * self.charHeight + 4)
        self.scrollArea.setMinimumHeight(self.charHeight * 8)
        self.update()

    def showEvent(self, e):
        self.adjust()
        super().showEvent(e)

    def set_data(self, d):
        self.originalData = self.data
        self.data = bytearray(d)
        while len(self.data) > len(self.originalData):
            self.originalData.append(0)
        self.adjust()
        self.setCursorPosition(0)

    Data = property(lambda self: self.data, set_data)


class HexEdit(QtWidgets.QScrollArea):
    def __init__(self):
        super().__init__()
        self.bv = BinViewer(self)
        self.setWidget(self.bv)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setFocusPolicy(Qt.NoFocus)


class HexEditor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(abspath('hexeditor.ui'), baseinstance=self)
        self.he = HexEdit()
        self.setCentralWidget(self.he)
        self.actionOpen.triggered.connect(self.doOpen)
        self.actionSave.triggered.connect(self.doSave)
        self.actionSaveAs.triggered.connect(self.doSaveAs)
        self.fileName = None
        self.updateControls()

    def updateControls(self):
        s = True if self.fileName else False
        self.actionSave.setEnabled(s)
        self.actionSaveAs.setEnabled(s)

    def doOpen(self):
      filename = QtWidgets.QFileDialog.getOpenFileName(self)
      if filename:
         with open(filename, 'rb') as f:
            self.he.bv.Data = f.read()
         self.fileName = filename
      self.updateControls()

    def doSave(self):
        self.updateControls()

    def doSaveAs(self):
        filename = QFileDialog.getSaveFileName(self)
        if filename:
            with open(filename, 'wb') as f:
                f.write(self.he.bv.Data)
            self.fileName = filename
        self.updateControls()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    he = HexEditor()
    he.show()
    #he.bv.Data = bytearray(range(100)) * 8 + b'x'
    app.exec()
