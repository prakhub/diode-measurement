import contextlib
import logging
import math
import os
import pathlib
import threading
import time

from datetime import datetime
from typing import Any, Dict, List, Iterator, Optional

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
from .ui.panels import K6517BPanel

# LCR meters
from .ui.panels import K595Panel
from .ui.panels import E4980APanel
from .ui.panels import A4284APanel

# DMM
from .ui.panels import K2700Panel

from .ui.widgets import showException
from .ui.dialogs import ChangeVoltageDialog

from .measurement import Measurement
from .measurement.iv import IVMeasurement
from .measurement.cv import CVMeasurement

from .plugin import PluginRegistryMixin

from .reader import Reader
from .writer import Writer

from .utils import get_resource
from .utils import safe_filename
from .utils import format_metric

from .cache import Cache
from .settings import DEFAULTS

__all__ = ["Controller"]

logger = logging.getLogger(__name__)

MEASUREMENTS = {
    "iv": IVMeasurement,
    "cv": CVMeasurement,
}


def handle_exception(method):
    def handle_exception(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as exc:
            logger.exception(exc)
            self.handleException(exc)
    return handle_exception


class MeasurementRunner:

    def __init__(self, measurement: Measurement) -> None:
        self.measurement = measurement

    def __call__(self) -> None:
        measurement = self.measurement
        filename = measurement.state.get("filename")
        with contextlib.ExitStack() as stack:
            if filename:
                logger.info("preparing output file: %s", filename)

                path = os.path.dirname(filename)
                if not os.path.exists(path):
                    logger.debug("create output dir: %s", path)
                    os.makedirs(path)

                fp = stack.enter_context(open(filename, "w", newline=""))
                writer = Writer(fp)
                # TODO
                # Note: using signals executes slots in main thread, should be worker thread
                measurement.startedHandlers.append(lambda state=measurement.state: writer.write_meta(state))
                if isinstance(measurement, IVMeasurement):
                    measurement.ivReadingHandlers.append(lambda reading: writer.write_iv_row(reading))
                    measurement.itReadingHandlers.append(lambda reading: writer.write_it_row(reading))
                if isinstance(measurement, CVMeasurement):
                    measurement.cvReadingHandlers.append(lambda reading: writer.write_cv_row(reading))
                measurement.finishedHandlers.append(lambda: writer.flush())
            measurement.run()


class AbstractController(QtCore.QObject):

    def __init__(self, view, parent=None) -> None:
        super().__init__(parent)
        self.view = view


class Controller(PluginRegistryMixin, AbstractController):

    started = QtCore.pyqtSignal()
    aborted = QtCore.pyqtSignal()
    update = QtCore.pyqtSignal(dict)
    failed = QtCore.pyqtSignal(Exception)
    finished = QtCore.pyqtSignal()

    requestChangeVoltage = QtCore.pyqtSignal(float, float, float)

    def __init__(self, view, parent=None) -> None:
        super().__init__(view, parent)

        self.abortRequested = threading.Event()
        self.measurementThread: Optional[threading.Thread] = None
        self.state: Dict[str, Any] = {}
        self.cache: Cache = Cache()
        self.rpc_params: Cache = Cache()

        self.view.setProperty("contentsUrl", "https://github.com/hephy-dd/diode-measurement")
        self.view.setProperty("about", f"<h3>Diode Measurement</h3><p>Version {__version__}</p><p>&copy; 2021-2022 <a href=\"https://hephy.at\">HEPHY.at</a><p>")

        # Controller
        self.ivPlotsController = IVPlotsController(self.view, self)
        self.cvPlotsController = CVPlotsController(self.view, self)
        self.changeVoltageController = ChangeVoltageController(self.view, self.state, self)
        self.requestChangeVoltage.connect(self.changeVoltageController.onRequestChangeVoltage)
        self.failed.connect(self.handleException)
        self.finished.connect(self.saveScreenshot)

        # Source meter unit
        role = self.view.addRole("SMU")
        role.addInstrumentPanel(K237Panel())
        role.addInstrumentPanel(K2410Panel())
        role.addInstrumentPanel(K2470Panel())
        role.addInstrumentPanel(K2657APanel())

        # Electrometer
        role = self.view.addRole("ELM")
        role.addInstrumentPanel(K6514Panel())
        role.addInstrumentPanel(K6517BPanel())

        # LCR meter
        role = self.view.addRole("LCR")
        role.addInstrumentPanel(K595Panel())
        role.addInstrumentPanel(E4980APanel())
        role.addInstrumentPanel(A4284APanel())

        # Temperatur
        role = self.view.addRole("DMM")
        role.addInstrumentPanel(K2700Panel())

        self.view.importAction.triggered.connect(lambda: self.onImportFile())

        self.view.startAction.triggered.connect(self.started)
        self.view.startButton.clicked.connect(self.view.startAction.trigger)

        self.view.stopAction.triggered.connect(self.aborted)
        self.view.stopButton.clicked.connect(self.view.stopAction.trigger)

        self.view.continuousAction.toggled.connect(self.onContinuousToggled)
        self.view.continuousCheckBox.stateChanged.connect(self.onContinuousChanged)

        for spec in DEFAULTS:
            self.view.generalWidget.addMeasurement(spec)
        self.view.generalWidget.measurementComboBox.currentIndexChanged.connect(self.onMeasurementChanged)

        self.view.generalWidget.outputLineEdit.editingFinished.connect(self.onOutputEditingFinished)
        self.view.generalWidget.currentComplianceChanged.connect(self.onCurrentComplianceChanged)
        self.view.generalWidget.continueInComplianceChanged.connect(self.onContinueInComplianceChanged)
        self.view.generalWidget.waitingTimeContinuousChanged.connect(self.onWaitingTimeContinuousChanged)

        self.onMeasurementChanged(0)

        self.update.connect(self.onUpdate)

        self.view.generalWidget.smuCheckBox.toggled.connect(self.onToggleSmu)
        self.view.generalWidget.elmCheckBox.toggled.connect(self.onToggleElm)
        self.view.generalWidget.lcrCheckBox.toggled.connect(self.onToggleLcr)
        self.view.generalWidget.dmmCheckBox.toggled.connect(self.onToggleDmm)

        self.onToggleElm(False)
        self.onToggleLcr(False)
        self.onToggleDmm(False)

        self.view.messageLabel.hide()
        self.view.progressBar.hide()

        # States

        self.idleState = QtCore.QState()
        self.idleState.entered.connect(self.setIdleState)

        self.runningState = QtCore.QState()
        self.runningState.entered.connect(self.setRunningState)

        self.stoppingState = QtCore.QState()
        self.stoppingState.entered.connect(self.setStoppingState)

        # Transitions

        self.idleState.addTransition(self.started, self.runningState)

        self.runningState.addTransition(self.finished, self.idleState)
        self.runningState.addTransition(self.aborted, self.stoppingState)

        self.stoppingState.addTransition(self.finished, self.idleState)

        # State machine

        self.stateMachine = QtCore.QStateMachine()
        self.stateMachine.addState(self.idleState)
        self.stateMachine.addState(self.runningState)
        self.stateMachine.addState(self.stoppingState)
        self.stateMachine.setInitialState(self.idleState)
        self.stateMachine.start()

    def snapshot(self):
        """Return application state snapshot."""
        with self.cache:
            snapshot = {}
            snapshot["state"] = self.cache.get("rpc_state", "idle")
            snapshot["measurement_type"] = self.cache.get("measurement_type")
            snapshot["sample"] = self.cache.get("sample")
            snapshot["source_voltage"] = self.cache.get("source_voltage")
            snapshot["smu_current"] = self.cache.get("smu_current")
            snapshot["elm_current"] = self.cache.get("elm_current")
            snapshot["lcr_capacity"] = self.cache.get("lcr_capacity")
            snapshot["temperature"] = self.cache.get("dmm_temperature")
            return snapshot

    def prepareState(self):
        state = {}

        state["sample"] = self.view.generalWidget.sampleName()
        state["measurement_type"] = self.view.generalWidget.currentMeasurement().get("type")
        state["timestamp"] = time.time()

        state["continuous"] = self.view.isContinuous()
        state["reset"] = self.view.isReset()
        state["auto_reconnect"] = self.view.isAutoReconnect()
        state["save_screenshot"] = self.view.generalWidget.isSaveScreenshot()
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
            state.setdefault(key, {})
            state.get(key).update({
                "resource_name": resource_name,
                "visa_library": visa_library,
                "model": role.resourceWidget.model(),
                "termination": role.resourceWidget.termination(),
                "timeout": role.resourceWidget.timeout()
            })
            state.get(key).update(role.config())

        if self.view.generalWidget.isSMUEnabled():
            state["source"] = "smu"
        elif self.view.generalWidget.isELMEnabled():
            state["source"] = "elm"
        elif self.view.generalWidget.isLCREnabled():
            state["source"] = "lcr"

        state.get("smu").update({"enabled": self.view.generalWidget.isSMUEnabled()})
        state.get("elm").update({"enabled": self.view.generalWidget.isELMEnabled()})
        state.get("lcr").update({"enabled": self.view.generalWidget.isLCREnabled()})
        state.get("dmm").update({"enabled": self.view.generalWidget.isDMMEnabled()})

        for key, value in state.items():
            logger.info("> %s: %s", key, value)

        return state

    def shutdown(self):
        self.stateMachine.stop()
        self.abortRequested.set()
        self.uninstallPlugins()

    @handle_exception
    def loadSettings(self):
        settings = QtCore.QSettings()

        geometry = settings.value("mainwindow/geometry", QtCore.QByteArray(), QtCore.QByteArray)
        if geometry.isEmpty():
            self.view.resize(800, 600)
        else:
            self.view.restoreGeometry(geometry)

        state = settings.value("mainwindow/state", QtCore.QByteArray(), QtCore.QByteArray)
        self.view.restoreState(state)

        continuous = settings.value("continuous", False, bool)
        self.view.setContinuous(continuous)

        reset = settings.value("reset", False, bool)
        self.view.setReset(reset)

        autoReconnect = settings.value("autoReconnect", False, bool)
        self.view.setAutoReconnect(autoReconnect)

        settings.beginGroup("generalTab")

        index = settings.value("measurement/index", 0, int)
        self.view.generalWidget.measurementComboBox.setCurrentIndex(index)

        enabled = settings.value("smu/enabled", False, bool)
        self.view.generalWidget.setSMUEnabled(enabled)

        enabled = settings.value("elm/enabled", False, bool)
        self.view.generalWidget.setELMEnabled(enabled)

        enabled = settings.value("lcr/enabled", False, bool)
        self.view.generalWidget.setLCREnabled(enabled)

        enabled = settings.value("dmm/enabled", False, bool)
        self.view.generalWidget.setDMMEnabled(enabled)

        enabled = settings.value("outputEnabled", False, bool)
        self.view.generalWidget.setOutputEnabled(enabled)

        sample = settings.value("sampleName", "Unnamed")
        self.view.generalWidget.setSampleName(sample)

        path = settings.value("outputDir", os.path.expanduser("~"))
        self.view.generalWidget.setOutputDir(path)

        saveScreenshot = settings.value("saveScreenshot", False, bool)
        self.view.generalWidget.setSaveScreenshot(saveScreenshot)

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

        settings.setValue("mainwindow/geometry", self.view.saveGeometry())
        settings.setValue("mainwindow/state", self.view.saveState())

        continuous = self.view.isContinuous()
        settings.setValue("continuous", continuous)

        reset = self.view.isReset()
        settings.setValue("reset", reset)

        autoReconnect = self.view.isAutoReconnect()
        settings.setValue("autoReconnect", autoReconnect)

        settings.beginGroup("generalTab")

        measurement_index = self.view.generalWidget.measurementComboBox.currentIndex()
        settings.setValue("measurement/index", measurement_index)

        enabled = self.view.generalWidget.isSMUEnabled()
        settings.setValue("smu/enabled", enabled)

        enabled = self.view.generalWidget.isELMEnabled()
        settings.setValue("elm/enabled", enabled)

        enabled = self.view.generalWidget.isLCREnabled()
        settings.setValue("lcr/enabled", enabled)

        enabled = self.view.generalWidget.isDMMEnabled()
        settings.setValue("dmm/enabled", enabled)

        enabled = self.view.generalWidget.isOutputEnabled()
        settings.setValue("outputEnabled", enabled)

        sample = self.view.generalWidget.sampleName()
        settings.setValue("sampleName", sample)

        path = self.view.generalWidget.outputDir()
        settings.setValue("outputDir", path)

        saveScreenshot = self.view.generalWidget.isSaveScreenshot()
        settings.setValue("saveScreenshot", saveScreenshot)

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

    @handle_exception
    def onImportFile(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.view,
            "Select measurement file",
            self.view.generalWidget.outputDir(),
            "Text (*.txt);;All (*);;"
        )
        if filename:
            logger.info("Importing measurement file: %s", filename)
            self.view.setEnabled(False)
            self.view.clear()
            try:
                # Open in binary mode!
                with open(filename, "rb") as fp:
                    reader = Reader(fp)
                    meta = reader.read_meta()
                    data = reader.read_data()
                    continuousData = reader.read_data()

                # Meta
                self.view.generalWidget.measurementComboBox.setCurrentIndex(-1)
                if meta.get("measurement_type"):
                    for index in range(self.view.generalWidget.measurementComboBox.count()):
                        spec = self.view.generalWidget.measurementComboBox.itemData(index)
                        if spec["type"] == meta.get("measurement_type"):
                            self.view.generalWidget.measurementComboBox.setCurrentIndex(index)
                            break
                if meta.get("voltage_begin"):
                    self.view.generalWidget.setBeginVoltage(meta.get("voltage_begin"))
                if meta.get("voltage_end"):
                    self.view.generalWidget.setEndVoltage(meta.get("voltage_end"))
                if meta.get("voltage_step"):
                    self.view.generalWidget.setStepVoltage(meta.get("voltage_step"))
                if meta.get("waiting_time"):
                    self.view.generalWidget.setWaitingTime(meta.get("waiting_time"))
                if meta.get("waiting_time_continuous"):
                    self.view.generalWidget.setWaitingTimeContinuous(meta.get("waiting_time_continuous"))
                if meta.get("current_compliance"):
                    self.view.generalWidget.setCurrentCompliance(meta.get("current_compliance"))

                # Data
                if meta.get("measurement_type") == "iv":
                    self.ivPlotsController.onLoadIVReadings(data)
                    self.ivPlotsController.onLoadItReadings(continuousData)
                if meta.get("measurement_type") == "cv":
                    self.cvPlotsController.onLoadCVReadings(data)
                    self.cvPlotsController.onLoadCV2Readings(data)
            finally:
                self.view.setEnabled(True)

    @handle_exception
    def saveScreenshot(self) -> None:
        """Save screenshot of active IV/CV plots."""
        if self.state.get("save_screenshot"):
            p = pathlib.Path(str(self.state.get("filename")))
            # Only if output file was produced.
            if p.exists():
                filename = str(p.with_suffix(".png"))
                pixmap = self.view.dataStackedWidget.grab()
                pixmap.save(filename, "PNG")
                logger.info("Saved screenshot to %s", filename)

    # State slots

    def setIdleState(self):
        self.view.setIdleState()
        self.view.clearMessage()
        self.view.clearProgress()
        self.updateContinuousOption()
        with self.cache:
            self.cache.clear()
        self.ivPlotsController.updateTimer.stop()
        self.cvPlotsController.updateTimer.stop()

    def setRunningState(self):
        self.view.setRunningState()
        self.view.clear()
        self.startMeasurement()
        self.ivPlotsController.clear()
        self.cvPlotsController.clear()
        self.ivPlotsController.updateTimer.start(500)
        self.cvPlotsController.updateTimer.start(500)

    def setStoppingState(self):
        self.view.setStoppingState()
        self.view.setMessage("Stop requested...")
        self.state.update({"stop_requested": True})

    # Slots

    def handleException(self, exc):
        showException(exc, self.view)

    def onUpdate(self, data):
        cache = {}
        if "rpc_state" in data:
            cache.update({"rpc_state": data.get("rpc_state")})
        if "source_voltage" in data:
            self.view.updateSourceVoltage(data.get("source_voltage"))
            cache.update({"source_voltage": data.get("source_voltage")})
        if "smu_current" in data:
            self.view.updateSMUCurrent(data.get("smu_current"))
            cache.update({"smu_current": data.get("smu_current")})
        if "elm_current" in data:
            self.view.updateELMCurrent(data.get("elm_current"))
            cache.update({"elm_current": data.get("elm_current")})
        if "lcr_capacity" in data:
            self.view.updateLCRCapacity(data.get("lcr_capacity"))
            cache.update({"lcr_capacity": data.get("lcr_capacity")})
        if "dmm_temperature" in data:
            self.view.updateDMMTemperature(data.get("dmm_temperature"))
            cache.update({"dmm_temperature": data.get("dmm_temperature")})
        if "source_output_state" in data:
            self.view.updateSourceOutputState(data.get("source_output_state"))
        if "message" in data:
            self.view.setMessage(data.get("message", ""))
        if "progress" in data:
            self.view.setProgress(*data.get("progress", (0, 0, 0)))
        with self.cache:
            self.cache.update(cache)

    def onContinuousToggled(self, checked):
        self.view.setContinuous(checked)
        self.view.itPlotWidget.setVisible(checked)
        self.view.generalWidget.continuousGroupBox.setEnabled(checked)

    def onContinuousChanged(self, state):
        self.onContinuousToggled(state == QtCore.Qt.Checked)

    def onMeasurementChanged(self, index):
        spec = DEFAULTS[index]

        if spec.get("type") == "iv":
            self.view.showIVPlots()
            self.view.continuousAction.setEnabled(True)
            self.view.generalWidget.continuousGroupBox.setEnabled(self.view.isContinuous())
        elif spec.get("type") == "cv":
            self.view.showCVPlots()
            self.view.continuousAction.setEnabled(False)
            self.view.generalWidget.continuousGroupBox.setEnabled(False)
        self.updateContinuousOption()

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
        self.view.smuGroupBox.setVisible(state)

    def onToggleElm(self, state):
        self.view.ivPlotWidget.elmSeries.setVisible(state)
        self.view.itPlotWidget.elmSeries.setVisible(state)
        self.view.elmGroupBox.setEnabled(state)
        self.view.elmGroupBox.setVisible(state)

    def onToggleLcr(self, state):
        self.view.lcrGroupBox.setEnabled(state)
        self.view.lcrGroupBox.setVisible(state)

    def onToggleDmm(self, state):
        self.view.dmmGroupBox.setEnabled(state)
        self.view.dmmGroupBox.setVisible(state)

    def onOutputEditingFinished(self):
        if not self.view.generalWidget.outputLineEdit.text().strip():
            self.view.generalWidget.outputLineEdit.setText(os.path.expanduser("~"))

    def onCurrentComplianceChanged(self, value):
        logger.info("updated current_compliance: %s", format_metric(value, "A"))
        self.state.update({"current_compliance": value})

    def onContinueInComplianceChanged(self, checked):
        logger.info("updated continue_in_compliance: %s", checked)
        self.state.update({"continue_in_compliance": checked})

    def onWaitingTimeContinuousChanged(self, value):
        logger.info("updated waiting_time_continuous: %s", format_metric(value, "s"))
        self.state.update({"waiting_time_continuous": value})

    def updateContinuousOption(self):
        # Tweak continuous option
        validTypes = ["iv"]
        currentMeasurement = self.view.generalWidget.currentMeasurement()
        enabled = False
        if currentMeasurement:
            measurementType = currentMeasurement.get("type")
            enabled = measurementType in validTypes
        self.view.continuousCheckBox.setEnabled(enabled)

    def createFilename(self):
        path = self.view.generalWidget.outputDir()
        sample = self.state.get("sample")
        timestamp = datetime.fromtimestamp(self.state.get("timestamp", 0)).strftime("%Y-%m-%dT%H-%M-%S")
        filename = safe_filename(f"{sample}-{timestamp}.txt")
        return os.path.join(path, filename)

    def connectIVPlots(self, measurement) -> None:
        measurement.ivReadingQueue = self.ivPlotsController.ivReadingQueue
        measurement.ivReadingLock = self.ivPlotsController.ivReadingLock
        measurement.itReadingQueue = self.ivPlotsController.itReadingQueue
        measurement.itReadingLock = self.ivPlotsController.itReadingLock
        measurement.itChangeVoltageReady.connect(lambda: self.changeVoltageController.onChangeVoltageReady())

    def connectCVPlots(self, measurement) -> None:
        measurement.cvReadingQueue = self.cvPlotsController.cvReadingQueue
        measurement.cvReadingLock = self.cvPlotsController.cvReadingLock

    def createMeasurement(self):
        measurementType = self.state.get("measurement_type")
        measurement = MEASUREMENTS.get(measurementType)(self.state)

        measurement.update.connect(self.update)

        if isinstance(measurement, IVMeasurement):
            self.connectIVPlots(measurement)
        elif isinstance(measurement, CVMeasurement):
            self.connectCVPlots(measurement)

        # Prepare role drivers
        for role in self.view.roles():
            measurement.registerInstrument(role.name().lower())

        measurement.failed.connect(self.handleException)

        return measurement

    def startMeasurement(self) -> None:
        try:
            logger.debug("handle RPC params...")
            with self.rpc_params:
                rpc_params = self.rpc_params
                if "reset" in rpc_params:
                    self.view.setReset(rpc_params.get("reset"))
                if "continuous" in rpc_params:
                    self.view.setContinuous(rpc_params.get("continuous"))
                if "auto_reconnect" in rpc_params:
                    self.view.setAutoReconnect(rpc_params.get("auto_reconnect"))
                if "end_voltage" in rpc_params:
                    self.view.generalWidget.setEndVoltage(rpc_params.get("end_voltage"))
                if "begin_voltage" in rpc_params:
                    self.view.generalWidget.setBeginVoltage(rpc_params.get("begin_voltage"))
                if "step_voltage" in rpc_params:
                    self.view.generalWidget.setStepVoltage(rpc_params.get("step_voltage"))
                if "waiting_time" in rpc_params:
                    self.view.generalWidget.setWaitingTime(rpc_params.get("waiting_time"))
                if "compliance" in rpc_params:
                    self.view.generalWidget.setCurrentCompliance(rpc_params.get("compliance"))
                if "waiting_time_continuous" in rpc_params:
                    self.view.generalWidget.setWaitingTimeContinuous(rpc_params.get("waiting_time_continuous"))
                self.rpc_params.clear()
            logger.debug("handle RPC params... done.")

            logger.debug("preparing state...")
            state = self.prepareState()
            logger.debug("preparing state... done.")

            if not state.get("source"):
                raise RuntimeError("No source instrument selected.")

            # Update state
            self.state.update(state)
            self.state.update({"stop_requested": False})

            with self.cache:
                self.cache.update({
                    "measurement_type": state.get("measurement_type"),
                    "sample": state.get("sample")
                })

            # Filename
            outputEnabled = self.view.generalWidget.isOutputEnabled()
            filename = self.createFilename() if outputEnabled else None
            self.state.update({"filename": filename})

            # Create and run measurement
            measurement = self.createMeasurement()

            self.abortRequested = threading.Event()
            self.measurementThread = threading.Thread(target=self.runMeasurement, args=[measurement])
            self.measurementThread.start()

        except Exception as exc:
            logger.exception(exc)
            self.failed.emit(exc)
            self.aborted.emit()
            self.finished.emit()

    def runMeasurement(self, measurement):
        try:
            MeasurementRunner(measurement)()
        except Exception as exc:
            logger.exception(exc)
            self.failed.emit(exc)
        finally:
            self.finished.emit()


class IVPlotsController(AbstractController):

    def __init__(self, view, parent=None) -> None:
        super().__init__(view, parent)
        self.ivReadingQueue = []
        self.ivReadingLock = threading.RLock()
        self.itReadingQueue = []
        self.itReadingLock = threading.RLock()

        self.updateTimer = QtCore.QTimer()
        self.updateTimer.timeout.connect(self.onFlushIVReadings)
        self.updateTimer.timeout.connect(self.onFlushItReadings)

    def clear(self):
        self.ivReadingQueue.clear()
        self.itReadingQueue.clear()
        self.view.ivPlotWidget.clear()
        self.view.itPlotWidget.clear()

    def onFlushIVReadings(self) -> None:
        with self.ivReadingLock:
            readings = self.ivReadingQueue.copy()
            self.ivReadingQueue.clear()
        for reading in readings:
            self.onIVReading(reading, fit=False)
        if len(readings):
            self.view.ivPlotWidget.fit()

    def onIVReading(self, reading: dict, fit: bool = True) -> None:
        voltage: float = reading.get("voltage", math.nan)
        i_smu: float = reading.get("i_smu", math.nan)
        i_elm: float = reading.get("i_elm", math.nan)
        if math.isfinite(voltage) and math.isfinite(i_smu):
            self.view.ivPlotWidget.append("smu", voltage, i_smu)
        if math.isfinite(voltage) and math.isfinite(i_elm):
            self.view.ivPlotWidget.append("elm", voltage, i_elm)
        if fit:
            self.view.ivPlotWidget.fit()

    def onLoadIVReadings(self, readings: List[dict]) -> None:
        smuPoints = []
        elmPoints = []
        widget = self.view.ivPlotWidget
        widget.clear()
        for reading in readings:
            voltage: float = reading.get("voltage", math.nan)
            i_smu: float = reading.get("i_smu", math.nan)
            i_elm: float = reading.get("i_elm", math.nan)
            if math.isfinite(voltage) and math.isfinite(i_smu):
                smuPoints.append(QtCore.QPointF(voltage, i_smu))
                widget.iLimits.append(i_smu)
                widget.vLimits.append(voltage)
            if math.isfinite(voltage) and math.isfinite(i_elm):
                elmPoints.append(QtCore.QPointF(voltage, i_elm))
                widget.iLimits.append(i_elm)
                widget.vLimits.append(voltage)
        widget.series.get("smu").replace(smuPoints)
        widget.series.get("elm").replace(elmPoints)
        widget.fit()

    def onFlushItReadings(self) -> None:
        with self.itReadingLock:
            readings = self.itReadingQueue.copy()
            self.itReadingQueue.clear()
        for reading in readings:
            self.onItReading(reading, fit=False)
        if len(readings):
            self.view.itPlotWidget.fit()

    def onItReading(self, reading: dict, fit: bool = True) -> None:
        timestamp: float = reading.get("timestamp", math.nan)
        i_smu: float = reading.get("i_smu", math.nan)
        i_elm: float = reading.get("i_elm", math.nan)
        if math.isfinite(timestamp) and math.isfinite(i_smu):
            self.view.itPlotWidget.append("smu", timestamp, i_smu)
        if math.isfinite(timestamp) and math.isfinite(i_elm):
            self.view.itPlotWidget.append("elm", timestamp, i_elm)
        if fit:
            self.view.itPlotWidget.fit()

    def onLoadItReadings(self, readings: List[dict]) -> None:
        smuPoints: List[QtCore.QPointF] = []
        elmPoints: List[QtCore.QPointF] = []
        widget = self.view.itPlotWidget
        widget.clear()
        for reading in readings:
            timestamp: float = reading.get("timestamp", math.nan)
            i_smu: float = reading.get("i_smu", math.nan)
            i_elm: float = reading.get("i_elm", math.nan)
            if math.isfinite(timestamp) and math.isfinite(i_smu):
                smuPoints.append(QtCore.QPointF(timestamp * 1e3, i_smu))
                widget.iLimits.append(i_smu)
                widget.tLimits.append(timestamp)
            if math.isfinite(timestamp) and math.isfinite(i_elm):
                elmPoints.append(QtCore.QPointF(timestamp * 1e3, i_elm))
                widget.iLimits.append(i_elm)
                widget.tLimits.append(timestamp)
        widget.series.get("smu").replace(smuPoints)
        widget.series.get("elm").replace(elmPoints)
        widget.fit()


class CVPlotsController(AbstractController):

    def __init__(self, view, parent=None) -> None:
        super().__init__(view, parent)
        self.cvReadingQueue = []
        self.cvReadingLock = threading.RLock()

        self.updateTimer = QtCore.QTimer()
        self.updateTimer.timeout.connect(self.onFlushCvReadings)

    def clear(self):
        self.cvReadingQueue.clear()
        self.view.cvPlotWidget.clear()

    def onFlushCvReadings(self) -> None:
        with self.cvReadingLock:
            readings = self.cvReadingQueue.copy()
            self.cvReadingQueue.clear()
        for reading in readings:
            self.onCVReading(reading, fit=False)
        if len(readings):
            self.view.cvPlotWidget.fit()

    def onCVReading(self, reading: dict, fit: bool = True) -> None:
        voltage: float = reading.get("voltage", math.nan)
        c_lcr: float = reading.get("c_lcr", math.nan)
        c2_lcr: float = reading.get("c2_lcr", math.nan)
        if math.isfinite(voltage) and math.isfinite(c_lcr):
            self.view.cvPlotWidget.append("lcr", voltage, c_lcr)
        if math.isfinite(voltage) and math.isfinite(c2_lcr):
            self.view.cv2PlotWidget.append("lcr", voltage, c2_lcr)
        if fit:
            self.view.itPlotWidget.fit()

    def onLoadCVReadings(self, readings: List[dict]) -> None:
        lcrPoints: List[QtCore.QPointF] = []
        widget = self.view.cvPlotWidget
        widget.clear()
        for reading in readings:
            voltage: float = reading.get("voltage", math.nan)
            c_lcr: float = reading.get("c_lcr", math.nan)
            if math.isfinite(voltage) and math.isfinite(c_lcr):
                lcrPoints.append(QtCore.QPointF(voltage, c_lcr))
                widget.cLimits.append(c_lcr)
                widget.vLimits.append(voltage)
        widget.series.get("lcr").replace(lcrPoints)
        widget.fit()

    def onLoadCV2Readings(self, readings: List[dict]) -> None:
        lcr2Points: List[QtCore.QPointF] = []
        widget = self.view.cv2PlotWidget
        widget.clear()
        for reading in readings:
            voltage: float = reading.get("voltage", math.nan)
            c2_lcr: float = reading.get("c2_lcr", math.nan)
            if math.isfinite(voltage) and math.isfinite(c2_lcr):
                lcr2Points.append(QtCore.QPointF(voltage, c2_lcr))
                widget.cLimits.append(c2_lcr)
                widget.vLimits.append(voltage)
        widget.series.get("lcr").replace(lcr2Points)
        widget.fit()


class ChangeVoltageController(AbstractController):

    def __init__(self, view, state, parent=None) -> None:
        super().__init__(view, parent)
        self.state = state
        # Connect signals
        self.view.prepareChangeVoltage.connect(self.onPrepareChangeVoltage)

    def sourceVoltage(self):
        if self.state.get("source_voltage") is not None:
            return self.state.get("source_voltage")
        return self.view.generalWidget.endVoltage()

    def onPrepareChangeVoltage(self) -> None:
        dialog = ChangeVoltageDialog(self.view)
        dialog.setEndVoltage(self.sourceVoltage())
        dialog.setStepVoltage(self.view.generalWidget.stepVoltage())
        dialog.setWaitingTime(self.view.generalWidget.waitingTime())
        dialog.exec()
        if dialog.result() == dialog.Accepted:
            self.onRequestChangeVoltage(
                dialog.endVoltage(),
                dialog.stepVoltage(),
                dialog.waitingTime()
            )

    def onRequestChangeVoltage(self, endVoltage: float, stepVoltage: float, waitingTime: float) -> None:
        if self.view.isChangeVoltageEnabled():
            logger.info(
                "updated change_voltage_continuous: end_voltage=%s, step_voltage=%s, waiting_time=%s",
                format_metric(endVoltage, "V"),
                format_metric(stepVoltage, "V"),
                format_metric(waitingTime, "s")
            )
            self.state.update({"change_voltage_continuous": {
                "end_voltage": endVoltage,
                "step_voltage": stepVoltage,
                "waiting_time": waitingTime
            }})
            self.view.setChangeVoltageEnabled(False)

    def onChangeVoltageReady(self) -> None:
        self.view.setChangeVoltageEnabled(True)
