from qtwrapper import QtWidgets


class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('About')
        l = QtWidgets.QVBoxLayout(self)
        txt = QtWidgets.QTextEdit(self)
        txt.setReadOnly(True)
        aboutText = "ppci debugger"
        txt.append(aboutText)
        l.addWidget(txt)
        but = QtWidgets.QPushButton('OK')
        but.setDefault(True)
        but.clicked.connect(self.close)
        l.addWidget(but)
