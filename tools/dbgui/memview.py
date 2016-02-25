from qtwrapper import QtWidgets
from hexedit import HexEdit


class MemoryView(QtWidgets.QWidget):
    BlockSize = 0x100

    def __init__(self):
        super().__init__()
        l = QtWidgets.QVBoxLayout(self)
        l2 = QtWidgets.QHBoxLayout()
        l2.addWidget(QtWidgets.QLabel('Address'))
        self.addressLine = QtWidgets.QLineEdit()
        self.addressLine.setInputMask('Hhhhhhhh')
        l2.addWidget(self.addressLine)
        upButton = QtWidgets.QPushButton('up')
        l2.addWidget(upButton)
        upButton.clicked.connect(self.doUp)
        downButton = QtWidgets.QPushButton('down')
        downButton.clicked.connect(self.doDown)
        l2.addWidget(downButton)
        l.addLayout(l2)
        self.device = None
        self.hexEdit = HexEdit()
        self.Address = 0x8000000
        l.addWidget(self.hexEdit)
        self.addressLine.returnPressed.connect(self.refresh)

    def refresh(self):
        address = self.Address
        if self.device:
            data = self.device.iface.read_mem32(address, self.BlockSize)
        else:
            data = bytearray(self.BlockSize)
        self.hexEdit.bv.Data = data
        self.hexEdit.bv.Offset = address

    def getAddress(self):
          txt = self.addressLine.text()
          return int(txt, 16)

    def doUp(self):
        self.Address -= self.BlockSize

    def doDown(self):
        self.Address += self.BlockSize

    def setAddress(self, address):
        self.addressLine.setText('{0:08X}'.format(address))
        self.refresh()
    Address = property(getAddress, setAddress)

    def setDevice(self, dev):
        self.device = dev
        self.Address = 0x8000000
