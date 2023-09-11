from typing import Any, Dict

from PyQt5 import QtWidgets

from ..utils import ureg
from .metric import MetricWidget

__all__ = [
    "K237Panel",
    "K595Panel",
    "K2410Panel",
    "K2470Panel",
    "K2657APanel",
    "K2700Panel",
    "K6514Panel",
    "K6517BPanel",
    "A4284APanel",
    "E4980APanel",
    "BrandBoxPanel",
]

ConfigType = Dict[str, Any]


class WidgetParameter:

    def __init__(self, widget) -> None:
        self.widget = widget

    def value(self) -> Any:
        widget = self.widget
        if isinstance(widget, QtWidgets.QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QtWidgets.QLineEdit):
            return widget.text()
        elif isinstance(widget, QtWidgets.QSpinBox):
            return widget.value()
        elif isinstance(widget, QtWidgets.QDoubleSpinBox):
            return widget.value()
        elif isinstance(widget, QtWidgets.QComboBox):
            return widget.currentData()
        elif isinstance(widget, MetricWidget):
            return widget.value()
        raise TypeError(f"Invalid widget type: {repr(widget)}")

    def setValue(self, value: Any) -> None:
        widget = self.widget
        if isinstance(widget, QtWidgets.QCheckBox):
            widget.setChecked(value)
        elif isinstance(widget, QtWidgets.QLineEdit):
            widget.setText(value)
        elif isinstance(widget, QtWidgets.QSpinBox):
            widget.setValue(value)
        elif isinstance(widget, QtWidgets.QDoubleSpinBox):
            widget.setValue(value)
        elif isinstance(widget, QtWidgets.QComboBox):
            index = widget.findData(value)
            widget.setCurrentIndex(index)
        elif isinstance(widget, MetricWidget):
            widget.setValue(value)
        else:
            raise TypeError(f"Invalid widget type: {repr(widget)}")


class MethodParameter:

    def __init__(self, getter, setter) -> None:
        self.getter = getter
        self.setter = setter

    def value(self) -> Any:
        return self.getter()

    def setValue(self, value: Any) -> None:
        self.setter(value)


class InstrumentPanel(QtWidgets.QWidget):

    def __init__(self, model: str, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self._parameters: Dict[str, Any] = {}
        self.setModel(model)

    def model(self) -> str:
        return self.property("model")

    def setModel(self, model: str) -> None:
        self.setProperty("model", model)

    def restoreDefaults(self) -> None:
        ...

    def setLocked(self, state: bool) -> None:
        ...

    def bindParameter(self, key: str, parameter: Any) -> None:
        if key in self._parameters:
            raise KeyError(f"Parameter already exists: {repr(key)}")
        self._parameters[key] = parameter

    def config(self) -> ConfigType:
        config: ConfigType = {}
        for key, parameter in self._parameters.items():
            config[key] = parameter.value()
        return config

    def setConfig(self, config: ConfigType) -> None:
        for key, value in config.items():
            parameter = self._parameters.get(key)
            if parameter is None:
                raise KeyError(f"No such parameter: {repr(key)}")
            parameter.setValue(value)


class K237Panel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("K237", parent)

        # Filter

        self.filterGroupBox = QtWidgets.QGroupBox()
        self.filterGroupBox.setTitle("Filter")

        self.filterModeLabel = QtWidgets.QLabel("Mode")

        self.filterModeComboBox = QtWidgets.QComboBox()
        self.filterModeComboBox.addItem("Disabled", 0)
        self.filterModeComboBox.addItem("2-readings", 1)
        self.filterModeComboBox.addItem("4-readings", 2)
        self.filterModeComboBox.addItem("8-readings", 3)
        self.filterModeComboBox.addItem("16-readings", 4)
        self.filterModeComboBox.addItem("32-readings", 5)

        filterLayout = QtWidgets.QVBoxLayout(self.filterGroupBox)
        filterLayout.addWidget(self.filterModeLabel)
        filterLayout.addWidget(self.filterModeComboBox)
        filterLayout.addStretch()

        # Layout

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.filterGroupBox)
        layout.addStretch()
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        # Parameters

        self.bindParameter("filter.mode", WidgetParameter(self.filterModeComboBox))

        self.restoreDefaults()

    def restoreDefaults(self) -> None:
        self.filterModeComboBox.setCurrentIndex(0)

    def setLocked(self, state: bool) -> None:
        self.filterModeComboBox.setEnabled(not state)


class K595Panel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("K595", parent)


class K2410Panel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("K2410", parent)

        # Filter

        self.filterGroupBox = QtWidgets.QGroupBox()
        self.filterGroupBox.setTitle("Filter")
        self.filterEnableCheckBox = QtWidgets.QCheckBox("Enabled")

        self.filterCountLabel = QtWidgets.QLabel("Count")

        self.filterCountSpinBox = QtWidgets.QSpinBox()
        self.filterCountSpinBox.setSingleStep(1)
        self.filterCountSpinBox.setRange(2, 100)

        self.filterModeLabel = QtWidgets.QLabel("Mode")

        self.filterModeComboBox = QtWidgets.QComboBox()
        self.filterModeComboBox.addItem("Repeat", "REP")
        self.filterModeComboBox.addItem("Moving", "MOV")

        filterLayout = QtWidgets.QVBoxLayout(self.filterGroupBox)
        filterLayout.addWidget(self.filterEnableCheckBox)
        filterLayout.addWidget(self.filterCountLabel)
        filterLayout.addWidget(self.filterCountSpinBox)
        filterLayout.addWidget(self.filterModeLabel)
        filterLayout.addWidget(self.filterModeComboBox)
        filterLayout.addStretch()

        # Integration Time

        self.integrationTimeGroupBox = QtWidgets.QGroupBox()
        self.integrationTimeGroupBox.setTitle("Integration Time")

        self.nplcLabel = QtWidgets.QLabel("NPLC")

        self.nplcSpinBox = QtWidgets.QDoubleSpinBox()
        self.nplcSpinBox.setStatusTip("Number of Power Line Cycles (0.01 to 10)")
        self.nplcSpinBox.setRange(0.01, 10.0)
        self.nplcSpinBox.setDecimals(2)
        self.nplcSpinBox.setSingleStep(0.1)
        self.nplcSpinBox.setStepType(QtWidgets.QDoubleSpinBox.AdaptiveDecimalStepType)

        integrationTimeLayout = QtWidgets.QVBoxLayout(self.integrationTimeGroupBox)
        integrationTimeLayout.addWidget(self.nplcLabel)
        integrationTimeLayout.addWidget(self.nplcSpinBox)

        # Route terminals

        self.routeTerminalsGroupBox = QtWidgets.QGroupBox()
        self.routeTerminalsGroupBox.setTitle("Route Terminals")

        self.routeTerminalsComboBox = QtWidgets.QComboBox()
        self.routeTerminalsComboBox.addItem("Front", "FRON")
        self.routeTerminalsComboBox.addItem("Rear", "REAR")

        routeTerminalsLayout = QtWidgets.QVBoxLayout(self.routeTerminalsGroupBox)
        routeTerminalsLayout.addWidget(self.routeTerminalsComboBox)
        routeTerminalsLayout.addStretch()

        # Layout

        leftLayout = QtWidgets.QVBoxLayout()
        leftLayout.addWidget(self.filterGroupBox)

        rightLayout = QtWidgets.QVBoxLayout()
        rightLayout.addWidget(self.integrationTimeGroupBox)
        rightLayout.addWidget(self.routeTerminalsGroupBox)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(leftLayout)
        layout.addLayout(rightLayout)
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        # Parameters

        self.bindParameter("filter.enable", WidgetParameter(self.filterEnableCheckBox))
        self.bindParameter("filter.count", WidgetParameter(self.filterCountSpinBox))
        self.bindParameter("filter.mode", WidgetParameter(self.filterModeComboBox))
        self.bindParameter("nplc", WidgetParameter(self.nplcSpinBox))
        self.bindParameter("route.terminals", WidgetParameter(self.routeTerminalsComboBox))

        self.restoreDefaults()

    def restoreDefaults(self) -> None:
        self.filterEnableCheckBox.setChecked(False)
        self.filterCountSpinBox.setValue(10)
        self.filterModeComboBox.setCurrentIndex(0)
        self.nplcSpinBox.setValue(1.0)
        self.routeTerminalsComboBox.setCurrentIndex(0)

    def setLocked(self, state: bool) -> None:
        self.filterEnableCheckBox.setEnabled(not state)
        self.filterCountSpinBox.setEnabled(not state)
        self.filterModeComboBox.setEnabled(not state)
        self.nplcSpinBox.setEnabled(not state)
        self.routeTerminalsComboBox.setEnabled(not state)


class K2470Panel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("K2470", parent)

        # Filter

        self.filterGroupBox = QtWidgets.QGroupBox()
        self.filterGroupBox.setTitle("Filter")
        self.filterEnableCheckBox = QtWidgets.QCheckBox("Enabled")

        self.filterCountLabel = QtWidgets.QLabel("Count")

        self.filterCountSpinBox = QtWidgets.QSpinBox()
        self.filterCountSpinBox.setSingleStep(1)
        self.filterCountSpinBox.setRange(2, 100)

        self.filterModeLabel = QtWidgets.QLabel("Mode")

        self.filterModeComboBox = QtWidgets.QComboBox()
        self.filterModeComboBox.addItem("Repeat", "REP")
        self.filterModeComboBox.addItem("Moving", "MOV")

        filterLayout = QtWidgets.QVBoxLayout(self.filterGroupBox)
        filterLayout.addWidget(self.filterEnableCheckBox)
        filterLayout.addWidget(self.filterCountLabel)
        filterLayout.addWidget(self.filterCountSpinBox)
        filterLayout.addWidget(self.filterModeLabel)
        filterLayout.addWidget(self.filterModeComboBox)
        filterLayout.addStretch()

        # Integration Time

        self.integrationTimeGroupBox = QtWidgets.QGroupBox()
        self.integrationTimeGroupBox.setTitle("Integration Time")

        self.nplcLabel = QtWidgets.QLabel("NPLC")

        self.nplcSpinBox = QtWidgets.QDoubleSpinBox()
        self.nplcSpinBox.setStatusTip("Number of Power Line Cycles (0.01 to 10)")
        self.nplcSpinBox.setRange(0.01, 10.0)
        self.nplcSpinBox.setDecimals(2)
        self.nplcSpinBox.setSingleStep(0.1)
        self.nplcSpinBox.setStepType(QtWidgets.QDoubleSpinBox.AdaptiveDecimalStepType)

        integrationTimeLayout = QtWidgets.QVBoxLayout(self.integrationTimeGroupBox)
        integrationTimeLayout.addWidget(self.nplcLabel)
        integrationTimeLayout.addWidget(self.nplcSpinBox)

        # Route Terminals

        self.routeTerminalsComboBox = QtWidgets.QComboBox()
        self.routeTerminalsComboBox.addItem("Front", "FRON")
        self.routeTerminalsComboBox.addItem("Rear", "REAR")

        self.routeTerminalsGroupBox = QtWidgets.QGroupBox()
        self.routeTerminalsGroupBox.setTitle("Route Terminals")

        routeTerminalsLayout = QtWidgets.QVBoxLayout(self.routeTerminalsGroupBox)
        routeTerminalsLayout.addWidget(self.routeTerminalsComboBox)

        # System

        self.systemGroupBox = QtWidgets.QGroupBox()
        self.systemGroupBox.setTitle("System")

        self.breakdownProtectionCheckBox = QtWidgets.QCheckBox("Breakdown Protection")

        systemLayout = QtWidgets.QVBoxLayout(self.systemGroupBox)
        systemLayout.addWidget(self.breakdownProtectionCheckBox)
        systemLayout.addStretch()

        # Layout

        leftLayout = QtWidgets.QVBoxLayout()
        leftLayout.addWidget(self.filterGroupBox)

        rightLayout = QtWidgets.QVBoxLayout()
        rightLayout.addWidget(self.integrationTimeGroupBox)
        rightLayout.addWidget(self.routeTerminalsGroupBox)
        rightLayout.addWidget(self.systemGroupBox)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(leftLayout)
        layout.addLayout(rightLayout)
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        self.bindParameter("filter.enable", WidgetParameter(self.filterEnableCheckBox))
        self.bindParameter("filter.count", WidgetParameter(self.filterCountSpinBox))
        self.bindParameter("filter.mode", WidgetParameter(self.filterModeComboBox))
        self.bindParameter("nplc", WidgetParameter(self.nplcSpinBox))
        self.bindParameter("route.terminals", WidgetParameter(self.routeTerminalsComboBox))
        self.bindParameter("system.breakdown.protection", WidgetParameter(self.breakdownProtectionCheckBox))

        self.restoreDefaults()

    def restoreDefaults(self) -> None:
        self.filterEnableCheckBox.setChecked(False)
        self.filterCountSpinBox.setValue(10)
        self.filterModeComboBox.setCurrentIndex(0)
        self.nplcSpinBox.setValue(1.0)
        self.routeTerminalsComboBox.setCurrentIndex(0)
        self.breakdownProtectionCheckBox.setChecked(False)

    def setLocked(self, state: bool) -> None:
        self.filterEnableCheckBox.setEnabled(not state)
        self.filterCountSpinBox.setEnabled(not state)
        self.filterModeComboBox.setEnabled(not state)
        self.nplcSpinBox.setEnabled(not state)
        self.routeTerminalsComboBox.setEnabled(not state)
        self.breakdownProtectionCheckBox.setEnabled(not state)


class K2657APanel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("K2657A", parent)

        self.filterGroupBox = QtWidgets.QGroupBox()
        self.filterGroupBox.setTitle("Filter")
        self.filterEnableCheckBox = QtWidgets.QCheckBox("Enabled")

        self.filterCountLabel = QtWidgets.QLabel("Count")

        self.filterCountSpinBox = QtWidgets.QSpinBox()
        self.filterCountSpinBox.setSingleStep(1)
        self.filterCountSpinBox.setRange(2, 100)

        self.filterModeLabel = QtWidgets.QLabel("Mode")

        self.filterModeComboBox = QtWidgets.QComboBox()
        self.filterModeComboBox.addItem("Repeat", "REPEAT_AVG")
        self.filterModeComboBox.addItem("Moving", "MOVING_AVG")
        self.filterModeComboBox.addItem("Median", "MEDIAN")

        filterLayout = QtWidgets.QVBoxLayout(self.filterGroupBox)
        filterLayout.addWidget(self.filterEnableCheckBox)
        filterLayout.addWidget(self.filterCountLabel)
        filterLayout.addWidget(self.filterCountSpinBox)
        filterLayout.addWidget(self.filterModeLabel)
        filterLayout.addWidget(self.filterModeComboBox)
        filterLayout.addStretch()

        # Integration Time

        self.integrationTimeGroupBox = QtWidgets.QGroupBox()
        self.integrationTimeGroupBox.setTitle("Integration Time")

        self.nplcLabel = QtWidgets.QLabel("NPLC")

        self.nplcSpinBox = QtWidgets.QDoubleSpinBox()
        self.nplcSpinBox.setStatusTip("Number of Power Line Cycles (0.001 to 25)")
        self.nplcSpinBox.setRange(0.001, 25.0)
        self.nplcSpinBox.setDecimals(3)
        self.nplcSpinBox.setSingleStep(0.1)
        self.nplcSpinBox.setStepType(QtWidgets.QDoubleSpinBox.AdaptiveDecimalStepType)

        integrationTimeLayout = QtWidgets.QVBoxLayout(self.integrationTimeGroupBox)
        integrationTimeLayout.addWidget(self.nplcLabel)
        integrationTimeLayout.addWidget(self.nplcSpinBox)
        integrationTimeLayout.addStretch()

        # Layout

        leftLayout = QtWidgets.QVBoxLayout()
        leftLayout.addWidget(self.filterGroupBox)
        leftLayout.addWidget(self.integrationTimeGroupBox)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(leftLayout)
        layout.addStretch()
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        self.bindParameter("filter.enable", WidgetParameter(self.filterEnableCheckBox))
        self.bindParameter("filter.count", WidgetParameter(self.filterCountSpinBox))
        self.bindParameter("filter.mode", WidgetParameter(self.filterModeComboBox))
        self.bindParameter("nplc", WidgetParameter(self.nplcSpinBox))

        self.restoreDefaults()

    def restoreDefaults(self) -> None:
        self.filterEnableCheckBox.setChecked(False)
        self.filterCountSpinBox.setValue(10)
        self.filterModeComboBox.setCurrentIndex(0)
        self.nplcSpinBox.setValue(1.0)

    def setLocked(self, state: bool) -> None:
        self.filterEnableCheckBox.setEnabled(not state)
        self.filterCountSpinBox.setEnabled(not state)
        self.filterModeComboBox.setEnabled(not state)
        self.nplcSpinBox.setEnabled(not state)


class K2700Panel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("K2700", parent)


class K6514Panel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("K6514", parent)

        # Range

        self.rangeGroupBox = QtWidgets.QGroupBox()
        self.rangeGroupBox.setTitle("Sense Range")

        self.senseRangeMetric = MetricWidget()
        self.senseRangeMetric.setDecimals(3)
        self.senseRangeMetric.setRange(0, 999)  # TODO
        self.senseRangeMetric.setUnit("A")
        self.senseRangeMetric.setPrefixes("munp")

        self.autoRangeLLimitLabel = QtWidgets.QLabel("Lower Limit")

        self.autoRangeLLimitMetric = MetricWidget()
        self.autoRangeLLimitMetric.setDecimals(3)
        self.autoRangeLLimitMetric.setRange(0, 999)  # TODO
        self.autoRangeLLimitMetric.setUnit("A")
        self.autoRangeLLimitMetric.setPrefixes("munp")

        self.autoRangeULimitLabel = QtWidgets.QLabel("Upper Limit")

        self.autoRangeULimitMetric = MetricWidget()
        self.autoRangeULimitMetric.setDecimals(3)
        self.autoRangeULimitMetric.setRange(0, 999)  # TODO
        self.autoRangeULimitMetric.setUnit("A")
        self.autoRangeULimitMetric.setPrefixes("munp")

        self.autoRangeCheckBox = QtWidgets.QCheckBox("Auto Range")
        self.autoRangeCheckBox.toggled.connect(self.updateState)

        rangeLayout = QtWidgets.QVBoxLayout(self.rangeGroupBox)
        rangeLayout.addWidget(self.senseRangeMetric)
        rangeLayout.addWidget(self.autoRangeCheckBox)
        rangeLayout.addWidget(self.autoRangeLLimitLabel)
        rangeLayout.addWidget(self.autoRangeLLimitMetric)
        rangeLayout.addWidget(self.autoRangeULimitLabel)
        rangeLayout.addWidget(self.autoRangeULimitMetric)
        rangeLayout.addStretch()

        # Filter

        self.filterGroupBox = QtWidgets.QGroupBox()
        self.filterGroupBox.setTitle("Filter")

        self.filterEnableCheckBox = QtWidgets.QCheckBox("Enabled")

        self.filterCountLabel = QtWidgets.QLabel("Count")

        self.filterCountSpinBox = QtWidgets.QSpinBox()
        self.filterCountSpinBox.setSingleStep(1)
        self.filterCountSpinBox.setRange(2, 100)

        self.filterModeLabel = QtWidgets.QLabel("Mode")

        self.filterModeComboBox = QtWidgets.QComboBox()
        self.filterModeComboBox.addItem("Repeat", "REP")
        self.filterModeComboBox.addItem("Moving", "MOV")

        filterLayout = QtWidgets.QVBoxLayout(self.filterGroupBox)
        filterLayout.addWidget(self.filterEnableCheckBox)
        filterLayout.addWidget(self.filterCountLabel)
        filterLayout.addWidget(self.filterCountSpinBox)
        filterLayout.addWidget(self.filterModeLabel)
        filterLayout.addWidget(self.filterModeComboBox)
        # filterLayout.addStretch()

        # Integration Time

        self.integrationTimeGroupBox = QtWidgets.QGroupBox()
        self.integrationTimeGroupBox.setTitle("Integration Time")

        self.nplcLabel = QtWidgets.QLabel("NPLC")

        self.nplcSpinBox = QtWidgets.QDoubleSpinBox()
        self.nplcSpinBox.setStatusTip("Number of Power Line Cycles (0.01 to 10)")
        self.nplcSpinBox.setRange(0.01, 10.0)
        self.nplcSpinBox.setDecimals(2)
        self.nplcSpinBox.setSingleStep(0.1)
        self.nplcSpinBox.setStepType(QtWidgets.QDoubleSpinBox.AdaptiveDecimalStepType)

        integrationTimeLayout = QtWidgets.QVBoxLayout(self.integrationTimeGroupBox)
        integrationTimeLayout.addWidget(self.nplcLabel)
        integrationTimeLayout.addWidget(self.nplcSpinBox)
        integrationTimeLayout.addStretch()

        # Layout

        leftLayout = QtWidgets.QVBoxLayout()
        leftLayout.addWidget(self.rangeGroupBox)

        rightLayout = QtWidgets.QVBoxLayout()
        rightLayout.addWidget(self.filterGroupBox)
        rightLayout.addWidget(self.integrationTimeGroupBox)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(leftLayout)
        layout.addLayout(rightLayout)
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        # Parameters

        self.bindParameter("sense.range", WidgetParameter(self.senseRangeMetric))
        self.bindParameter("sense.auto_range", WidgetParameter(self.autoRangeCheckBox))
        self.bindParameter("sense.auto_range.lower_limit", WidgetParameter(self.autoRangeLLimitMetric))
        self.bindParameter("sense.auto_range.upper_limit", WidgetParameter(self.autoRangeULimitMetric))
        self.bindParameter("filter.enable", WidgetParameter(self.filterEnableCheckBox))
        self.bindParameter("filter.count", WidgetParameter(self.filterCountSpinBox))
        self.bindParameter("filter.mode", WidgetParameter(self.filterModeComboBox))
        self.bindParameter("nplc", WidgetParameter(self.nplcSpinBox))

        self.restoreDefaults()

    def restoreDefaults(self) -> None:
        self.senseRangeMetric.setValue(200e-6)
        self.autoRangeCheckBox.setChecked(True)
        self.autoRangeLLimitMetric.setValue(2e-12)
        self.autoRangeULimitMetric.setValue(20e-3)
        self.filterEnableCheckBox.setChecked(False)
        self.filterCountSpinBox.setValue(10)
        self.filterModeComboBox.setCurrentIndex(0)
        self.nplcSpinBox.setValue(5.0)
        self.updateState(self.autoRangeCheckBox.isChecked())

    def setLocked(self, state: bool) -> None:
        self.senseRangeMetric.setEnabled(not state)
        self.autoRangeCheckBox.setEnabled(not state)
        self.autoRangeLLimitMetric.setEnabled(not state)
        self.autoRangeULimitMetric.setEnabled(not state)
        self.filterEnableCheckBox.setEnabled(not state)
        self.filterCountSpinBox.setEnabled(not state)
        self.filterModeComboBox.setEnabled(not state)
        self.nplcSpinBox.setEnabled(not state)
        self.updateState(self.autoRangeCheckBox.isChecked())

    def updateState(self, checked) -> None:
        enabled = self.autoRangeCheckBox.isEnabled()
        self.senseRangeMetric.setEnabled(enabled and not checked)
        self.autoRangeLLimitLabel.setEnabled(enabled and checked)
        self.autoRangeLLimitMetric.setEnabled(enabled and checked)
        self.autoRangeULimitLabel.setEnabled(enabled and checked)
        self.autoRangeULimitMetric.setEnabled(enabled and checked)


class K6517BPanel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("K6517B", parent)

        # Range

        self.rangeGroupBox = QtWidgets.QGroupBox()
        self.rangeGroupBox.setTitle("Sense Range")

        self.senseRangeMetric = MetricWidget()
        self.senseRangeMetric.setDecimals(3)
        self.senseRangeMetric.setRange(0, 999)  # TODO
        self.senseRangeMetric.setUnit("A")
        self.senseRangeMetric.setPrefixes("munp")

        self.autoRangeLLimitLabel = QtWidgets.QLabel("Lower Limit")

        self.autoRangeLLimitMetric = MetricWidget()
        self.autoRangeLLimitMetric.setDecimals(3)
        self.autoRangeLLimitMetric.setRange(0, 999)  # TODO
        self.autoRangeLLimitMetric.setUnit("A")
        self.autoRangeLLimitMetric.setPrefixes("munp")

        self.autoRangeULimitLabel = QtWidgets.QLabel("Upper Limit")

        self.autoRangeULimitMetric = MetricWidget()
        self.autoRangeULimitMetric.setDecimals(3)
        self.autoRangeULimitMetric.setRange(0, 999)  # TODO
        self.autoRangeULimitMetric.setUnit("A")
        self.autoRangeULimitMetric.setPrefixes("munp")

        self.autoRangeCheckBox = QtWidgets.QCheckBox("Auto Range")
        self.autoRangeCheckBox.toggled.connect(self.updateState)

        rangeLayout = QtWidgets.QVBoxLayout(self.rangeGroupBox)
        rangeLayout.addWidget(self.senseRangeMetric)
        rangeLayout.addWidget(self.autoRangeCheckBox)
        rangeLayout.addWidget(self.autoRangeLLimitLabel)
        rangeLayout.addWidget(self.autoRangeLLimitMetric)
        rangeLayout.addWidget(self.autoRangeULimitLabel)
        rangeLayout.addWidget(self.autoRangeULimitMetric)

        # Source

        self.sourceGroupBox = QtWidgets.QGroupBox()
        self.sourceGroupBox.setTitle("Source")

        self.meterConnectCheckBox = QtWidgets.QCheckBox("Meter Connect")
        self.meterConnectCheckBox.setStatusTip("Enable or disable V-source LO to ammeter LO connection.")

        sourceLayout = QtWidgets.QVBoxLayout(self.sourceGroupBox)
        sourceLayout.addWidget(self.meterConnectCheckBox)
        sourceLayout.addStretch()

        # Filter

        self.filterGroupBox = QtWidgets.QGroupBox()
        self.filterGroupBox.setTitle("Filter")
        self.filterEnableCheckBox = QtWidgets.QCheckBox("Enabled")

        self.filterCountLabel = QtWidgets.QLabel("Count")

        self.filterCountSpinBox = QtWidgets.QSpinBox()
        self.filterCountSpinBox.setSingleStep(1)
        self.filterCountSpinBox.setRange(2, 100)

        self.filterModeLabel = QtWidgets.QLabel("Mode")

        self.filterModeComboBox = QtWidgets.QComboBox()
        self.filterModeComboBox.addItem("Repeat", "REP")
        self.filterModeComboBox.addItem("Moving", "MOV")

        filterLayout = QtWidgets.QVBoxLayout(self.filterGroupBox)
        filterLayout.addWidget(self.filterEnableCheckBox)
        filterLayout.addWidget(self.filterCountLabel)
        filterLayout.addWidget(self.filterCountSpinBox)
        filterLayout.addWidget(self.filterModeLabel)
        filterLayout.addWidget(self.filterModeComboBox)
        # filterLayout.addStretch()

        # Integration Time

        self.integrationTimeGroupBox = QtWidgets.QGroupBox()
        self.integrationTimeGroupBox.setTitle("Integration Time")

        self.nplcLabel = QtWidgets.QLabel("NPLC")

        self.nplcSpinBox = QtWidgets.QDoubleSpinBox()
        self.nplcSpinBox.setStatusTip("Number of Power Line Cycles (0.01 to 10)")
        self.nplcSpinBox.setRange(0.01, 10.0)
        self.nplcSpinBox.setDecimals(2)
        self.nplcSpinBox.setSingleStep(0.1)
        self.nplcSpinBox.setStepType(QtWidgets.QDoubleSpinBox.AdaptiveDecimalStepType)

        integrationTimeLayout = QtWidgets.QVBoxLayout(self.integrationTimeGroupBox)
        integrationTimeLayout.addWidget(self.nplcLabel)
        integrationTimeLayout.addWidget(self.nplcSpinBox)
        integrationTimeLayout.addStretch()

        # Layout

        leftLayout = QtWidgets.QVBoxLayout()
        leftLayout.addWidget(self.rangeGroupBox)
        leftLayout.addWidget(self.sourceGroupBox)

        rightLayout = QtWidgets.QVBoxLayout()
        rightLayout.addWidget(self.filterGroupBox)
        rightLayout.addWidget(self.integrationTimeGroupBox)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(leftLayout)
        layout.addLayout(rightLayout)
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        # Parameters

        self.bindParameter("sense.range", WidgetParameter(self.senseRangeMetric))
        self.bindParameter("sense.auto_range", WidgetParameter(self.autoRangeCheckBox))
        self.bindParameter("sense.auto_range.lower_limit", WidgetParameter(self.autoRangeLLimitMetric))
        self.bindParameter("sense.auto_range.upper_limit", WidgetParameter(self.autoRangeULimitMetric))
        self.bindParameter("source.meter_connect", WidgetParameter(self.meterConnectCheckBox))
        self.bindParameter("filter.enable", WidgetParameter(self.filterEnableCheckBox))
        self.bindParameter("filter.count", WidgetParameter(self.filterCountSpinBox))
        self.bindParameter("filter.mode", WidgetParameter(self.filterModeComboBox))
        self.bindParameter("nplc", WidgetParameter(self.nplcSpinBox))

        self.restoreDefaults()

    def restoreDefaults(self) -> None:
        self.senseRangeMetric.setValue(20e-3)
        self.autoRangeCheckBox.setChecked(True)
        self.autoRangeLLimitMetric.setValue(2e-12)
        self.autoRangeULimitMetric.setValue(20e-3)
        self.meterConnectCheckBox.setChecked(False)
        self.filterEnableCheckBox.setChecked(False)
        self.filterCountSpinBox.setValue(10)
        self.filterModeComboBox.setCurrentIndex(0)
        self.nplcSpinBox.setValue(1.0)

    def setLocked(self, state: bool) -> None:
        self.senseRangeMetric.setEnabled(not state)
        self.autoRangeCheckBox.setEnabled(not state)
        self.autoRangeLLimitMetric.setEnabled(not state)
        self.autoRangeULimitMetric.setEnabled(not state)
        self.meterConnectCheckBox.setEnabled(not state)
        self.filterEnableCheckBox.setEnabled(not state)
        self.filterCountSpinBox.setEnabled(not state)
        self.filterModeComboBox.setEnabled(not state)
        self.nplcSpinBox.setEnabled(not state)
        self.updateState(self.autoRangeCheckBox.isChecked())

    def updateState(self, checked) -> None:
        enabled = self.autoRangeCheckBox.isEnabled()
        self.senseRangeMetric.setEnabled(enabled and not checked)
        self.autoRangeLLimitLabel.setEnabled(enabled and checked)
        self.autoRangeLLimitMetric.setEnabled(enabled and checked)
        self.autoRangeULimitLabel.setEnabled(enabled and checked)
        self.autoRangeULimitMetric.setEnabled(enabled and checked)


class A4284APanel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("A4284A", parent)

        # AC amplitude

        self.amplitudeGroupBox = QtWidgets.QGroupBox()
        self.amplitudeGroupBox.setTitle("AC Amplitude")

        self.amplitudeVoltageTimeLabel = QtWidgets.QLabel("Voltage")

        self.amplitudeVoltageSpinBox = QtWidgets.QDoubleSpinBox()
        self.amplitudeVoltageSpinBox.setSuffix(" mV")
        self.amplitudeVoltageSpinBox.setDecimals(0)
        self.amplitudeVoltageSpinBox.setRange(5, 20e3)

        self.amplitudeFrequencyTimeLabel = QtWidgets.QLabel("Frequency")

        self.amplitudeFrequencySpinBox = QtWidgets.QDoubleSpinBox()
        self.amplitudeFrequencySpinBox.setSuffix(" kHz")
        self.amplitudeFrequencySpinBox.setDecimals(3)
        self.amplitudeFrequencySpinBox.setRange(0.020, 2e6)

        self.amplitudeAlcCheckBox = QtWidgets.QCheckBox("Auto Level Control (ALC)")

        amplitudeLayout = QtWidgets.QVBoxLayout(self.amplitudeGroupBox)
        amplitudeLayout.addWidget(self.amplitudeVoltageTimeLabel)
        amplitudeLayout.addWidget(self.amplitudeVoltageSpinBox)
        amplitudeLayout.addWidget(self.amplitudeFrequencyTimeLabel)
        amplitudeLayout.addWidget(self.amplitudeFrequencySpinBox)
        amplitudeLayout.addWidget(self.amplitudeAlcCheckBox)
        amplitudeLayout.addStretch()

        # Aperture

        self.apertureGroupBox = QtWidgets.QGroupBox()
        self.apertureGroupBox.setTitle("Aperture")

        self.integrationTimeLabel = QtWidgets.QLabel("Integration Time")

        self.integrationTimeComboBox = QtWidgets.QComboBox()
        self.integrationTimeComboBox.addItem("Short", "SHOR")
        self.integrationTimeComboBox.addItem("Medium", "MED")
        self.integrationTimeComboBox.addItem("Long", "LONG")

        self.averagingRateLabel = QtWidgets.QLabel("Averaging Rate")

        self.averagingRateSpinBox = QtWidgets.QSpinBox()
        self.averagingRateSpinBox.setRange(1, 128)

        apertureLayout = QtWidgets.QVBoxLayout(self.apertureGroupBox)
        apertureLayout.addWidget(self.integrationTimeLabel)
        apertureLayout.addWidget(self.integrationTimeComboBox)
        apertureLayout.addWidget(self.averagingRateLabel)
        apertureLayout.addWidget(self.averagingRateSpinBox)

        # Correction

        self.correctionGroupBox = QtWidgets.QGroupBox()
        self.correctionGroupBox.setTitle("Correction")

        self.lengthLabel = QtWidgets.QLabel("Cable Length")

        self.lengthComboBox = QtWidgets.QComboBox()
        self.lengthComboBox.addItem("0 m", 0)
        self.lengthComboBox.addItem("1 m", 1)
        self.lengthComboBox.addItem("2 m", 2)

        self.openEnabledCheckBox = QtWidgets.QCheckBox("Enable OPEN correction")
        self.openEnabledCheckBox.setStatusTip("Enable OPEN correction")

        self.shortEnabledCheckBox = QtWidgets.QCheckBox("Enable SHORT correction")
        self.shortEnabledCheckBox.setStatusTip("Enable SHORT correction")

        correctionLayout = QtWidgets.QVBoxLayout(self.correctionGroupBox)
        correctionLayout.addWidget(self.lengthLabel)
        correctionLayout.addWidget(self.lengthComboBox)
        correctionLayout.addWidget(self.openEnabledCheckBox)
        correctionLayout.addWidget(self.shortEnabledCheckBox)
        correctionLayout.addStretch()

        # Layout

        rightLayout = QtWidgets.QVBoxLayout()
        rightLayout.addWidget(self.apertureGroupBox)
        rightLayout.addWidget(self.correctionGroupBox)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.amplitudeGroupBox)
        layout.addLayout(rightLayout)
        layout.addStretch()
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        self.bindParameter("voltage", MethodParameter(self.amplitudeVoltage, self.setAmplitudeVoltage))
        self.bindParameter("frequency", MethodParameter(self.amplitudeFrequency, self.setAmplitudeFrequency))
        self.bindParameter("amplitude.alc", WidgetParameter(self.amplitudeAlcCheckBox))
        self.bindParameter("aperture.integration_time", WidgetParameter(self.integrationTimeComboBox))
        self.bindParameter("aperture.averaging_rate", WidgetParameter(self.averagingRateSpinBox))
        self.bindParameter("correction.length", WidgetParameter(self.lengthComboBox))
        self.bindParameter("correction.open.enabled", WidgetParameter(self.openEnabledCheckBox))
        self.bindParameter("correction.short.enabled", WidgetParameter(self.shortEnabledCheckBox))

        self.restoreDefaults()

    def amplitudeVoltage(self) -> float:
        return self.amplitudeVoltageSpinBox.value() / 1e3  # mV to V

    def setAmplitudeVoltage(self, voltage: float) -> None:
        self.amplitudeVoltageSpinBox.setValue(voltage * 1e3)  # V to mV

    def amplitudeFrequency(self) -> float:
        return self.amplitudeFrequencySpinBox.value() * 1e3  # kHz to Hz

    def setAmplitudeFrequency(self, frequency: float) -> None:
        self.amplitudeFrequencySpinBox.setValue(frequency / 1e3)  # Hz to kHz

    def restoreDefaults(self) -> None:
        self.setAmplitudeVoltage(1e0)
        self.setAmplitudeFrequency(1e3)
        self.amplitudeAlcCheckBox.setChecked(False)
        self.integrationTimeComboBox.setCurrentIndex(1)
        self.averagingRateSpinBox.setValue(1)
        self.lengthComboBox.setCurrentIndex(0)
        self.openEnabledCheckBox.setChecked(False)
        self.shortEnabledCheckBox.setChecked(False)

    def setLocked(self, state: bool) -> None:
        self.amplitudeVoltageSpinBox.setEnabled(not state)
        self.amplitudeFrequencySpinBox.setEnabled(not state)
        self.amplitudeAlcCheckBox.setEnabled(not state)
        self.integrationTimeComboBox.setEnabled(not state)
        self.averagingRateSpinBox.setEnabled(not state)
        self.lengthComboBox.setEnabled(not state)
        self.openEnabledCheckBox.setEnabled(not state)
        self.shortEnabledCheckBox.setEnabled(not state)


class E4980APanel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("E4980A", parent)

        # AC amplitude

        self.amplitudeGroupBox = QtWidgets.QGroupBox()
        self.amplitudeGroupBox.setTitle("AC Amplitude")

        self.amplitudeVoltageTimeLabel = QtWidgets.QLabel("Voltage")

        self.amplitudeVoltageSpinBox = QtWidgets.QDoubleSpinBox()
        self.amplitudeVoltageSpinBox.setSuffix(" mV")
        self.amplitudeVoltageSpinBox.setDecimals(0)
        self.amplitudeVoltageSpinBox.setRange(0, 20e3)

        self.amplitudeFrequencyTimeLabel = QtWidgets.QLabel("Frequency")

        self.amplitudeFrequencySpinBox = QtWidgets.QDoubleSpinBox()
        self.amplitudeFrequencySpinBox.setSuffix(" kHz")
        self.amplitudeFrequencySpinBox.setDecimals(3)
        self.amplitudeFrequencySpinBox.setRange(0.020, 2e6)

        self.amplitudeAlcCheckBox = QtWidgets.QCheckBox("Auto Level Control (ALC)")

        amplitudeLayout = QtWidgets.QVBoxLayout(self.amplitudeGroupBox)
        amplitudeLayout.addWidget(self.amplitudeVoltageTimeLabel)
        amplitudeLayout.addWidget(self.amplitudeVoltageSpinBox)
        amplitudeLayout.addWidget(self.amplitudeFrequencyTimeLabel)
        amplitudeLayout.addWidget(self.amplitudeFrequencySpinBox)
        amplitudeLayout.addWidget(self.amplitudeAlcCheckBox)
        amplitudeLayout.addStretch()

        # Aperture

        self.apertureGroupBox = QtWidgets.QGroupBox()
        self.apertureGroupBox.setTitle("Aperture")

        self.integrationTimeLabel = QtWidgets.QLabel("Integration Time")

        self.integrationTimeComboBox = QtWidgets.QComboBox()
        self.integrationTimeComboBox.addItem("Short", "SHOR")
        self.integrationTimeComboBox.addItem("Medium", "MED")
        self.integrationTimeComboBox.addItem("Long", "LONG")

        self.averagingRateLabel = QtWidgets.QLabel("Averaging Rate")

        self.averagingRateSpinBox = QtWidgets.QSpinBox()
        self.averagingRateSpinBox.setRange(1, 128)

        apertureLayout = QtWidgets.QVBoxLayout(self.apertureGroupBox)
        apertureLayout.addWidget(self.integrationTimeLabel)
        apertureLayout.addWidget(self.integrationTimeComboBox)
        apertureLayout.addWidget(self.averagingRateLabel)
        apertureLayout.addWidget(self.averagingRateSpinBox)

        # Correction

        self.correctionGroupBox = QtWidgets.QGroupBox()
        self.correctionGroupBox.setTitle("Correction")

        self.lengthLabel = QtWidgets.QLabel("Cable Length")

        self.lengthComboBox = QtWidgets.QComboBox()
        self.lengthComboBox.addItem("0 m", 0)
        self.lengthComboBox.addItem("1 m", 1)
        self.lengthComboBox.addItem("2 m", 2)
        self.lengthComboBox.addItem("4 m", 4)

        self.openEnabledCheckBox = QtWidgets.QCheckBox("Enable OPEN correction")
        self.openEnabledCheckBox.setStatusTip("Enable OPEN correction")

        self.shortEnabledCheckBox = QtWidgets.QCheckBox("Enable SHORT correction")
        self.shortEnabledCheckBox.setStatusTip("Enable SHORT correction")

        correctionLayout = QtWidgets.QVBoxLayout(self.correctionGroupBox)
        correctionLayout.addWidget(self.lengthLabel)
        correctionLayout.addWidget(self.lengthComboBox)
        correctionLayout.addWidget(self.openEnabledCheckBox)
        correctionLayout.addWidget(self.shortEnabledCheckBox)
        correctionLayout.addStretch()

        # Layout

        rightLayout = QtWidgets.QVBoxLayout()
        rightLayout.addWidget(self.apertureGroupBox)
        rightLayout.addWidget(self.correctionGroupBox)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.amplitudeGroupBox)
        layout.addLayout(rightLayout)
        layout.addStretch()
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        self.bindParameter("voltage", MethodParameter(self.amplitudeVoltage, self.setAmplitudeVoltage))
        self.bindParameter("frequency", MethodParameter(self.amplitudeFrequency, self.setAmplitudeFrequency))
        self.bindParameter("amplitude.alc", WidgetParameter(self.amplitudeAlcCheckBox))
        self.bindParameter("aperture.integration_time", WidgetParameter(self.integrationTimeComboBox))
        self.bindParameter("aperture.averaging_rate", WidgetParameter(self.averagingRateSpinBox))
        self.bindParameter("correction.length", WidgetParameter(self.lengthComboBox))
        self.bindParameter("correction.open.enabled", WidgetParameter(self.openEnabledCheckBox))
        self.bindParameter("correction.short.enabled", WidgetParameter(self.shortEnabledCheckBox))

        self.restoreDefaults()

    def amplitudeVoltage(self) -> float:
        return self.amplitudeVoltageSpinBox.value() / 1e3  # mV to V

    def setAmplitudeVoltage(self, voltage: float) -> None:
        self.amplitudeVoltageSpinBox.setValue(voltage * 1e3)  # V to mV

    def amplitudeFrequency(self) -> float:
        return self.amplitudeFrequencySpinBox.value() * 1e3  # kHz to Hz

    def setAmplitudeFrequency(self, frequency: float) -> None:
        self.amplitudeFrequencySpinBox.setValue(frequency / 1e3)  # Hz to kHz

    def restoreDefaults(self) -> None:
        self.setAmplitudeVoltage(1e0)
        self.setAmplitudeFrequency(1e3)
        self.amplitudeAlcCheckBox.setChecked(False)
        self.integrationTimeComboBox.setCurrentIndex(1)
        self.averagingRateSpinBox.setValue(1)
        self.lengthComboBox.setCurrentIndex(0)
        self.openEnabledCheckBox.setChecked(False)
        self.shortEnabledCheckBox.setChecked(False)

    def setLocked(self, state: bool) -> None:
        self.amplitudeVoltageSpinBox.setEnabled(not state)
        self.amplitudeFrequencySpinBox.setEnabled(not state)
        self.amplitudeAlcCheckBox.setEnabled(not state)
        self.integrationTimeComboBox.setEnabled(not state)
        self.averagingRateSpinBox.setEnabled(not state)
        self.lengthComboBox.setEnabled(not state)
        self.openEnabledCheckBox.setEnabled(not state)
        self.shortEnabledCheckBox.setEnabled(not state)


class BrandBoxPanel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("BrandBox", parent)

        # Channels

        self.a1CheckBox = QtWidgets.QCheckBox("A1")
        self.a2CheckBox = QtWidgets.QCheckBox("A2")
        self.b1CheckBox = QtWidgets.QCheckBox("B1")
        self.b2CheckBox = QtWidgets.QCheckBox("B2")
        self.c1CheckBox = QtWidgets.QCheckBox("C1")
        self.c2CheckBox = QtWidgets.QCheckBox("C2")

        self.channelsGroupBox = QtWidgets.QGroupBox("Channels")

        channelsLayout = QtWidgets.QGridLayout(self.channelsGroupBox)
        channelsLayout.addWidget(self.a1CheckBox, 0, 0)
        channelsLayout.addWidget(self.a2CheckBox, 1, 0)
        channelsLayout.addWidget(self.b1CheckBox, 0, 1)
        channelsLayout.addWidget(self.b2CheckBox, 1, 1)
        channelsLayout.addWidget(self.c1CheckBox, 0, 2)
        channelsLayout.addWidget(self.c2CheckBox, 1, 2)

        # Layout

        leftLayout = QtWidgets.QVBoxLayout()
        leftLayout.addWidget(self.channelsGroupBox)
        leftLayout.addStretch()

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(leftLayout)
        layout.addStretch()
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        # Parameters

        self.bindParameter("channels", MethodParameter(self.closedChannels, self.setClosedChannels))

        self.restoreDefaults()

    def closedChannels(self) -> list:
        channels = []
        if self.a1CheckBox.isChecked():
            channels.append("A1")
        if self.a2CheckBox.isChecked():
            channels.append("A2")
        if self.b1CheckBox.isChecked():
            channels.append("B1")
        if self.b2CheckBox.isChecked():
            channels.append("B2")
        if self.c1CheckBox.isChecked():
            channels.append("C1")
        if self.c2CheckBox.isChecked():
            channels.append("C2")
        return channels

    def setClosedChannels(self, channels: list) -> None:
        self.a1CheckBox.setChecked("A1" in channels)
        self.a2CheckBox.setChecked("A2" in channels)
        self.b1CheckBox.setChecked("B1" in channels)
        self.b2CheckBox.setChecked("B2" in channels)
        self.c1CheckBox.setChecked("C1" in channels)
        self.c2CheckBox.setChecked("C2" in channels)

    def restoreDefaults(self) -> None:
        self.a1CheckBox.setChecked(False)
        self.a2CheckBox.setChecked(False)
        self.b1CheckBox.setChecked(False)
        self.b2CheckBox.setChecked(False)
        self.c1CheckBox.setChecked(False)
        self.c2CheckBox.setChecked(False)

    def setLocked(self, state: bool) -> None:
        self.a1CheckBox.setEnabled(not state)
        self.a2CheckBox.setEnabled(not state)
        self.b1CheckBox.setEnabled(not state)
        self.b2CheckBox.setEnabled(not state)
        self.c1CheckBox.setEnabled(not state)
        self.c2CheckBox.setEnabled(not state)
