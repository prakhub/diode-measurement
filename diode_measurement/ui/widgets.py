import traceback

from PyQt5 import QtCore, QtWidgets

__all__ = ["showException", "ResourceWidget"]


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


class ResourceWidget(QtWidgets.QGroupBox):

    modelChanged = QtCore.pyqtSignal(str)
    resourceChanged = QtCore.pyqtSignal(str)
    terminationChanged = QtCore.pyqtSignal(str)
    timeoutChanged = QtCore.pyqtSignal(float)

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.setTitle("Instrument")

        self.modelLabel = QtWidgets.QLabel("Model")

        self.modelComboBox = QtWidgets.QComboBox()
        self.modelComboBox.setToolTip("Instrument model.")
        self.modelComboBox.setStatusTip("Instrument model.")
        self.modelComboBox.currentTextChanged.connect(
            lambda text: self.modelChanged.emit(text)
        )

        self.resourceLabel = QtWidgets.QLabel("Resource")

        self.resourceLineEdit = QtWidgets.QLineEdit()
        self.resourceLineEdit.setToolTip("Instrument resource GPIB number, IP and port or any valid VISA resource name.")
        self.resourceLineEdit.setStatusTip("Instrument resource GPIB number, IP and port or any valid VISA resource name.")
        self.resourceLineEdit.editingFinished.connect(
            lambda: self.resourceChanged.emit(self.resourceName())
        )

        self.terminationLabel = QtWidgets.QLabel("Termination")

        self.terminationComboBox = QtWidgets.QComboBox()
        self.terminationComboBox.setToolTip("Read and write termination characters.")
        self.terminationComboBox.setStatusTip("Read and write termination characters.")
        self.terminationComboBox.addItem("CR+LF", "\r\n")
        self.terminationComboBox.addItem("CR", "\r")
        self.terminationComboBox.addItem("LF", "\n")
        self.terminationComboBox.currentIndexChanged.connect(
            lambda index: self.terminationChanged.emit(self.terminationComboBox.itemData(index))
        )

        self.timeoutLabel = QtWidgets.QLabel("Timeout")

        self.timeoutSpinBox = QtWidgets.QDoubleSpinBox()
        self.timeoutSpinBox.setSuffix(" s")
        self.timeoutSpinBox.setRange(1, 60)
        self.timeoutSpinBox.setValue(4)
        self.timeoutSpinBox.setDecimals(2)
        self.timeoutSpinBox.valueChanged.connect(
            lambda value: self.timeoutChanged.emit(value)
        )

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.modelLabel)
        layout.addWidget(self.modelComboBox)
        layout.addWidget(self.resourceLabel)
        layout.addWidget(self.resourceLineEdit)
        hbox = QtWidgets.QHBoxLayout()
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.terminationLabel)
        vbox.addWidget(self.terminationComboBox)
        hbox.addLayout(vbox)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.timeoutLabel)
        vbox.addWidget(self.timeoutSpinBox)
        hbox.addLayout(vbox)
        layout.addLayout(hbox)
        layout.addStretch()

    def setLocked(self, state: bool) -> None:
        self.modelComboBox.setEnabled(not state)
        self.resourceLineEdit.setEnabled(not state)
        self.terminationComboBox.setEnabled(not state)
        self.timeoutSpinBox.setEnabled(not state)

    def model(self) -> str:
        return self.modelComboBox.currentText()

    def setModel(self, model: str) -> None:
        index = self.modelComboBox.findText(model)
        self.modelComboBox.setCurrentIndex(max(0, index))
        self.modelChanged.emit(self.modelComboBox.itemText(max(0, index)))

    def addModel(self, model: str) -> None:
        self.modelComboBox.addItem(model)

    def resourceName(self) -> str:
        return self.resourceLineEdit.text().strip()

    def setResourceName(self, resource: str) -> None:
        self.resourceLineEdit.setText(resource)

    def termination(self) -> str:
        return self.terminationComboBox.currentData()

    def setTermination(self, termination: str) -> None:
        index = self.terminationComboBox.findData(termination)
        self.terminationComboBox.setCurrentIndex(max(0, index))
        self.terminationChanged.emit(self.terminationComboBox.itemData(max(0, index)))

    def timeout(self) -> float:
        return self.timeoutSpinBox.value()

    def setTimeout(self, timeout: float) -> None:
        self.timeoutSpinBox.setValue(timeout)
