import logging
import webbrowser

from typing import Dict, List, Optional

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from .plots import IVPlotWidget
from .plots import ItPlotWidget
from .plots import CVPlotWidget
from .plots import CV2PlotWidget

from .general import GeneralWidget
from .role import RoleWidget
from .logwindow import LogWindow

from ..utils import format_metric
from ..utils import format_switch


class MainWindow(QtWidgets.QMainWindow):

    prepareChangeVoltage = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.setProperty("locked", False)

        self._createActions()
        self._createMenus()
        self._createWidgets()
        self._createLayout()
        self._createDialogs()

    def _createActions(self) -> None:
        self.importAction = QtWidgets.QAction("&Import File...")
        self.importAction.setStatusTip("Import measurement data")

        self.quitAction = QtWidgets.QAction("&Quit")
        self.quitAction.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
        self.quitAction.setStatusTip("Quit the application")
        self.quitAction.triggered.connect(self.close)

        self.logWindowAction = QtWidgets.QAction("Logging...")
        self.logWindowAction.setStatusTip("Show log window")
        self.logWindowAction.triggered.connect(self.showLogWindow)

        self.startAction = QtWidgets.QAction("&Start")
        self.startAction.setStatusTip("Start a new measurement")

        self.stopAction = QtWidgets.QAction("Sto&p")
        self.stopAction.setStatusTip("Stop an active measurement")

        self.continuousAction = QtWidgets.QAction("&Continuous Meas.")
        self.continuousAction.setCheckable(True)
        self.continuousAction.setStatusTip("Enable continuous measurement")

        self.changeVoltageAction = QtWidgets.QAction("&Change Voltage...")
        self.changeVoltageAction.setStatusTip("Change voltage in continuous measurement")
        self.changeVoltageAction.setEnabled(False)
        self.changeVoltageAction.triggered.connect(self.prepareChangeVoltage.emit)

        self.contentsAction = QtWidgets.QAction("&Contents")
        self.contentsAction.setStatusTip("Open the user manual")
        self.contentsAction.setShortcut(QtGui.QKeySequence('F1'))
        self.contentsAction.triggered.connect(self.showContents)

        self.aboutQtAction = QtWidgets.QAction("About &Qt")
        self.aboutQtAction.setStatusTip("About the used Qt framework")
        self.aboutQtAction.triggered.connect(self.showAboutQt)

        self.aboutAction = QtWidgets.QAction("&About")
        self.aboutAction.setStatusTip("About the application")
        self.aboutAction.triggered.connect(self.showAbout)

    def _createMenus(self) -> None:
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.importAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.quitAction)

        self.viewMenu = self.menuBar().addMenu("&View")
        self.viewMenu.addAction(self.logWindowAction)

        self.measureMenu = self.menuBar().addMenu("&Measure")
        self.measureMenu.addAction(self.startAction)
        self.measureMenu.addAction(self.stopAction)
        self.measureMenu.addSeparator()
        self.measureMenu.addAction(self.continuousAction)
        self.measureMenu.addAction(self.changeVoltageAction)

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.contentsAction)
        self.helpMenu.addAction(self.aboutQtAction)
        self.helpMenu.addAction(self.aboutAction)

    def _createWidgets(self) -> None:
        self.ivPlotWidget = IVPlotWidget()

        self.itPlotWidget = ItPlotWidget()
        self.itPlotWidget.setVisible(False)

        self.cvPlotWidget = CVPlotWidget()

        self.cv2PlotWidget = CV2PlotWidget()

        self.ivWidget = QtWidgets.QWidget()

        self.cvWidget = QtWidgets.QWidget()

        self.dataTabWidget = QtWidgets.QTabWidget()
        self.dataTabWidget.addTab(self.ivWidget, "IV")
        self.dataTabWidget.addTab(self.cvWidget, "CV")

        self.startButton = QtWidgets.QPushButton("&Start")
        self.startButton.setToolTip("Start a new measurement")
        self.startButton.setStatusTip("Start a new measurement")
        self.startButton.setCheckable(True)
        self.startButton.setStyleSheet("QPushButton:enabled{ color: green; }")

        self.stopButton = QtWidgets.QPushButton("Sto&p")
        self.stopButton.setToolTip("Stop an active measurement")
        self.stopButton.setStatusTip("Stop an active measurement")
        self.stopButton.setStyleSheet("QPushButton:enabled{ color: red; }")
        self.stopButton.setCheckable(True)
        self.stopButton.setMinimumHeight(72)

        self.continuousCheckBox = QtWidgets.QCheckBox("&Continuous Meas.")
        self.continuousCheckBox.setToolTip("Enable continuous measurement")
        self.continuousCheckBox.setStatusTip("Enable continuous measurement")

        self.resetCheckBox = QtWidgets.QCheckBox("&Reset Instruments")
        self.resetCheckBox.setToolTip("Reset instruments on start")
        self.resetCheckBox.setStatusTip("Reset instruments on start")

        self.generalWidget = GeneralWidget()
        self.generalWidget.changeVoltageButton.clicked.connect(self.changeVoltageAction.trigger)

        self.roleWidgets: Dict[str, RoleWidget] = {}

        self.controlTabWidget = QtWidgets.QTabWidget()
        self.controlTabWidget.addTab(self.generalWidget, self.generalWidget.windowTitle())

        self.smuGroupBox = QtWidgets.QGroupBox()
        self.smuGroupBox.setTitle("SMU Status")

        self.elmGroupBox = QtWidgets.QGroupBox()
        self.elmGroupBox.setTitle("ELM Status")

        self.lcrGroupBox = QtWidgets.QGroupBox()
        self.lcrGroupBox.setTitle("LCR Status")

        self.dmmGroupBox = QtWidgets.QGroupBox()
        self.dmmGroupBox.setTitle("DMM Status")

        self.smuVoltageLineEdit = QtWidgets.QLineEdit("---")
        self.smuVoltageLineEdit.setReadOnly(True)
        self.smuVoltageLineEdit.setAlignment(QtCore.Qt.AlignRight)

        self.smuCurrentLineEdit = QtWidgets.QLineEdit("---")
        self.smuCurrentLineEdit.setReadOnly(True)
        self.smuCurrentLineEdit.setAlignment(QtCore.Qt.AlignRight)

        self.smuOutputStateLineEdit = QtWidgets.QLineEdit("---")
        self.smuOutputStateLineEdit.setReadOnly(True)
        self.smuOutputStateLineEdit.setAlignment(QtCore.Qt.AlignRight)

        self.elmVoltageLineEdit = QtWidgets.QLineEdit("---")
        self.elmVoltageLineEdit.setReadOnly(True)
        self.elmVoltageLineEdit.setAlignment(QtCore.Qt.AlignRight)

        self.elmCurrentLineEdit = QtWidgets.QLineEdit("---")
        self.elmCurrentLineEdit.setReadOnly(True)
        self.elmCurrentLineEdit.setAlignment(QtCore.Qt.AlignRight)

        self.elmOutputStateLineEdit = QtWidgets.QLineEdit("---")
        self.elmOutputStateLineEdit.setReadOnly(True)
        self.elmOutputStateLineEdit.setAlignment(QtCore.Qt.AlignRight)

        self.lcrVoltageLineEdit = QtWidgets.QLineEdit("---")
        self.lcrVoltageLineEdit.setReadOnly(True)
        self.lcrVoltageLineEdit.setAlignment(QtCore.Qt.AlignRight)

        self.lcrCurrentLineEdit = QtWidgets.QLineEdit("---")
        self.lcrCurrentLineEdit.setReadOnly(True)
        self.lcrCurrentLineEdit.setAlignment(QtCore.Qt.AlignRight)

        self.lcrOutputStateLineEdit = QtWidgets.QLineEdit("---")
        self.lcrOutputStateLineEdit.setReadOnly(True)
        self.lcrOutputStateLineEdit.setAlignment(QtCore.Qt.AlignRight)

        self.dmmTemperatureLineEdit = QtWidgets.QLineEdit("---")
        self.dmmTemperatureLineEdit.setReadOnly(True)
        self.dmmTemperatureLineEdit.setAlignment(QtCore.Qt.AlignRight)

        centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(centralWidget)

        self.messageLabel = QtWidgets.QLabel()
        self.statusBar().addPermanentWidget(self.messageLabel)

        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setFixedWidth(240)
        self.statusBar().addPermanentWidget(self.progressBar)

    def _createLayout(self) -> None:
        ivLayout = QtWidgets.QHBoxLayout(self.ivWidget)
        ivLayout.addWidget(self.ivPlotWidget)
        ivLayout.addWidget(self.itPlotWidget)
        ivLayout.setStretch(0, 1)
        ivLayout.setStretch(1, 1)

        cvLayout = QtWidgets.QHBoxLayout(self.cvWidget)
        cvLayout.addWidget(self.cvPlotWidget)
        cvLayout.addWidget(self.cv2PlotWidget)
        cvLayout.setStretch(0, 1)
        cvLayout.setStretch(1, 1)

        controlLayout = QtWidgets.QVBoxLayout()
        controlLayout.addWidget(self.startButton)
        controlLayout.addWidget(self.stopButton)
        controlLayout.addWidget(self.continuousCheckBox)
        controlLayout.addWidget(self.resetCheckBox)
        controlLayout.addStretch()

        smuGroupBox = QtWidgets.QHBoxLayout(self.smuGroupBox)
        vboxLayout = QtWidgets.QVBoxLayout()
        vboxLayout.addWidget(QtWidgets.QLabel("Voltage"))
        vboxLayout.addWidget(self.smuVoltageLineEdit)
        smuGroupBox.addLayout(vboxLayout)
        vboxLayout = QtWidgets.QVBoxLayout()
        vboxLayout.addWidget(QtWidgets.QLabel("Current"))
        vboxLayout.addWidget(self.smuCurrentLineEdit)
        smuGroupBox.addLayout(vboxLayout)
        vboxLayout = QtWidgets.QVBoxLayout()
        vboxLayout.addWidget(QtWidgets.QLabel("Output"))
        vboxLayout.addWidget(self.smuOutputStateLineEdit)
        smuGroupBox.addLayout(vboxLayout)
        smuGroupBox.setStretch(0, 3)
        smuGroupBox.setStretch(1, 3)
        smuGroupBox.setStretch(2, 1)

        elmGroupBox = QtWidgets.QHBoxLayout(self.elmGroupBox)
        vboxLayout = QtWidgets.QVBoxLayout()
        vboxLayout.addWidget(QtWidgets.QLabel("Voltage"))
        vboxLayout.addWidget(self.elmVoltageLineEdit)
        elmGroupBox.addLayout(vboxLayout)
        vboxLayout = QtWidgets.QVBoxLayout()
        vboxLayout.addWidget(QtWidgets.QLabel("Current"))
        vboxLayout.addWidget(self.elmCurrentLineEdit)
        elmGroupBox.addLayout(vboxLayout)
        vboxLayout = QtWidgets.QVBoxLayout()
        vboxLayout.addWidget(QtWidgets.QLabel("Output"))
        vboxLayout.addWidget(self.elmOutputStateLineEdit)
        elmGroupBox.addLayout(vboxLayout)
        elmGroupBox.setStretch(0, 3)
        elmGroupBox.setStretch(1, 3)
        elmGroupBox.setStretch(2, 1)

        lcrGroupBox = QtWidgets.QHBoxLayout(self.lcrGroupBox)
        vboxLayout = QtWidgets.QVBoxLayout()
        vboxLayout.addWidget(QtWidgets.QLabel("Voltage"))
        vboxLayout.addWidget(self.lcrVoltageLineEdit)
        lcrGroupBox.addLayout(vboxLayout)
        vboxLayout = QtWidgets.QVBoxLayout()
        vboxLayout.addWidget(QtWidgets.QLabel("Capacity"))
        vboxLayout.addWidget(self.lcrCurrentLineEdit)
        lcrGroupBox.addLayout(vboxLayout)
        vboxLayout = QtWidgets.QVBoxLayout()
        vboxLayout.addWidget(QtWidgets.QLabel("Output"))
        vboxLayout.addWidget(self.lcrOutputStateLineEdit)
        lcrGroupBox.addLayout(vboxLayout)
        lcrGroupBox.setStretch(0, 3)
        lcrGroupBox.setStretch(1, 3)
        lcrGroupBox.setStretch(2, 1)

        dmmGroupBox = QtWidgets.QHBoxLayout(self.dmmGroupBox)
        vboxLayout = QtWidgets.QVBoxLayout()
        vboxLayout.addWidget(QtWidgets.QLabel("Temperature"))
        vboxLayout.addWidget(self.dmmTemperatureLineEdit)
        dmmGroupBox.addLayout(vboxLayout)
        dmmGroupBox.addStretch()
        dmmGroupBox.setStretch(0, 2)
        dmmGroupBox.setStretch(1, 3)

        bottomLayout = QtWidgets.QHBoxLayout()
        bottomLayout.addLayout(controlLayout)
        bottomLayout.addWidget(self.controlTabWidget)
        vboxLayout = QtWidgets.QVBoxLayout()
        vboxLayout.addWidget(self.smuGroupBox)
        vboxLayout.addWidget(self.elmGroupBox)
        vboxLayout.addWidget(self.lcrGroupBox)
        vboxLayout.addWidget(self.dmmGroupBox)
        vboxLayout.addStretch()
        bottomLayout.addLayout(vboxLayout)
        bottomLayout.setStretch(0, 0)
        bottomLayout.setStretch(1, 7)
        bottomLayout.setStretch(2, 3)

        layout = QtWidgets.QVBoxLayout(self.centralWidget())
        layout.addWidget(self.dataTabWidget)
        layout.addLayout(bottomLayout)

    def _createDialogs(self) -> None:
        self.logWindow = LogWindow()
        self.logWindow.addLogger(logging.getLogger())
        self.logWindow.setLevel(logging.DEBUG)
        self.logWindow.resize(640, 420)
        self.logWindow.hide()

    def addRole(self, name: str) -> RoleWidget:
        if name in self.roleWidgets:
            raise KeyError(f"No suc role: {name}")
        widget = RoleWidget(name)
        self.roleWidgets[name] = widget
        self.controlTabWidget.addTab(widget, widget.name())
        return widget

    def findRole(self, name: str) -> Optional[RoleWidget]:
        return self.roleWidgets.get(name)

    def roles(self) -> List:
        return list(self.roleWidgets.values())

    def clear(self) -> None:
        """Clear displayed data in plots and inputs."""
        self.ivPlotWidget.clear()
        self.ivPlotWidget.reset()
        self.itPlotWidget.clear()
        self.itPlotWidget.reset()
        self.cvPlotWidget.clear()
        self.cvPlotWidget.reset()
        self.cv2PlotWidget.clear()
        self.cv2PlotWidget.reset()
        self.smuVoltageLineEdit.setText("---")
        self.smuCurrentLineEdit.setText("---")
        self.smuOutputStateLineEdit.setText("---")
        self.elmVoltageLineEdit.setText("---")
        self.elmCurrentLineEdit.setText("---")
        self.elmOutputStateLineEdit.setText("---")
        self.lcrVoltageLineEdit.setText("---")
        self.lcrCurrentLineEdit.setText("---")
        self.lcrOutputStateLineEdit.setText("---")
        self.dmmTemperatureLineEdit.setText("---")

    def setIdleState(self) -> None:
        self.importAction.setEnabled(True)
        self.startAction.setEnabled(True)
        self.stopAction.setEnabled(False)
        self.continuousAction.setEnabled(True)
        self.startButton.setEnabled(True)
        self.startButton.setChecked(False)
        self.stopButton.setEnabled(False)
        self.stopButton.setChecked(False)
        self.continuousCheckBox.setEnabled(True)
        self.resetCheckBox.setEnabled(True)
        self.generalWidget.unlock()
        for role in self.roles():
            role.unlock()
        self.setProperty("locked", False)

    def setRunningState(self) -> None:
        self.setProperty("locked", True)
        self.importAction.setEnabled(False)
        self.startAction.setEnabled(False)
        self.stopAction.setEnabled(True)
        self.continuousAction.setEnabled(False)
        self.startButton.setEnabled(False)
        self.startButton.setChecked(True)
        self.stopButton.setEnabled(True)
        self.stopButton.setChecked(False)
        self.continuousCheckBox.setEnabled(False)
        self.resetCheckBox.setEnabled(False)
        self.generalWidget.lock()
        for role in self.roles():
            role.lock()

    def setStoppingState(self) -> None:
        self.generalWidget.setStoppingState()

    def setMessage(self, message: str) -> None:
        self.messageLabel.show()
        self.messageLabel.setText(message)

    def clearMessage(self) -> None:
        self.messageLabel.hide()
        self.messageLabel.clear()

    def setProgress(self, minimum: int, maximum: int, value: int) -> None:
        self.progressBar.show()
        self.progressBar.setRange(minimum, maximum)
        self.progressBar.setValue(value)

    def clearProgress(self) -> None:
        self.progressBar.hide()
        self.progressBar.setRange(0, 1)
        self.progressBar.setValue(0)

    def raiseIVTab(self) -> None:
        index = self.dataTabWidget.indexOf(self.ivWidget)
        self.dataTabWidget.setCurrentIndex(index)

    def raiseCVTab(self) -> None:
        index = self.dataTabWidget.indexOf(self.cvWidget)
        self.dataTabWidget.setCurrentIndex(index)

    def isContinuous(self) -> bool:
        return self.continuousAction.isChecked()

    def setContinuous(self, enabled: bool) -> None:
        self.continuousAction.setChecked(enabled)
        self.continuousCheckBox.setChecked(enabled)

    def isChangeVoltageEnabled(self) -> bool:
        return self.changeVoltageAction.isEnabled()

    def setChangeVoltageEnabled(self, state: bool) -> None:
        self.changeVoltageAction.setEnabled(state)
        self.generalWidget.changeVoltageButton.setEnabled(state)

    def isReset(self) -> bool:
        return self.resetCheckBox.isChecked()

    def setReset(self, enabled: bool) -> None:
        return self.resetCheckBox.setChecked(enabled)

    def setSourceEnabled(self, source: str, enabled: bool) -> None:
        for widget in self.roles():
            if widget.name() == source:
                index = self.controlTabWidget.indexOf(widget)
                self.controlTabWidget.setTabEnabled(index, enabled)
        self.generalWidget.setSourceEnabled(source, enabled)

    def updateSourceVoltage(self, voltage: float) -> None:
        self.smuVoltageLineEdit.setText(format_metric(voltage, "V"))

    def updateSourceOutputState(self, state: bool) -> None:
        if self.smuGroupBox.isEnabled():
            self.smuOutputStateLineEdit.setText(format_switch(state))
        elif self.elmGroupBox.isEnabled():
            self.elmOutputStateLineEdit.setText(format_switch(state))
        elif self.lcrGroupBox.isEnabled():
            self.lcrOutputStateLineEdit.setText(format_switch(state))

    def updateSMUCurrent(self, current: float) -> None:
        self.smuCurrentLineEdit.setText(format_metric(current, "A"))

    def updateELMVoltage(self, voltage: float) -> None:
        self.elmVoltageLineEdit.setText(format_metric(voltage, "V"))

    def updateELMCurrent(self, current: float) -> None:
        self.elmCurrentLineEdit.setText(format_metric(current, "A"))

    def updateLCRCapacity(self, capacity: float) -> None:
        self.lcrCurrentLineEdit.setText(format_metric(capacity, "F"))

    def updateDMMTemperature(self, temperature: float) -> None:
        self.dmmTemperatureLineEdit.setText(format_metric(temperature, "°C"))

    def showLogWindow(self) -> None:
        self.logWindow.show()
        self.logWindow.raise_()

    def showContents(self) -> None:
        webbrowser.open(self.property("contentsUrl"))

    def showAboutQt(self) -> None:
        QtWidgets.QMessageBox.aboutQt(self)

    def showAbout(self) -> None:
        QtWidgets.QMessageBox.about(self, "About", self.property("about"))

    def showActiveInfo(self) -> None:
        title = "Measurement active"
        text = "Stop the current measurement to exiting the application."
        QtWidgets.QMessageBox.information(self, title, text)

    def closeEvent(self, event: QtCore.QEvent) -> None:
        if self.property("locked"):
            self.showActiveInfo()
            event.ignore()
        else:
            self.logWindow.close()
            event.accept()
