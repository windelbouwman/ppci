""" Wrapper around the ppci.binutils.dbg.Debugger object.

Main purpose is to fire Qt signals when something happens on the target.
"""

from qtwrapper import QtCore, pyqtSignal


class QDebugger(QtCore.QObject):
    """ Thin wrapper around the Debugger object.

    This class is mainly an adapter between the GUI logic and the lower level
    classes.
    """
    stopped = pyqtSignal()
    started = pyqtSignal()
    halted = pyqtSignal(bool)

    def __init__(self, debugger):
        super().__init__()
        self.debugger = debugger
        self.debugger.events.on_stop += self._handle_stopped
        self.debugger.events.on_start += self._handle_started

    def run(self):
        self.debugger.run()

    def stop(self):
        self.debugger.stop()

    def step(self):
        self.debugger.step()

    def _handle_stopped(self):
        self.stopped.emit()
        self.halted.emit(True)

    def _handle_started(self):
        self.started.emit()
        self.halted.emit(False)
