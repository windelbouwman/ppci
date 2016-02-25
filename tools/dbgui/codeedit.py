#!/usr/bin/python
""" Code editor """

import sys
import os
from qtwrapper import QtGui, QtCore, QtWidgets, pyqtSignal, Qt, get_icon
import inspect

GAP = 5


def clipVal(v, mn, mx):
    if v < mn:
        return mn
    if v > mx:
        return mx
    return v


class InnerCode(QtWidgets.QWidget):
    textChanged = pyqtSignal()

    def __init__(self, scrollArea):
        super().__init__(scrollArea)
        self.scrollArea = scrollArea
        self.setFont(QtGui.QFont('Courier', 12))
        self.setFocusPolicy(Qt.StrongFocus)
        # TODO: only beam cursor in text area..
        self.setCursor(Qt.IBeamCursor)
        h = QtGui.QFontMetrics(self.font()).height()
        self.errorPixmap = get_icon('error.png').scaled(h, h)
        self.arrowPixmap = get_icon('arrow.png').scaled(h, h)
        self.blinkcursor = False
        self.errorlist = []
        self.arrow = None
        # Initial values:
        self.setSource('')
        self.CursorPosition = 0
        self.t = QtCore.QTimer(self)
        self.t.timeout.connect(self.updateCursor)
        self.t.setInterval(500)
        self.t.start()

    def updateCursor(self):
        self.blinkcursor = not self.blinkcursor
        self.update()
        #self.update(self.cursorX, self.cursorY, self.charWidth, self.charHeight)

    def setSource(self, src):
        self.src = src
        self.adjust()

    def getSource(self):
        return self.src

    def setErrors(self, el):
        self.errorlist = el
        self.update()

    def setCursorPosition(self, c):
        self.cursorPosition = clipVal(c, 0, len(self.src))
        self.update()

    CursorPosition = property(lambda self: self.cursorPosition, setCursorPosition)

    @property
    def Rows(self):
        # Make this nicer:
        return self.src.split('\n')

    @property
    def CursorRow(self):
        # TODO: make this nice.
        txt = self.src[0:self.cursorPosition]
        return len(txt.split('\n'))

    @property
    def CursorCol(self):
        txt = self.src[0:self.cursorPosition]
        curLine = txt.split('\n')[-1]
        return len(curLine) + 1

    @property
    def CurrentLine(self):
        return self.getRow(self.CursorRow)

    def setRowCol(self, r, c):
        prevRows = self.Rows[:r-1]
        txt = '\n'.join(prevRows)
        c = clipVal(c, 1, len(self.getRow(r)))
        self.CursorPosition = len(txt) + c + 1
        self.showRow(self.CursorRow)

    def getRow(self, r):
        rows = self.Rows
        r = r - 1
        if r < 0 or r > len(rows) - 1:
            return ''
        else:
            return rows[r]

    def showRow(self, r):
        self.scrollArea.ensureVisible(self.xposTXT, r * self.charHeight, 4, self.charHeight)

    # Annotations:
    def addAnnotation(self, row, col, ln, msg):
        pass

    # Text modification:
    def getChar(self, pos):
        pass

    def insertText(self, txt):
        self.setSource(self.src[0:self.CursorPosition] + txt + self.src[self.CursorPosition:])
        self.CursorPosition += len(txt)
        self.textChanged.emit()

    def deleteChar(self):
        self.setSource(self.src[0:self.CursorPosition] + self.src[self.CursorPosition+1:])
        self.textChanged.emit()

    def GotoNextChar(self):
        if self.src[self.CursorPosition] != '\n':
            self.CursorPosition += 1

    def GotoPrevChar(self):
        if self.src[self.CursorPosition - 1] != '\n':
            self.CursorPosition -= 1

    def GotoNextLine(self):
        curLine = self.CurrentLine
        c = self.CursorCol - 1 # go to zero based
        self.CursorPosition += len(curLine) - c + 1 # line break char!
        curLine = self.CurrentLine
        if len(curLine) < c:
            self.CursorPosition += len(curLine)
        else:
            self.CursorPosition += c
        self.showRow(self.CursorRow)

    def GotoPrevLine(self):
        c = self.CursorCol - 1 # go to zero based
        self.CursorPosition -= c + 1 # line break char!
        curLine = self.CurrentLine
        if len(curLine) > c:
            self.CursorPosition -= len(curLine) - c
        self.showRow(self.CursorRow)

    def paintEvent(self, event):
        # Helper variables:
        er = event.rect()
        chw, chh = self.charWidth, self.charHeight
        painter = QtGui.QPainter(self)
        # Background:
        painter.fillRect(er, self.palette().color(QtGui.QPalette.Base))
        painter.fillRect(QtCore.QRect(self.xposLNA, er.top(), 4 * chw, er.bottom() + 1), Qt.gray)
        errorPen = QtGui.QPen(Qt.red, 3)
        # first and last row:
        row1 = max(int(er.top() / chh) - 1, 1)
        row2 = max(int(er.bottom() / chh) + 1, 1)
        # Draw contents:
        ypos = row1 * chh - self.charDescent
        curRow = self.CursorRow
        ydt = -chh + self.charDescent
        for row in range(row1, row2 + 1):
         if curRow == row and self.hasFocus():
            painter.fillRect(self.xposTXT, ypos + ydt, er.width(), chh, Qt.yellow)
            # cursor
            if self.blinkcursor:
               cursorX = self.CursorCol * self.charWidth + self.xposTXT - self.charWidth
               cursorY = ypos + ydt
               painter.fillRect(cursorX, cursorY, 2, chh, Qt.black)
         painter.setPen(Qt.black)
         painter.drawText(self.xposLNA, ypos, '{0}'.format(row))
         xpos = self.xposTXT
         painter.drawText(xpos, ypos, self.getRow(row))
         if self.arrow and self.arrow.row == row:
                painter.drawPixmap(self.xposERR, ypos + ydt, self.arrowPixmap)
         curErrors = [e for e in self.errorlist if e.loc and e.loc.row == row]
         for e in curErrors:
               painter.drawPixmap(self.xposERR, ypos + ydt, self.errorPixmap)
               painter.setPen(errorPen)
               x = self.xposTXT + (e.loc.col - 1) * chw - 2
               wt = e.loc.length * chw + 4
               dy = self.charDescent
               painter.drawLine(x, ypos + dy, x + wt, ypos + dy)
               #painter.drawRoundedRect(x, ypos + ydt, wt, chh, 7, 7)
               # print error balloon
               #painter.drawText(x, ypos + chh, e.msg)
         #if len(curErrors) > 0:
         #   ypos += chh
         ypos += chh

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.MoveToNextChar):
            self.GotoNextChar()
        elif event.matches(QtGui.QKeySequence.MoveToPreviousChar):
            self.GotoPrevChar()
        elif event.matches(QtGui.QKeySequence.MoveToNextLine):
            self.GotoNextLine()
        elif event.matches(QtGui.QKeySequence.MoveToPreviousLine):
            self.GotoPrevLine()
        elif event.matches(QtGui.QKeySequence.MoveToNextPage):
            for i in range(5):
                self.GotoNextLine()
        elif event.matches(QtGui.QKeySequence.MoveToPreviousPage):
            for i in range(5):
                self.GotoPrevLine()
        elif event.matches(QtGui.QKeySequence.MoveToEndOfLine):
            self.CursorPosition += len(self.CurrentLine) - self.CursorCol + 1
        elif event.matches(QtGui.QKeySequence.MoveToStartOfLine):
            self.CursorPosition -= self.CursorCol - 1
        elif event.matches(QtGui.QKeySequence.Delete):
            self.deleteChar()
        elif event.matches(QtGui.QKeySequence.InsertParagraphSeparator):
            self.insertText('\n')
        elif event.key() == Qt.Key_Backspace:
            self.CursorPosition -= 1
            self.deleteChar()
        else:
            char = event.text()
            if char:
                self.insertText(char)
        self.update()

    def mousePressEvent(self, event):
        pos = event.pos()
        if pos.x() > self.xposTXT and pos.x():
            c = round((pos.x() - self.xposTXT) / self.charWidth)
            r = int(pos.y() / self.charHeight) + 1
            self.setRowCol(r, c)
        super().mousePressEvent(event)

    def adjust(self):
        metrics = self.fontMetrics()
        self.charHeight = metrics.height()
        self.charWidth = metrics.width('x')
        self.charDescent = metrics.descent()
        self.xposERR = GAP
        self.xposLNA = self.xposERR + GAP + self.errorPixmap.width()
        self.xposTXT = self.xposLNA + 4 * self.charWidth + GAP
        self.xposEnd = self.xposTXT + self.charWidth * 80
        self.setMinimumWidth(self.xposEnd)
        txt = self.src.split('\n')
        self.setMinimumHeight(self.charHeight * len(txt))
        self.update()


class CodeEdit(QtWidgets.QScrollArea):
    def __init__(self):
        super().__init__()
        self.ic = InnerCode(self)
        self.textChanged = self.ic.textChanged
        self.setWidget(self.ic)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setFocusPolicy(Qt.NoFocus)
        self.showRow = self.ic.showRow
        self.setRowCol = self.ic.setRowCol
        self.FileName = None

    def get_source(self):
        return self.ic.getSource()

    Source = property(get_source, lambda s, v: s.ic.setSource(v))

    def setErrors(self, el):
        self.ic.setErrors(el)

    def setFocus(self):
        self.ic.setFocus()
        super().setFocus()

    def setFileName(self, fn):
        self.filename = fn
        if fn:
            fn = os.path.basename(fn)
        else:
            fn = 'Untitled'
        self.setWindowTitle(fn)

    def getFileName(self):
        return self.filename

    FileName = property(getFileName, setFileName)

    def save(self):
        if self.FileName:
            s = self.Source
            with open(self.FileName, 'w') as f:
                f.write(s)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ce = CodeEdit()
    ce.show()
    src = ''.join(inspect.getsourcelines(InnerCode)[0])
    ce.Source = src
    ce.resize(600, 800)
    app.exec()
