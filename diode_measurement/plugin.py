from PyQt5 import QtCore


class Plugin(QtCore.QObject):

    def __init__(self, parent=None):
        super().__init__(parent)

    def install(self, context):
        pass

    def shutdown(self, context):
        pass
