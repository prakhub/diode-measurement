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
    'E4285Panel',
    'E4980APanel'
]


class InstrumentPanel(QtWidgets.QWidget):

    def __init__(self, model: str, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.setModel(model)

    def model(self) -> str:
        return self.property("model")

    def setModel(self, model: str) -> None:
        self.setProperty("model", model)

    def lock(self) -> None:
        pass

    def unlock(self) -> None:
        pass

    def config(self) -> Dict[str, Any]:
        return {}

    def setConfig(self, config: Dict[str, Any]) -> None:
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

    def config(self) -> Dict[str, Any]:
        config = {}
        config["filter.mode"] = self.filterModeComboBox.currentData()
        return config

    def setConfig(self, config: Dict[str, Any]) -> None:
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

    def lock(self) -> None:
        self.filterEnableCheckBox.setEnabled(False)
        self.filterCountSpinBox.setEnabled(False)
        self.filterModeComboBox.setEnabled(False)
        self.nplcSpinBox.setEnabled(False)

    def unlock(self) -> None:
        self.filterEnableCheckBox.setEnabled(True)
        self.filterCountSpinBox.setEnabled(True)
        self.filterModeComboBox.setEnabled(True)
        self.nplcSpinBox.setEnabled(True)

    def config(self) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        params["filter.enable"] = self.filterEnableCheckBox.isChecked()
        params["filter.count"] = self.filterCountSpinBox.value()
        params["filter.mode"] = self.filterModeComboBox.currentData()
        params["nplc"] = self.nplcSpinBox.value()
        params["route.terminals"] = self.routeTerminalsComboBox.currentData()
        return params

    def setConfig(self, config: Dict[str, Any]) -> None:
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

    def lock(self) -> None:
        self.filterEnableCheckBox.setEnabled(False)
        self.filterCountSpinBox.setEnabled(False)
        self.filterModeComboBox.setEnabled(False)
        self.nplcSpinBox.setEnabled(False)

    def unlock(self) -> None:
        self.filterEnableCheckBox.setEnabled(True)
        self.filterCountSpinBox.setEnabled(True)
        self.filterModeComboBox.setEnabled(True)
        self.nplcSpinBox.setEnabled(True)

    def config(self) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        params["filter.enable"] = self.filterEnableCheckBox.isChecked()
        params["filter.count"] = self.filterCountSpinBox.value()
        params["filter.mode"] = self.filterModeComboBox.currentData()
        params["nplc"] = self.nplcSpinBox.value()
        params["route.terminals"] = self.routeTerminalsComboBox.currentData()
        return params

    def setConfig(self, config: Dict[str, Any]) -> None:
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

    def lock(self) -> None:
        self.filterEnableCheckBox.setEnabled(False)
        self.filterCountSpinBox.setEnabled(False)
        self.filterModeComboBox.setEnabled(False)
        self.nplcSpinBox.setEnabled(False)

    def unlock(self) -> None:
        self.filterEnableCheckBox.setEnabled(True)
        self.filterCountSpinBox.setEnabled(True)
        self.filterModeComboBox.setEnabled(True)
        self.nplcSpinBox.setEnabled(True)

    def config(self) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        params["filter.enable"] = self.filterEnableCheckBox.isChecked()
        params["filter.count"] = self.filterCountSpinBox.value()
        params["filter.mode"] = self.filterModeComboBox.currentData()
        params["nplc"] = self.nplcSpinBox.value()
        return params

    def setConfig(self, config: Dict[str, Any]) -> None:
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


class E4285Panel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("E4285", parent)


class E4980APanel(InstrumentPanel):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__("E4980A", parent)
