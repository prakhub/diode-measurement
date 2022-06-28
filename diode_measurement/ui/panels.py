from typing import Any, Dict

from PyQt5 import QtWidgets

__all__ = [
    'K237Panel',
    'K595Panel',
    'K2410Panel',
    'K2470Panel',
    'K2657APanel',
    'K2700Panel',
    'K6514Panel',
    'K6517BPanel',
    'E4980APanel',
    'A4284APanel',
]

ConfigType = Dict[str, Any]


class InstrumentPanel(QtWidgets.QWidget):

    def __init__(self, model: str, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.setModel(model)

    def model(self) -> str:
        return self.property("model")

    def setModel(self, model: str) -> None:
        self.setProperty("model", model)

    def restoreDefaults(self) -> None:
        pass

    def setLocked(self, state: bool) -> None:
        pass

    def config(self) -> ConfigType:
        return {}

    def setConfig(self, config: ConfigType) -> None:
        pass


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

    def restoreDefaults(self) -> None:
        self.filterModeComboBox.setCurrentIndex(0)

    def setLocked(self, state: bool) -> None:
        self.filterModeComboBox.setEnabled(not state)

    def config(self) -> ConfigType:
        config: ConfigType = {}
        config["filter.mode"] = self.filterModeComboBox.currentData()
        return config

    def setConfig(self, config: ConfigType) -> None:
        filter_mode = config.get("filter.mode")
        if filter_mode is not None:
            index = self.filterModeComboBox.findData(filter_mode)
            self.filterModeComboBox.setCurrentIndex(index)


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
        self.filterCountSpinBox.setRange(1, 100)

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
        self.nplcSpinBox.setValue(1.0)

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

    def restoreDefaults(self) -> None:
        self.filterEnableCheckBox.setChecked(False)
        self.filterCountSpinBox.setValue(0)
        self.filterModeComboBox.setCurrentIndex(0)
        self.nplcSpinBox.setValue(1.0)
        self.routeTerminalsComboBox.setCurrentIndex(0)

    def setLocked(self, state: bool) -> None:
        self.filterEnableCheckBox.setEnabled(not state)
        self.filterCountSpinBox.setEnabled(not state)
        self.filterModeComboBox.setEnabled(not state)
        self.nplcSpinBox.setEnabled(not state)
        self.routeTerminalsComboBox.setEnabled(not state)

    def config(self) -> ConfigType:
        params: ConfigType = {}
        params["filter.enable"] = self.filterEnableCheckBox.isChecked()
        params["filter.count"] = self.filterCountSpinBox.value()
        params["filter.mode"] = self.filterModeComboBox.currentData()
        params["nplc"] = self.nplcSpinBox.value()
        params["route.terminals"] = self.routeTerminalsComboBox.currentData()
        return params

    def setConfig(self, config: ConfigType) -> None:
        filter_enable = config.get("filter.enable")
        if filter_enable is not None:
            self.filterEnableCheckBox.setChecked(filter_enable)

        filter_count = config.get("filter.count")
        if filter_count is not None:
            self.filterCountSpinBox.setValue(filter_count)

        filter_mode = config.get("filter.mode")
        if filter_mode is not None:
            index = self.filterModeComboBox.findData(filter_mode)
            self.filterModeComboBox.setCurrentIndex(index)

        nplc = config.get("nplc", None)
        if nplc is not None:
            self.nplcSpinBox.setValue(nplc)

        route_terminals = config.get("route.terminals")
        if route_terminals is not None:
            index = self.routeTerminalsComboBox.findData(route_terminals)
            self.routeTerminalsComboBox.setCurrentIndex(index)


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
        self.filterCountSpinBox.setRange(1, 100)

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
        self.nplcSpinBox.setValue(1.0)

        integrationTimeLayout = QtWidgets.QVBoxLayout(self.integrationTimeGroupBox)
        integrationTimeLayout.addWidget(self.nplcLabel)
        integrationTimeLayout.addWidget(self.nplcSpinBox)

        # Route Terminals

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

    def restoreDefaults(self) -> None:
        self.filterEnableCheckBox.setChecked(False)
        self.filterCountSpinBox.setValue(0)
        self.filterModeComboBox.setCurrentIndex(0)
        self.nplcSpinBox.setValue(1.0)
        self.routeTerminalsComboBox.setCurrentIndex(0)

    def setLocked(self, state: bool) -> None:
        self.filterEnableCheckBox.setEnabled(not state)
        self.filterCountSpinBox.setEnabled(not state)
        self.filterModeComboBox.setEnabled(not state)
        self.nplcSpinBox.setEnabled(not state)
        self.routeTerminalsComboBox.setEnabled(not state)

    def config(self) -> ConfigType:
        params: ConfigType = {}
        params["filter.enable"] = self.filterEnableCheckBox.isChecked()
        params["filter.count"] = self.filterCountSpinBox.value()
        params["filter.mode"] = self.filterModeComboBox.currentData()
        params["nplc"] = self.nplcSpinBox.value()
        params["route.terminals"] = self.routeTerminalsComboBox.currentData()
        return params

    def setConfig(self, config: ConfigType) -> None:
        filter_enable = config.get("filter.enable")
        if filter_enable is not None:
            self.filterEnableCheckBox.setChecked(filter_enable)

        filter_count = config.get("filter.count")
        if filter_count is not None:
            self.filterCountSpinBox.setValue(filter_count)

        filter_mode = config.get("filter.mode")
        if filter_mode is not None:
            index = self.filterModeComboBox.findData(filter_mode)
            self.filterModeComboBox.setCurrentIndex(index)

        nplc = config.get("nplc")
        if nplc is not None:
            self.nplcSpinBox.setValue(nplc)

        route_terminals = config.get("route.terminals")
        if route_terminals is not None:
            index = self.routeTerminalsComboBox.findData(route_terminals)
            self.routeTerminalsComboBox.setCurrentIndex(index)


class K2657APanel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("K2657A", parent)

        self.filterGroupBox = QtWidgets.QGroupBox()
        self.filterGroupBox.setTitle("Filter")
        self.filterEnableCheckBox = QtWidgets.QCheckBox("Enabled")

        self.filterCountLabel = QtWidgets.QLabel("Count")

        self.filterCountSpinBox = QtWidgets.QSpinBox()
        self.filterCountSpinBox.setSingleStep(1)
        self.filterCountSpinBox.setRange(1, 100)

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
        self.nplcSpinBox.setValue(1.0)

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

    def restoreDefaults(self) -> None:
        self.filterEnableCheckBox.setChecked(False)
        self.filterCountSpinBox.setValue(0)
        self.filterModeComboBox.setCurrentIndex(0)
        self.nplcSpinBox.setValue(1.0)

    def setLocked(self, state: bool) -> None:
        self.filterEnableCheckBox.setEnabled(not state)
        self.filterCountSpinBox.setEnabled(not state)
        self.filterModeComboBox.setEnabled(not state)
        self.nplcSpinBox.setEnabled(not state)

    def config(self) -> ConfigType:
        params: ConfigType = {}
        params["filter.enable"] = self.filterEnableCheckBox.isChecked()
        params["filter.count"] = self.filterCountSpinBox.value()
        params["filter.mode"] = self.filterModeComboBox.currentData()
        params["nplc"] = self.nplcSpinBox.value()
        return params

    def setConfig(self, config: ConfigType) -> None:
        filter_enable = config.get("filter.enable")
        if filter_enable is not None:
            self.filterEnableCheckBox.setChecked(filter_enable)

        filter_count = config.get("filter.count")
        if filter_count is not None:
            self.filterCountSpinBox.setValue(filter_count)

        filter_mode = config.get("filter.mode")
        if filter_mode is not None:
            index = self.filterModeComboBox.findData(filter_mode)
            self.filterModeComboBox.setCurrentIndex(index)

        nplc = config.get("nplc")
        if nplc is not None:
            self.nplcSpinBox.setValue(nplc)


class K2700Panel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("K2700", parent)


class K6514Panel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("K6514", parent)


class K6517BPanel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("K6517B", parent)


class A4284APanel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("A4284A", parent)

        # Aperture

        self.apertureGroupBox = QtWidgets.QGroupBox()
        self.apertureGroupBox.setTitle("Aperture")

        self.integrationTimeLabel = QtWidgets.QLabel("Integration Time")

        self.integrationTimeComboBox = QtWidgets.QComboBox()
        self.integrationTimeComboBox.addItem("Short", "SHOR")
        self.integrationTimeComboBox.addItem("Medium", "MED")
        self.integrationTimeComboBox.addItem("Long", "LONG")
        self.integrationTimeComboBox.setCurrentIndex(1)

        self.averagingRateLabel = QtWidgets.QLabel("Averaging Rate")

        self.averagingRateSpinBox = QtWidgets.QSpinBox()
        self.averagingRateSpinBox.setRange(1, 128)
        self.averagingRateSpinBox.setValue(1)

        apertureLayout = QtWidgets.QVBoxLayout(self.apertureGroupBox)
        apertureLayout.addWidget(self.integrationTimeLabel)
        apertureLayout.addWidget(self.integrationTimeComboBox)
        apertureLayout.addWidget(self.averagingRateLabel)
        apertureLayout.addWidget(self.averagingRateSpinBox)
        apertureLayout.addStretch()

        # Correction

        self.correctionGroupBox = QtWidgets.QGroupBox()
        self.correctionGroupBox.setTitle("Correction")

        self.lengthLabel = QtWidgets.QLabel("Cable Length")

        self.lengthComboBox = QtWidgets.QComboBox()
        self.lengthComboBox.addItem("0 m", 0)
        self.lengthComboBox.addItem("1 m", 1)
        self.lengthComboBox.addItem("2 m", 2)

        self.openEnabledCheckBox = QtWidgets.QCheckBox("Enable OPEN")

        correctionLayout = QtWidgets.QVBoxLayout(self.correctionGroupBox)
        correctionLayout.addWidget(self.lengthLabel)
        correctionLayout.addWidget(self.lengthComboBox)
        correctionLayout.addWidget(self.openEnabledCheckBox)
        correctionLayout.addStretch()

        # Layout

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.apertureGroupBox)
        layout.addWidget(self.correctionGroupBox)
        layout.addStretch()
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

    def restoreDefaults(self) -> None:
        self.integrationTimeComboBox.setCurrentIndex(1)
        self.averagingRateSpinBox.setValue(1)
        self.lengthComboBox.setCurrentIndex(0)
        self.openEnabledCheckBox.setChecked(False)

    def setLocked(self, state: bool) -> None:
        self.integrationTimeComboBox.setEnabled(not state)
        self.averagingRateSpinBox.setEnabled(not state)
        self.lengthComboBox.setEnabled(not state)
        self.openEnabledCheckBox.setEnabled(not state)

    def config(self) -> ConfigType:
        config: ConfigType = {}
        config["aperture.integration_time"] = self.integrationTimeComboBox.currentData()
        config["aperture.averaging_rate"] = self.averagingRateSpinBox.value()
        config["correction.length"] = self.lengthComboBox.currentData()
        config["correction.open.enabled"] = self.openEnabledCheckBox.isChecked()
        return config

    def setConfig(self, config: ConfigType) -> None:
        integration_time = config.get("aperture.integration_time")
        if integration_time is not None:
            index = self.integrationTimeComboBox.findData(integration_time)
            self.integrationTimeComboBox.setCurrentIndex(index)
        averaging_rate = config.get("aperture.averaging_rate")
        if averaging_rate is not None:
            self.averagingRateSpinBox.setValue(averaging_rate)
        correction_length = config.get("correction.length")
        if correction_length is not None:
            index = self.lengthComboBox.findData(correction_length)
            self.lengthComboBox.setCurrentIndex(index)
        correction_open_enabled = config.get("correction.open.enabled")
        if correction_open_enabled is not None:
            self.openEnabledCheckBox.setChecked(correction_open_enabled)


class E4980APanel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("E4980A", parent)

        # Aperture

        self.apertureGroupBox = QtWidgets.QGroupBox()
        self.apertureGroupBox.setTitle("Aperture")

        self.integrationTimeLabel = QtWidgets.QLabel("Integration Time")

        self.integrationTimeComboBox = QtWidgets.QComboBox()
        self.integrationTimeComboBox.addItem("Short", "SHOR")
        self.integrationTimeComboBox.addItem("Medium", "MED")
        self.integrationTimeComboBox.addItem("Long", "LONG")
        self.integrationTimeComboBox.setCurrentIndex(1)

        self.averagingRateLabel = QtWidgets.QLabel("Averaging Rate")

        self.averagingRateSpinBox = QtWidgets.QSpinBox()
        self.averagingRateSpinBox.setRange(1, 128)
        self.averagingRateSpinBox.setValue(1)

        apertureLayout = QtWidgets.QVBoxLayout(self.apertureGroupBox)
        apertureLayout.addWidget(self.integrationTimeLabel)
        apertureLayout.addWidget(self.integrationTimeComboBox)
        apertureLayout.addWidget(self.averagingRateLabel)
        apertureLayout.addWidget(self.averagingRateSpinBox)
        apertureLayout.addStretch()

        # Correction

        self.correctionGroupBox = QtWidgets.QGroupBox()
        self.correctionGroupBox.setTitle("Correction")

        self.lengthLabel = QtWidgets.QLabel("Cable Length")

        self.lengthComboBox = QtWidgets.QComboBox()
        self.lengthComboBox.addItem("0 m", 0)
        self.lengthComboBox.addItem("1 m", 1)
        self.lengthComboBox.addItem("2 m", 2)
        self.lengthComboBox.addItem("4 m", 4)

        self.openEnabledCheckBox = QtWidgets.QCheckBox("Enable OPEN")

        correctionLayout = QtWidgets.QVBoxLayout(self.correctionGroupBox)
        correctionLayout.addWidget(self.lengthLabel)
        correctionLayout.addWidget(self.lengthComboBox)
        correctionLayout.addWidget(self.openEnabledCheckBox)
        correctionLayout.addStretch()

        # Layout

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.apertureGroupBox)
        layout.addWidget(self.correctionGroupBox)
        layout.addStretch()
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

    def restoreDefaults(self) -> None:
        self.integrationTimeComboBox.setCurrentIndex(1)
        self.averagingRateSpinBox.setValue(1)
        self.lengthComboBox.setCurrentIndex(0)
        self.openEnabledCheckBox.setChecked(False)

    def setLocked(self, state: bool) -> None:
        self.integrationTimeComboBox.setEnabled(not state)
        self.averagingRateSpinBox.setEnabled(not state)
        self.lengthComboBox.setEnabled(not state)
        self.openEnabledCheckBox.setEnabled(not state)

    def config(self) -> ConfigType:
        config: ConfigType = {}
        config["aperture.integration_time"] = self.integrationTimeComboBox.currentData()
        config["aperture.averaging_rate"] = self.averagingRateSpinBox.value()
        config["correction.length"] = self.lengthComboBox.currentData()
        config["correction.open.enabled"] = self.openEnabledCheckBox.isChecked()
        return config

    def setConfig(self, config: ConfigType) -> None:
        integration_time = config.get("aperture.integration_time")
        if integration_time is not None:
            index = self.integrationTimeComboBox.findData(integration_time)
            self.integrationTimeComboBox.setCurrentIndex(index)
        averaging_rate = config.get("aperture.averaging_rate")
        if averaging_rate is not None:
            self.averagingRateSpinBox.setValue(averaging_rate)
        correction_length = config.get("correction.length")
        if correction_length is not None:
            index = self.lengthComboBox.findData(correction_length)
            self.lengthComboBox.setCurrentIndex(index)
        correction_open_enabled = config.get("correction.open.enabled")
        if correction_open_enabled is not None:
            self.openEnabledCheckBox.setChecked(correction_open_enabled)
