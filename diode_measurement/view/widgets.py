import traceback

from PyQt5 import QtWidgets

__all__ = ["showException"]


def showException(exc, parent=None):
    details = "".join(traceback.format_tb(exc.__traceback__))
    dialog = QtWidgets.QMessageBox(parent)
    dialog.setWindowTitle("Exception occured")
    dialog.setIcon(dialog.Critical)
    dialog.setText(format(exc))
    dialog.setDetailedText(details)
    dialog.setStandardButtons(dialog.Ok)
    dialog.setDefaultButton(dialog.Ok)
    # Fix message box width
    spacer = QtWidgets.QSpacerItem(448, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
    dialog.layout().addItem(spacer, dialog.layout().rowCount(), 0, 1, dialog.layout().columnCount())
    dialog.exec()
