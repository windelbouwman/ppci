from qtwrapper import QtWidgets
from hexedit import HexEdit


class MemoryView(QtWidgets.QWidget):
    block_size = 0x100

    def __init__(self, debugger):
        super().__init__()
        self.debugger = debugger

        # Layout widgets:
        l = QtWidgets.QVBoxLayout(self)
        l2 = QtWidgets.QHBoxLayout()
        l2.addWidget(QtWidgets.QLabel('Address'))
        self.addressLine = QtWidgets.QLineEdit()
        self.addressLine.setInputMask('Hhhhhhhhhhhhhhhh')
        l2.addWidget(self.addressLine)
        upButton = QtWidgets.QPushButton('up')
        l2.addWidget(upButton)
        upButton.clicked.connect(self.do_up)
        downButton = QtWidgets.QPushButton('down')
        downButton.clicked.connect(self.do_down)
        l2.addWidget(downButton)
        l.addLayout(l2)

        self.hexEdit = HexEdit()
        self.address = 0x40200
        l.addWidget(self.hexEdit)
        self.addressLine.returnPressed.connect(self.refresh)

    def refresh(self):
        address = self.address
        if self.debugger.is_halted:
            data = self.debugger.read_mem(address, self.block_size)
            self.hexEdit.bv.Data = data
            self.hexEdit.bv.Offset = address

    def do_up(self):
        self.address -= self.block_size

    def do_down(self):
        self.address += self.block_size

    def get_address(self):
        txt = self.addressLine.text()
        return int(txt, 16)

    def set_address(self, address):
        self.addressLine.setText('{:016X}'.format(address))
        self.refresh()

    address = property(get_address, set_address)
