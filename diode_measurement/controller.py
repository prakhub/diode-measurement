import os
import math
import time
import logging
import threading
import contextlib
from datetime import datetime

from typing import List, Union

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
from .ui.panels import E4285Panel
from .ui.panels import E4980APanel

from .ui.widgets import showException
from .ui.dialogs import ChangeVoltageDialog

from .measurement import IVMeasurement
from .measurement import CVMeasurement

from .reader import Reader
from .writer import Writer

from .utils import get_resource
from .utils import safe_filename
from .utils import format_metric

from .settings import SPECS

logger = logging.getLogger(__name__)


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
    itChangeVoltageReady = QtCore.pyqtSignal()

    def __init__(self, view):
        super().__init__()
        self.measurementThread: threading.Thread = None

        self.view = view
        self.view.setProperty("contentsUrl", "https://github.com/hephy-dd/diode-measurement")
        self.view.setProperty("about", f"<h3>Diode Measurement</h3><p>Version {__version__}</p><p>&copy; 2021 <a href=\"https://hephy.at\">HEPHY.at</a><p>")

        # Source meter unit
        role = self.view.addRole("SMU")
        role.addInstrument(K237Panel())
        role.addInstrument(K2410Panel())
        role.addInstrument(K2470Panel())
        role.addInstrument(K2657APanel())

        # Electrometer
        role = self.view.addRole("ELM")
        role.addInstrument(K6514Panel())
        role.addInstrument(K6517BPanel())

        # LCR meter
        role = self.view.addRole("LCR")
        role.addInstrument(K595Panel())
        # TODO
        # role.addInstrument(E4285Panel())
        role.addInstrument(E4980APanel())

        # Temperatur
        # role = self.view.addRole("Temperature")

        self.state = {}

        self.view.importAction.triggered.connect(lambda: self.onImportFile())

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
        self.view.generalWidget.changeVoltageContinuousRequested.connect(self.onChangeVoltageRequested)

        self.view.unlock()
        self.onMeasurementChanged(0)

        self.finished.connect(self.onFinished)
        self.failed.connect(self.onFailed)
        self.update.connect(self.onUpdate)
        self.itChangeVoltageReady.connect(self.onChangeVoltageReady)

        self.view.generalWidget.smuCheckBox.toggled.connect(self.onToggleSmu)
        self.view.generalWidget.elmCheckBox.toggled.connect(self.onToggleElm)
        self.view.generalWidget.lcrCheckBox.toggled.connect(self.onToggleLcr)

        self.view.messageLabel.hide()
        self.view.progressBar.hide()

        self.ivPlotsController = IVPlotsController(self.view, self)
        self.cvPlotsController = CVPlotsController(self.view, self)

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

        enabled = settings.value("outputEnabled", False, bool)
        self.view.generalWidget.setOutputEnabled(enabled)

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

        enabled = self.view.generalWidget.isOutputEnabled()
        settings.setValue("outputEnabled", enabled)

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
            self.view.lock()
            self.view.clear()
            try:
                # Open in binary mode!
                with open(filename, 'rb') as fp:
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
                self.view.unlock()

    def onStart(self):
        try:
            self.view.lock()
            self.view.clear()
            self.startMeasurement()
        except Exception as exc:
            logger.exception(exc)
            self.onFailed(exc)
            self.onFinished()

    def onStop(self):
        self.state.update({"stop_requested": True})
        self.view.setMessage("Stop requested...")

    def onFinished(self):
        self.view.unlock()
        self.view.setMessage("")
        self.view.messageLabel.hide()
        self.view.progressBar.hide()
        self.updateContinuousOption()

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

    def onContinuousToggled(self, checked):
        self.view.setContinuous(checked)
        self.view.itPlotWidget.setVisible(checked)
        self.view.generalWidget.continuousGroupBox.setEnabled(checked)

    def onContinuousChanged(self, state):
        self.onContinuousToggled(state == QtCore.Qt.Checked)

    def onMeasurementChanged(self, index):
        spec = SPECS[index]

        if spec.get("type") == "iv":
            self.view.raiseIVTab()
            self.view.continuousAction.setEnabled(True)
            self.view.generalWidget.continuousGroupBox.setEnabled(self.view.isContinuous())
        elif spec.get("type") == "cv":
            self.view.raiseCVTab()
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

    def onToggleElm(self, state):
        self.view.ivPlotWidget.elmSeries.setVisible(state)
        self.view.itPlotWidget.elmSeries.setVisible(state)
        self.view.elmGroupBox.setEnabled(state)

    def onToggleLcr(self, state):
        self.view.lcrGroupBox.setEnabled(state)

    def onOutputEditingFinished(self):
        if not self.view.generalWidget.outputLineEdit.text().strip():
            self.view.generalWidget.outputLineEdit.setText(os.path.expanduser("~"))

    def onCurrentComplianceChanged(self, value):
        logging.info("updated current_compliance: %s", format_metric(value, 'A'))
        self.state.update({"current_compliance": value})

    def onContinueInComplianceChanged(self, checked):
        logging.info("updated continue_in_compliance: %s", checked)
        self.state.update({"continue_in_compliance": checked})

    def onWaitingTimeContinuousChanged(self, value):
        logging.info("updated waiting_time_continuous: %s", format_metric(value, 's'))
        self.state.update({"waiting_time_continuous": value})

    def onChangeVoltageReady(self):
        self.view.generalWidget.changeVoltageButton.setEnabled(True)

    def onChangeVoltageRequested(self):
        dialog = ChangeVoltageDialog(self.view)
        dialog.setEndVoltage(self.sourceVoltage())
        dialog.setStepVoltage(self.view.generalWidget.stepVoltage())
        dialog.setWaitingTime(self.view.generalWidget.waitingTime())
        dialog.exec()
        if dialog.result() == dialog.Accepted:
            logging.info("updated change_voltage_continuous: %s", format_metric(dialog.endVoltage(), 'V'))
            self.state.update({"change_voltage_continuous": {
                "end_voltage": dialog.endVoltage(),
                "step_voltage": dialog.stepVoltage(),
                "waiting_time": dialog.waitingTime()
            }})

    def updateContinuousOption(self):
        # Tweak continous option
        validTypes = ["iv"]
        currentMeasurement = self.view.generalWidget.currentMeasurement()
        enabled = False
        if currentMeasurement:
            measurementType = currentMeasurement.get("type")
            enabled = measurementType in validTypes
        self.view.continuousCheckBox.setEnabled(enabled)

    def sourceVoltage(self):
        if self.state.get('source_voltage') is not None:
            return self.state.get('source_voltage')
        return self.view.generalWidget.endVoltage()

    def createFilename(self):
        path = self.view.generalWidget.outputDir()
        sample = self.state.get('sample')
        timestamp = datetime.fromtimestamp(self.state.get('timestamp', 0)).strftime("%Y-%m-%dT%H-%M-%S")
        filename = safe_filename(f"{sample}-{timestamp}.txt")
        return os.path.join(path, filename)

    def connectIVPlots(self, measurement) -> None:
        measurement.ivReading.connect(lambda reading: self.ivPlotsController.ivReading.emit(reading))
        measurement.itReading.connect(lambda reading: self.ivPlotsController.itReading.emit(reading))
        measurement.itChangeVoltageReady.connect(lambda: self.itChangeVoltageReady.emit())

    def connectCVPlots(self, measurement) -> None:
        measurement.cvReading.connect(lambda reading: self.cvPlotsController.cvReading.emit(reading))

    def createMeasurement(self):
        measurements = {
            "iv": IVMeasurement,
            "cv": CVMeasurement,
        }
        measurementType = self.state.get("measurement_type")
        measurement = measurements.get(measurementType)(self.state)

        measurement.update.connect(lambda data: self.update.emit(data))

        if isinstance(measurement, IVMeasurement):
            self.connectIVPlots(measurement)
        elif isinstance(measurement, CVMeasurement):
            self.connectCVPlots(measurement)

        # Prepare role drivers
        for role in self.view.roles():
            measurement.prepareDriver(role.name().lower())

        return measurement

    def startMeasurement(self) -> None:
        state = self.prepareState()

        if not state.get("source"):
            raise RuntimeError("No source instrument selected.")

        # Update state
        self.state.update(state)
        self.state.update({"stop_requested": False})

        # Filename
        outputEnabled = self.view.generalWidget.isOutputEnabled()
        filename = self.createFilename() if outputEnabled else None
        self.state.update({"filename": filename})

        # Create and run measurement
        measurement = self.createMeasurement()
        self.measurementThread = threading.Thread(target=self._runMeasurement, args=[measurement])
        self.measurementThread.start()

    def _runMeasurement(self, measurement) -> None:
        try:
            filename = measurement.state.get("filename")
            with contextlib.ExitStack() as stack:
                if filename:
                    def createOutputDir(filename):
                        path = os.path.dirname(filename)
                        if not os.path.exists(path):
                            os.makedirs(path)
                    measurement.startedHandlers.append(lambda: createOutputDir(filename))
                    fp = stack.enter_context(open(filename, 'w', newline=''))
                    writer = Writer(fp)
                    # Note: using signals executes slots in main thread, shoyld be this thread
                    measurement.startedHandlers.append(lambda: writer.write_meta(measurement.state))
                    if isinstance(measurement, IVMeasurement):
                        measurement.ivReadingHandlers.append(lambda reading: writer.write_iv_row(reading))
                        measurement.itReadingHandlers.append(lambda reading: writer.write_it_row(reading))
                    if isinstance(measurement, CVMeasurement):
                        measurement.cvReadingHandlers.append(lambda reading: writer.write_cv_row(reading))
                    measurement.finishedHandlers.append(lambda: writer.flush())
                measurement.run()
        except Exception as exc:
            logger.exception(exc)
            self.failed.emit(exc)
        finally:
            self.finished.emit()


class IVPlotsController(QtCore.QObject):

    ivReading = QtCore.pyqtSignal(dict)
    itReading = QtCore.pyqtSignal(dict)

    def __init__(self, view, parent=None) -> None:
        super().__init__(parent)
        self.view = view
        self.ivReading.connect(self.onIVReading)
        self.itReading.connect(self.onItReading)

    def onIVReading(self, reading: dict) -> None:
        voltage: float = reading.get('voltage', math.nan)
        i_smu: float = reading.get('i_smu', math.nan)
        i_elm: float = reading.get('i_elm', math.nan)
        if math.isfinite(voltage) and math.isfinite(i_smu):
            self.view.ivPlotWidget.append('smu', voltage, i_smu)
        if math.isfinite(voltage) and math.isfinite(i_elm):
            self.view.ivPlotWidget.append('elm', voltage, i_elm)

    def onLoadIVReadings(self, readings: List[dict]) -> None:
        smuPoints = []
        elmPoints = []
        widget = self.view.ivPlotWidget
        widget.clear()
        for reading in readings:
            voltage: float = reading.get('voltage', math.nan)
            i_smu: float = reading.get('i_smu', math.nan)
            i_elm: float = reading.get('i_elm', math.nan)
            if math.isfinite(voltage) and math.isfinite(i_smu):
                smuPoints.append(QtCore.QPointF(voltage, i_smu))
                widget.iLimits.append(i_smu)
                widget.vLimits.append(voltage)
            if math.isfinite(voltage) and math.isfinite(i_elm):
                elmPoints.append(QtCore.QPointF(voltage, i_elm))
                widget.iLimits.append(i_elm)
                widget.vLimits.append(voltage)
        widget.series.get('smu').replace(smuPoints)
        widget.series.get('elm').replace(elmPoints)
        widget.fit()

    def onItReading(self, reading: dict, fit: bool = True) -> None:
        timestamp: float = reading.get('timestamp', math.nan)
        i_smu: float = reading.get('i_smu', math.nan)
        i_elm: float = reading.get('i_elm', math.nan)
        if math.isfinite(timestamp) and math.isfinite(i_smu):
            self.view.itPlotWidget.append('smu', timestamp, i_smu)
        if math.isfinite(timestamp) and math.isfinite(i_elm):
            self.view.itPlotWidget.append('elm', timestamp, i_elm)
        if fit:
            self.view.itPlotWidget.fit()

    def onLoadItReadings(self, readings: List[dict]) -> None:
        smuPoints: List[QtCore.QPointF] = []
        elmPoints: List[QtCore.QPointF] = []
        widget = self.view.itPlotWidget
        widget.clear()
        for reading in readings:
            timestamp: float = reading.get('timestamp', math.nan)
            i_smu: float = reading.get('i_smu', math.nan)
            i_elm: float = reading.get('i_elm', math.nan)
            if math.isfinite(timestamp) and math.isfinite(i_smu):
                smuPoints.append(QtCore.QPointF(timestamp * 1e3, i_smu))
                widget.iLimits.append(i_smu)
                widget.tLimits.append(timestamp)
            if math.isfinite(timestamp) and math.isfinite(i_elm):
                elmPoints.append(QtCore.QPointF(timestamp * 1e3, i_elm))
                widget.iLimits.append(i_elm)
                widget.tLimits.append(timestamp)
        widget.series.get('smu').replace(smuPoints)
        widget.series.get('elm').replace(elmPoints)
        widget.fit()


class CVPlotsController(QtCore.QObject):

    cvReading = QtCore.pyqtSignal(dict)

    def __init__(self, view, parent=None) -> None:
        super().__init__(parent)
        self.view = view
        self.cvReading.connect(self.onCVReading)

    def onCVReading(self, reading: dict) -> None:
        voltage: float = reading.get('voltage', math.nan)
        c_lcr: float = reading.get('c_lcr', math.nan)
        c2_lcr: float = reading.get('c2_lcr', math.nan)
        if math.isfinite(voltage) and math.isfinite(c_lcr):
            self.view.cvPlotWidget.append('lcr', voltage, c_lcr)
        if math.isfinite(voltage) and math.isfinite(c2_lcr):
            self.view.cv2PlotWidget.append('lcr', voltage, c2_lcr)

    def onLoadCVReadings(self, readings: List[dict]) -> None:
        lcrPoints: List[QtCore.QPointF] = []
        widget = self.view.cvPlotWidget
        widget.clear()
        for reading in readings:
            voltage: float = reading.get('voltage', math.nan)
            c_lcr: float = reading.get('c_lcr', math.nan)
            if math.isfinite(voltage) and math.isfinite(c_lcr):
                lcrPoints.append(QtCore.QPointF(voltage, c_lcr))
                widget.cLimits.append(c_lcr)
                widget.vLimits.append(voltage)
        widget.series.get('lcr').replace(lcrPoints)
        widget.fit()

    def onLoadCV2Readings(self, readings: List[dict]) -> None:
        lcr2Points: List[QtCore.QPointF] = []
        widget = self.view.cv2PlotWidget
        widget.clear()
        for reading in readings:
            voltage: float = reading.get('voltage', math.nan)
            c2_lcr: float = reading.get('c2_lcr', math.nan)
            if math.isfinite(voltage) and math.isfinite(c2_lcr):
                lcr2Points.append(QtCore.QPointF(voltage, c2_lcr))
                widget.cLimits.append(c2_lcr)
                widget.vLimits.append(voltage)
        widget.series.get('lcr').replace(lcr2Points)
        widget.fit()
