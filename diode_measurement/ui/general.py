from PyQt5 import QtCore
from PyQt5 import QtWidgets

from ..utils import ureg

__all__ = ['GeneralWidget']

class GeneralWidget(QtWidgets.QWidget):

    currentComplianceChanged = QtCore.pyqtSignal(float)
    continueInComplianceChanged = QtCore.pyqtSignal(bool)
    waitingTimeContinuousChanged = QtCore.pyqtSignal(float)
    changeVoltageContinuousRequested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("General")

        self._createWidgets()
        self._createLayout()

    def _createWidgets(self):
        self.measurementComboBox = QtWidgets.QComboBox()

        self.smuCheckBox = QtWidgets.QCheckBox("SMU")
        self.elmCheckBox = QtWidgets.QCheckBox("ELM")
        self.lcrCheckBox = QtWidgets.QCheckBox("LCR")

        self.beginVoltageSpinBox = QtWidgets.QDoubleSpinBox()
        self.beginVoltageSpinBox.setDecimals(3)
        self.beginVoltageSpinBox.setRange(-2000.0, +2000.0)
        self.beginVoltageSpinBox.setSuffix(" V")

        self.endVoltageSpinBox = QtWidgets.QDoubleSpinBox()
        self.endVoltageSpinBox.setDecimals(3)
        self.endVoltageSpinBox.setRange(-2000.0, +2000.0)
        self.endVoltageSpinBox.setSuffix(" V")

        self.stepVoltageSpinBox = QtWidgets.QDoubleSpinBox()
        self.stepVoltageSpinBox.setDecimals(3)
        self.stepVoltageSpinBox.setRange(0, +2000.0)
        self.stepVoltageSpinBox.setSuffix(" V")

        self.waitingTimeSpinBox = QtWidgets.QDoubleSpinBox()
        self.waitingTimeSpinBox.setSuffix(" s")

        self.currentComplianceSpinBox = QtWidgets.QDoubleSpinBox()
        self.currentComplianceSpinBox.setDecimals(3)
        self.currentComplianceSpinBox.setRange(0.0, +2000.0)
        self.currentComplianceSpinBox.setSuffix(" uA")
        self.currentComplianceSpinBox.editingFinished.connect(
            lambda: self.currentComplianceChanged.emit(self.currentCompliance())
        )

        self.continueInComplianceCheckBox = QtWidgets.QCheckBox()
        self.continueInComplianceCheckBox.setText("Continue in Compliance")
        self.continueInComplianceCheckBox.setStatusTip("Continue measurement when source in compliance.""")
        self.continueInComplianceCheckBox.setChecked(False)
        self.continueInComplianceCheckBox.toggled.connect(
            lambda checked: self.continueInComplianceChanged.emit(checked)
        )

        self.sampleLineEdit = QtWidgets.QLineEdit()

        self.outputLineEdit = QtWidgets.QLineEdit()
        completer = QtWidgets.QCompleter(self)
        completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        model = QtWidgets.QDirModel(completer)
        model.setFilter(QtCore.QDir.Dirs | QtCore.QDir.Drives | QtCore.QDir.NoDotAndDotDot | QtCore.QDir.AllDirs)
        completer.setModel(model)
        self.outputLineEdit.setCompleter(completer)

        self.outputToolButton = QtWidgets.QToolButton()
        self.outputToolButton.setText("...")
        self.outputToolButton.setStatusTip("Select output directory.")
        self.outputToolButton.clicked.connect(self.selectOutput)

        self.waitingTimeContinuousSpinBox = QtWidgets.QDoubleSpinBox()
        self.waitingTimeContinuousSpinBox.setSuffix(" s")
        self.waitingTimeContinuousSpinBox.setStatusTip("Waiting time for continuous measurement.")
        self.waitingTimeContinuousSpinBox.editingFinished.connect(
            lambda: self.waitingTimeContinuousChanged.emit(self.waitingTimeContinuous())
        )

        self.changeVoltageButton = QtWidgets.QToolButton()
        self.changeVoltageButton.setText("Change Voltage...")
        self.changeVoltageButton.setEnabled(False)
        self.changeVoltageButton.clicked.connect(
            lambda: (self.changeVoltageContinuousRequested.emit(),
                self.changeVoltageButton.setEnabled(False))
        )

        self.measurementGroupBox = QtWidgets.QGroupBox()
        self.measurementGroupBox.setTitle("Measurement")

        self.rampGroupBox = QtWidgets.QGroupBox()
        self.rampGroupBox.setTitle("Ramp")

        self.complianceGroupBox = QtWidgets.QGroupBox()
        self.complianceGroupBox.setTitle("Compliance")

        self.continuousGroupBox = QtWidgets.QGroupBox()
        self.continuousGroupBox.setTitle("Continuous Meas.")

    def _createLayout(self):
        layout = QtWidgets.QVBoxLayout(self.measurementGroupBox)
        layout.addWidget(QtWidgets.QLabel("Type"))
        layout.addWidget(self.measurementComboBox)
        layout.addWidget(QtWidgets.QLabel("Instruments"))
        self.instrumentWidget = QtWidgets.QWidget()
        layout.addWidget(self.instrumentWidget)
        self.instrumentLayout = QtWidgets.QHBoxLayout(self.instrumentWidget)
        self.instrumentLayout.addWidget(self.smuCheckBox)
        self.instrumentLayout.addWidget(self.elmCheckBox)
        self.instrumentLayout.addWidget(self.lcrCheckBox)
        self.instrumentLayout.addStretch()
        self.instrumentLayout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QtWidgets.QLabel("Sample"))
        layout.addWidget(self.sampleLineEdit)
        layout.addWidget(QtWidgets.QLabel("Output"))
        outputLayout = QtWidgets.QHBoxLayout()
        outputLayout.addWidget(self.outputLineEdit)
        outputLayout.addWidget(self.outputToolButton)
        layout.addLayout(outputLayout)
        layout.addStretch()

        layout = QtWidgets.QVBoxLayout(self.rampGroupBox)
        layout.addWidget(QtWidgets.QLabel("Begin"))
        layout.addWidget(self.beginVoltageSpinBox)
        layout.addWidget(QtWidgets.QLabel("End"))
        layout.addWidget(self.endVoltageSpinBox)
        layout.addWidget(QtWidgets.QLabel("Step"))
        layout.addWidget(self.stepVoltageSpinBox)
        layout.addWidget(QtWidgets.QLabel("Waiting Time"))
        layout.addWidget(self.waitingTimeSpinBox)
        layout.addStretch()

        layout = QtWidgets.QVBoxLayout(self.complianceGroupBox)
        layout.addWidget(QtWidgets.QLabel("Current"))
        layout.addWidget(self.currentComplianceSpinBox)
        layout.addWidget(self.continueInComplianceCheckBox)

        layout.addStretch()

        layout = QtWidgets.QVBoxLayout(self.continuousGroupBox)
        layout.addWidget(QtWidgets.QLabel("Waiting Time"))
        layout.addWidget(self.waitingTimeContinuousSpinBox)
        layout.addWidget(self.changeVoltageButton)
        layout.addStretch()

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.measurementGroupBox)
        layout.addWidget(self.rampGroupBox)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.complianceGroupBox)
        vbox.addWidget(self.continuousGroupBox)
        layout.addLayout(vbox)
        layout.addStretch()
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)
        layout.setStretch(2, 1)

    def lock(self):
        self.measurementComboBox.setEnabled(False)
        self.instrumentWidget.setEnabled(False)
        self.sampleLineEdit.setEnabled(False)
        self.outputLineEdit.setEnabled(False)
        self.outputToolButton.setEnabled(False)
        self.beginVoltageSpinBox.setEnabled(False)
        self.endVoltageSpinBox.setEnabled(False)
        self.stepVoltageSpinBox.setEnabled(False)
        self.waitingTimeSpinBox.setEnabled(False)
        self.changeVoltageButton.setEnabled(False)

    def unlock(self):
        self.measurementComboBox.setEnabled(True)
        self.instrumentWidget.setEnabled(True)
        self.sampleLineEdit.setEnabled(True)
        self.outputLineEdit.setEnabled(True)
        self.outputToolButton.setEnabled(True)
        self.beginVoltageSpinBox.setEnabled(True)
        self.endVoltageSpinBox.setEnabled(True)
        self.stepVoltageSpinBox.setEnabled(True)
        self.waitingTimeSpinBox.setEnabled(True)
        self.changeVoltageButton.setEnabled(False)

    def addMeasurement(self, spec):
        self.measurementComboBox.addItem(spec.get("title"), spec)

    def currentMeasurement(self):
        return self.measurementComboBox.currentData()

    def isSMUEnabled(self):
        return self.smuCheckBox.isChecked()

    def setSMUEnabled(self, enabled):
        return self.smuCheckBox.setChecked(enabled)

    def isELMEnabled(self):
        return self.elmCheckBox.isChecked()

    def setELMEnabled(self, enabled):
        return self.elmCheckBox.setChecked(enabled)

    def isLCREnabled(self):
        return self.lcrCheckBox.isChecked()

    def setLCREnabled(self, enabled):
        return self.lcrCheckBox.setChecked(enabled)

    def sampleName(self):
        return self.sampleLineEdit.text().strip()

    def setSampleName(self, text):
        self.sampleLineEdit.setText(text)

    def outputDir(self):
        return self.outputLineEdit.text().strip()

    def setOutputDir(self, text):
        self.outputLineEdit.setText(text)

    def selectOutput(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select ouput path", self.outputDir())
        if path:
            self.setOutputDir(path)

    def setVoltageUnit(self, unit):
        self.beginVoltageSpinBox.setSuffix(f" {unit}")
        self.endVoltageSpinBox.setSuffix(f" {unit}")
        self.stepVoltageSpinBox.setSuffix(f" {unit}")

    def beginVoltage(self):
        unit = self.beginVoltageSpinBox.suffix().strip()
        return (self.beginVoltageSpinBox.value() * ureg(unit)).to("V").m

    def setBeginVoltage(self, value):
        unit = self.beginVoltageSpinBox.suffix().strip()
        return self.beginVoltageSpinBox.setValue((value * ureg("V")).to(unit).m)

    def endVoltage(self):
        unit = self.endVoltageSpinBox.suffix().strip()
        return (self.endVoltageSpinBox.value() * ureg(unit)).to("V").m

    def setEndVoltage(self, value):
        unit = self.endVoltageSpinBox.suffix().strip()
        return self.endVoltageSpinBox.setValue((value * ureg("V")).to(unit).m)

    def stepVoltage(self):
        unit = self.stepVoltageSpinBox.suffix().strip()
        return (self.stepVoltageSpinBox.value() * ureg(unit)).to("V").m

    def setStepVoltage(self, value):
        unit = self.stepVoltageSpinBox.suffix().strip()
        return self.stepVoltageSpinBox.setValue((value * ureg("V")).to(unit).m)

    def waitingTime(self):
        return self.waitingTimeSpinBox.value()

    def setWaitingTime(self, value):
        return self.waitingTimeSpinBox.setValue(value)

    def setCurrentComplianceUnit(self, unit):
        self.currentComplianceSpinBox.setSuffix(f" {unit}")

    def currentCompliance(self):
        unit = self.currentComplianceSpinBox.suffix().strip()
        return (self.currentComplianceSpinBox.value() * ureg(unit)).to("A").m

    def setCurrentCompliance(self, value):
        unit = self.currentComplianceSpinBox.suffix().strip()
        return self.currentComplianceSpinBox.setValue((value * ureg("A")).to(unit).m)

    def isContinueInCompliance(self):
        return self.continueInComplianceCheckBox.isChecked()

    def setContinueInCompliance(self, enabled):
        self.continueInComplianceCheckBox.setChecked(enabled)

    def waitingTimeContinuous(self):
        return self.waitingTimeContinuousSpinBox.value()

    def setWaitingTimeContinuous(self, value):
        return self.waitingTimeContinuousSpinBox.setValue(value)
