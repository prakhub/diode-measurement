import os
import math
import time
import logging
import threading
import contextlib
from datetime import datetime

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import __version__

# Source meter units
from .ui.panels import K237Panel
from .ui.panels import K2410Panel
from .ui.panels import K2470Panel
from .ui.panels import K2657APanel

# Electrometers
from .ui.panels import K6514Panel
from .ui.panels import K6517Panel

# LCR meters
from .ui.panels import K595Panel
from .ui.panels import E4285Panel
from .ui.panels import E4980APanel

from .ui.widgets import showException

from .measurement import IVMeasurement
from .measurement import CVMeasurement

from .writer import Writer
from .utils import get_resource
from .utils import safe_filename
from .utils import format_metric

from .settings import SPECS

logger = logging.getLogger(__name__)

def isFinite(value):
    """Return True if value is a finite numerical value."""
    if value is None:
        return False
    return math.isfinite(value)

def handle_exception(method):
    def handle_exception(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as exc:
            logger.exception(exc)
            self.onFailed(exc)
    return handle_exception

class Controller(QtCore.QObject):

    failed = QtCore.pyqtSignal(object)
    finished = QtCore.pyqtSignal()
    update = QtCore.pyqtSignal(dict)
    ivReading = QtCore.pyqtSignal(dict)
    itReading = QtCore.pyqtSignal(dict)
    cvReading = QtCore.pyqtSignal(dict)

    def __init__(self, view):
        super().__init__()
        self.thread = None

        self.view = view
        self.view.setProperty("contentsUrl", "https://github.com/hephy-dd/diode-measurement")
        self.view.setProperty("about", f"Diode Measurement<br/>Version {__version__}<br/>(c) 2021 HEPHY.at")

        # Source meter unit
        role = self.view.addRole("SMU")
        role.addInstrument(K237Panel())
        role.addInstrument(K2410Panel())
        role.addInstrument(K2470Panel())
        role.addInstrument(K2657APanel())

        # Electrometer
        role = self.view.addRole("ELM")
        role.addInstrument(K6514Panel())
        role.addInstrument(K6517Panel())

        # LCR meter
        role = self.view.addRole("LCR")
        role.addInstrument(K595Panel())
        # TODO
        # role.addInstrument(E4285Panel())
        role.addInstrument(E4980APanel())

        # Temperatur
        role = self.view.addRole("Temperature")

        self.state = {}

        self.view.startAction.triggered.connect(lambda: self.onStart())
        self.view.startButton.clicked.connect(lambda: self.onStart())

        self.view.stopAction.triggered.connect(lambda: self.onStop())
        self.view.stopButton.clicked.connect(lambda: self.onStop())

        self.view.continuousAction.toggled.connect(self.onContinuousToggled)
        self.view.continuousCheckBox.stateChanged.connect(self.onContinuousChanged)

        for spec in SPECS:
            self.view.generalWidget.addMeasurement(spec)
        self.view.generalWidget.measurementComboBox.currentIndexChanged.connect(self.onMeasurementChanged)

        self.view.generalWidget.outputLineEdit.editingFinished.connect(self.onOutputEditingFinished)
        self.view.generalWidget.currentComplianceChanged.connect(self.onCurrentComplianceChanged)
        self.view.generalWidget.continueInComplianceChanged.connect(self.onContinueInComplianceChanged)
        self.view.generalWidget.waitingTimeContinuousChanged.connect(self.onWaitingTimeContinuousChanged)

        self.view.unlock()
        self.onMeasurementChanged(0)

        self.finished.connect(self.onFinished)
        self.failed.connect(self.onFailed)
        self.update.connect(self.onUpdate)
        self.ivReading.connect(self.onIVReading)
        self.itReading.connect(self.onItReading)
        self.cvReading.connect(self.onCVReading)

        self.view.generalWidget.smuCheckBox.toggled.connect(self.onToggleSmu)
        self.view.generalWidget.elmCheckBox.toggled.connect(self.onToggleElm)

        self.view.messageLabel.hide()
        self.view.progressBar.hide()

    def prepareState(self):
        state = {}

        state["sample"] = self.view.generalWidget.sampleName()
        state["measurement_type"] = self.view.generalWidget.currentMeasurement().get("type")
        state["timestamp"] = time.time()

        state["continuous"] = self.view.isContinuous()
        state["reset"] = self.view.isReset()
        state["voltage_begin"] = self.view.generalWidget.beginVoltage()
        state["voltage_end"] = self.view.generalWidget.endVoltage()
        state["voltage_step"] = self.view.generalWidget.stepVoltage()
        state["waiting_time"] = self.view.generalWidget.waitingTime()
        state["current_compliance"] = self.view.generalWidget.currentCompliance()
        state["continue_in_compliance"] = self.view.generalWidget.isContinueInCompliance()
        state["waiting_time_continuous"] = self.view.generalWidget.waitingTimeContinuous()

        for role in self.view.roles():
            key = role.name().lower()
            resource = role.resourceWidget.resourceName()
            resource_name, visa_library = get_resource(resource)
            state[f"{key}_resource_name"] = resource_name
            state[f"{key}_visa_library"] = visa_library
            state[f"{key}_model"] = role.resourceWidget.model()
            state[f"{key}_termination"] = role.resourceWidget.termination()
            state[f"{key}_timeout"] = role.resourceWidget.timeout()
            state.update({key: role.config()})

        if self.view.generalWidget.isSMUEnabled():
            state["source"] = "smu"
        elif self.view.generalWidget.isELMEnabled():
            state["source"] = "elm"
        elif self.view.generalWidget.isLCREnabled():
            state["source"] = "lcr"

        state.setdefault("smu", {}).update({"enabled": self.view.generalWidget.isSMUEnabled()})
        state.setdefault("elm", {}).update({"enabled": self.view.generalWidget.isELMEnabled()})
        state.setdefault("lcr", {}).update({"enabled": self.view.generalWidget.isLCREnabled()})

        for key, value in state.items():
            logger.info('> %s: %s', key, value)

        return state

    @handle_exception
    def loadSettings(self):
        settings = QtCore.QSettings()

        size = settings.value("mainwindow.size", QtCore.QSize(800, 600), QtCore.QSize)
        self.view.resize(size)

        size = settings.value("logwindow.size", QtCore.QSize(640, 480), QtCore.QSize)
        self.view.logWindow.resize(size)

        continuous = settings.value("continuous", False, bool)
        self.view.setContinuous(continuous)

        reset = settings.value("reset", False, bool)
        self.view.setReset(reset)

        settings.beginGroup("generalTab")

        index = settings.value("measurement/index", 0, int)
        self.view.generalWidget.measurementComboBox.setCurrentIndex(index)

        enabled = settings.value("smu/enabled", False, bool)
        self.view.generalWidget.setSMUEnabled(enabled)

        enabled = settings.value("elm/enabled", False, bool)
        self.view.generalWidget.setELMEnabled(enabled)

        enabled = settings.value("lcr/enabled", False, bool)
        self.view.generalWidget.setLCREnabled(enabled)

        sample = settings.value("sampleName", "Unnamed")
        self.view.generalWidget.setSampleName(sample)

        path = settings.value("outputDir", os.path.expanduser("~"))
        self.view.generalWidget.setOutputDir(path)

        voltage = settings.value("beginVoltage", 1, float)
        self.view.generalWidget.setBeginVoltage(voltage)

        voltage = settings.value("endVoltage", 1, float)
        self.view.generalWidget.setEndVoltage(voltage)

        voltage = settings.value("stepVoltage", 1, float)
        self.view.generalWidget.setStepVoltage(voltage)

        waitingTime = settings.value("waitingTime", 1, float)
        self.view.generalWidget.setWaitingTime(waitingTime)

        currentCompliance = settings.value("currentCompliance", 1, float)
        self.view.generalWidget.setCurrentCompliance(currentCompliance)

        continueInCompliance = settings.value("continueInCompliance", False, bool)
        self.view.generalWidget.setContinueInCompliance(continueInCompliance)

        waitingTime = settings.value("waitingTimeContinuous", 1, float)
        self.view.generalWidget.setWaitingTimeContinuous(waitingTime)

        settings.endGroup()

        settings.beginGroup("roles")

        for role in self.view.roles():
            name = role.name().lower()
            settings.beginGroup(name)
            role.setModel(settings.value("model", ""))
            role.setResourceName(settings.value("resource", ""))
            role.setTermination(settings.value("termination", ""))
            role.setTimeout(settings.value("timeout", 4, int))
            role.setConfig(settings.value("config", {}, dict))
            settings.endGroup()

        settings.endGroup()

    @handle_exception
    def storeSettings(self):
        settings = QtCore.QSettings()

        size = self.view.size()
        settings.setValue("mainwindow.size", size)

        size = self.view.logWindow.size()
        settings.setValue("logwindow.size", size)

        continuous = self.view.isContinuous()
        settings.setValue("continuous", continuous)

        reset = self.view.isReset()
        settings.setValue("reset", reset)

        settings.beginGroup("generalTab")

        measurement_index = self.view.generalWidget.measurementComboBox.currentIndex()
        settings.setValue("measurement/index", measurement_index)

        enabled = self.view.generalWidget.isSMUEnabled()
        settings.setValue("smu/enabled", enabled)

        enabled = self.view.generalWidget.isELMEnabled()
        settings.setValue("elm/enabled", enabled)

        enabled = self.view.generalWidget.isLCREnabled()
        settings.setValue("lcr/enabled", enabled)

        sample = self.view.generalWidget.sampleName()
        settings.setValue("sampleName", sample)

        path = self.view.generalWidget.outputDir()
        settings.setValue("outputDir", path)

        voltage = self.view.generalWidget.beginVoltage()
        settings.setValue("beginVoltage", voltage)

        voltage = self.view.generalWidget.endVoltage()
        settings.setValue("endVoltage", voltage)

        voltage = self.view.generalWidget.stepVoltage()
        settings.setValue("stepVoltage", voltage)

        waitingTime = self.view.generalWidget.waitingTime()
        settings.setValue("waitingTime", waitingTime)

        currentCompliance = self.view.generalWidget.currentCompliance()
        settings.setValue("currentCompliance", currentCompliance)

        continueInCompliance = self.view.generalWidget.isContinueInCompliance()
        settings.setValue("continueInCompliance", continueInCompliance)

        waitingTime = self.view.generalWidget.waitingTimeContinuous()
        settings.setValue("waitingTimeContinuous", waitingTime)

        settings.endGroup()

        settings.beginGroup("roles")

        for role in self.view.roles():
            name = role.name().lower()
            settings.beginGroup(name)
            settings.setValue("model", role.model())
            settings.setValue("resource", role.resourceName())
            settings.setValue("termination", role.termination())
            settings.setValue("timeout", role.timeout())
            settings.setValue("config", role.config())
            settings.endGroup()

        settings.endGroup()

    def onStart(self):
        self.view.lock()
        self.view.clear()

        self.state.update(self.prepareState())
        self.state.update({"stop_requested": False})

        measurement = {
            "iv": IVMeasurement,
            "cv": CVMeasurement,
        }.get(self.state.get("measurement_type"))(self.state)

        measurement.update.connect(lambda data: self.update.emit(data))

        if isinstance(measurement, IVMeasurement):
            measurement.ivReading.connect(lambda reading: self.ivReading.emit(reading))
            measurement.itReading.connect(lambda reading: self.itReading.emit(reading))
        elif isinstance(measurement, CVMeasurement):
            measurement.cvReading.connect(lambda reading: self.cvReading.emit(reading))

        self.thread = threading.Thread(target=self.runMeasurement, args=[measurement])
        self.thread.start()

    def onStop(self):
        self.state.update({"stop_requested": True})
        self.view.setMessage("Stop requested...")

    def onFinished(self):
        self.view.unlock()
        self.view.setMessage("")
        self.view.messageLabel.hide()
        self.view.progressBar.hide()

    def onFailed(self, exc):
        showException(exc, self.view)

    def onUpdate(self, data):
        if 'source_voltage' in data:
            self.view.updateSourceVoltage(data.get('source_voltage'))
        if 'smu_current' in data:
            self.view.updateSMUCurrent(data.get('smu_current'))
        if 'elm_current' in data:
            self.view.updateELMCurrent(data.get('elm_current'))
        if 'lcr_capacity' in data:
            self.view.updateLCRCapacity(data.get('lcr_capacity'))
        if 'source_output_state' in data:
            self.view.updateSourceOutputState(data.get('source_output_state'))
        if 'message' in data:
            self.view.setMessage(data.get('message', ''))
        if 'progress' in data:
            self.view.setProgress(*data.get('progress', (0, 0, 0)))

    def onIVReading(self, reading):
        voltage = reading.get('voltage')
        i_smu = reading.get('i_smu')
        i_elm = reading.get('i_elm')
        if not isFinite(voltage):
            return
        if isFinite(i_smu):
            self.view.ivPlotWidget.append('smu', voltage, i_smu)
        if isFinite(i_elm):
            self.view.ivPlotWidget.append('elm', voltage, i_elm)

    def onItReading(self, reading):
        timestamp = reading.get('timestamp')
        i_smu = reading.get('i_smu')
        i_elm = reading.get('i_elm')
        if isFinite(i_smu):
            self.view.itPlotWidget.append('smu', timestamp, i_smu)
        if isFinite(i_elm):
            self.view.itPlotWidget.append('elm', timestamp, i_elm)

    def onCVReading(self, reading):
        voltage = reading.get('voltage')
        c_lcr = reading.get('c_lcr')
        if not isFinite(voltage):
            return
        if isFinite(c_lcr):
            self.view.cvPlotWidget.append('lcr', voltage, c_lcr)
            self.view.cv2PlotWidget.append('lcr', voltage, 1 / c_lcr ** 2)

    def onContinuousToggled(self, checked):
        self.view.setContinuous(checked)
        self.view.itPlotWidget.setVisible(checked)

    def onContinuousChanged(self, state):
        self.onContinuousToggled(state == QtCore.Qt.Checked)

    def onMeasurementChanged(self, index):
        spec = SPECS[index]

        if spec.get("type") == "iv":
            self.view.raiseIVTab()
            self.view.continuousAction.setEnabled(True)
            self.view.continuousCheckBox.setEnabled(True)
            self.view.generalWidget.continuousGroupBox.setEnabled(True)
        elif spec.get("type") == "cv":
            self.view.raiseCVTab()
            self.view.continuousAction.setEnabled(False)
            self.view.continuousCheckBox.setEnabled(False)
            self.view.generalWidget.continuousGroupBox.setEnabled(False)

        enabled = "SMU" in spec.get("instruments", [])
        self.view.generalWidget.smuCheckBox.setEnabled(enabled)
        self.view.smuGroupBox.setEnabled(enabled)

        enabled = "ELM" in spec.get("instruments", [])
        self.view.generalWidget.elmCheckBox.setEnabled(enabled)
        self.view.elmGroupBox.setEnabled(enabled)

        enabled = "LCR" in spec.get("instruments", [])
        self.view.generalWidget.lcrCheckBox.setEnabled(enabled)
        self.view.lcrGroupBox.setEnabled(enabled)

        enabled = "SMU" in spec.get("default_instruments", [])
        self.view.generalWidget.setSMUEnabled(enabled)

        enabled = "ELM" in spec.get("default_instruments", [])
        self.view.generalWidget.setELMEnabled(enabled)

        enabled = "LCR" in spec.get("default_instruments", [])
        self.view.generalWidget.setLCREnabled(enabled)

        unit = spec.get("voltage_unit")
        self.view.generalWidget.setVoltageUnit(unit)

        voltage = spec.get("default_begin_voltage", 0.0)
        self.view.generalWidget.setBeginVoltage(voltage)

        voltage = spec.get("default_end_voltage", 0.0)
        self.view.generalWidget.setEndVoltage(voltage)

        voltage = spec.get("default_step_voltage", 0.0)
        self.view.generalWidget.setStepVoltage(voltage)

        value = spec.get("default_waiting_time", 1.0)
        self.view.generalWidget.setWaitingTime(value)

        value = spec.get("default_waiting_time_continuous", 1.0)
        self.view.generalWidget.setWaitingTimeContinuous(value)

        value = spec.get("current_compliance_unit")
        self.view.generalWidget.setCurrentComplianceUnit(value)

        value = spec.get("default_current_compliance", 0.0)
        self.view.generalWidget.setCurrentCompliance(value)

    def onToggleSmu(self, state):
        self.view.ivPlotWidget.smuSeries.setVisible(state)
        self.view.itPlotWidget.smuSeries.setVisible(state)
        self.view.smuGroupBox.setEnabled(state)

    def onToggleElm(self, state):
        self.view.ivPlotWidget.elmSeries.setVisible(state)
        self.view.itPlotWidget.elmSeries.setVisible(state)
        self.view.elmGroupBox.setEnabled(state)

    def onOutputEditingFinished(self):
        if not self.view.generalWidget.outputLineEdit.text().strip():
            self.view.generalWidget.outputLineEdit.setText(os.path.expanduser("~"))

    def onCurrentComplianceChanged(self, value):
        logging.info("updated current_compliance: %s", format_metric(value, 'A'))
        self.state.update({"current_compliance": value})

    def onContinueInComplianceChanged(self, checked):
        logging.info("updated continue_in_compliance: %s", checked == True)
        self.state.update({"continue_in_compliance": checked})

    def onWaitingTimeContinuousChanged(self, value):
        logging.info("updated waiting_time_continuous: %s", format_metric(value, 's'))
        self.state.update({"waiting_time_continuous": value})

    def createFilename(self):
        path = self.view.generalWidget.outputDir()
        sample = self.state.get('sample')
        timestamp = datetime.fromtimestamp(self.state.get('timestamp', 0)).strftime("%Y-%m-%dT%H-%M-%S")
        filename = safe_filename(f"{sample}-{timestamp}.txt")
        return os.path.join(path, filename)

    def runMeasurement(self, measurement):
        try:
            for name in ("smu", "lcr", "elm"):
                measurement.prepareDriver(name)

            filename = self.createFilename()
            path = os.path.dirname(filename)
            if not os.path.exists(path):
                os.makedirs(path)
            with contextlib.ExitStack() as stack:
                fp = stack.enter_context(open(filename, "w"))
                writer = Writer(measurement, fp)
                measurement.run()
        except Exception as exc:
            logger.exception(exc)
            self.failed.emit(exc)
        finally:
            self.finished.emit()
