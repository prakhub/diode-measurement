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

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.setModel(model)

    def model(self):
        return self.property("model")

    def setModel(self, model):
        self.setProperty("model", model)

    def lock(self):
        pass

    def unlock(self):
        pass

    def config(self):
        return {}

    def setConfig(self, config):
        pass


class K237Panel(InstrumentPanel):

    def __init__(self, parent=None):
        super().__init__("K237", parent)

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

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.filterGroupBox)
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        layout = QtWidgets.QVBoxLayout(self.filterGroupBox)
        layout.addWidget(self.filterModeLabel)
        layout.addWidget(self.filterModeComboBox)
        layout.addStretch()

    def config(self):
        config = {}
        config["filter.mode"] = self.filterModeComboBox.currentData()
        return config

    def setConfig(self, config):
        filter_mode = config.get("filter.mode")
        if filter_mode is not None:
            index = self.filterModeComboBox.findData(filter_mode)
            self.filterModeComboBox.setCurrentIndex(index)


class K595Panel(InstrumentPanel):

    def __init__(self, parent=None):
        super().__init__("K595", parent)


class K2410Panel(InstrumentPanel):

    def __init__(self, parent=None):
        super().__init__("K2410", parent)

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

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.filterGroupBox)
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        layout = QtWidgets.QVBoxLayout(self.filterGroupBox)
        layout.addWidget(self.filterEnableCheckBox)
        layout.addWidget(self.filterCountLabel)
        layout.addWidget(self.filterCountSpinBox)
        layout.addWidget(self.filterModeLabel)
        layout.addWidget(self.filterModeComboBox)
        layout.addStretch()

    def lock(self):
        self.filterEnableCheckBox.setEnabled(False)
        self.filterCountSpinBox.setEnabled(False)
        self.filterModeComboBox.setEnabled(False)

    def unlock(self):
        self.filterEnableCheckBox.setEnabled(True)
        self.filterCountSpinBox.setEnabled(True)
        self.filterModeComboBox.setEnabled(True)

    def config(self):
        params = {}
        params["filter.enable"] = self.filterEnableCheckBox.isChecked()
        params["filter.count"] = self.filterCountSpinBox.value()
        params["filter.mode"] = self.filterModeComboBox.currentData()
        return params

    def setConfig(self, config):
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


class K2470Panel(InstrumentPanel):

    def __init__(self, parent=None):
        super().__init__("K2470", parent)

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

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.filterGroupBox)
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        layout = QtWidgets.QVBoxLayout(self.filterGroupBox)
        layout.addWidget(self.filterEnableCheckBox)
        layout.addWidget(self.filterCountLabel)
        layout.addWidget(self.filterCountSpinBox)
        layout.addWidget(self.filterModeLabel)
        layout.addWidget(self.filterModeComboBox)
        layout.addStretch()

    def lock(self):
        self.filterEnableCheckBox.setEnabled(False)
        self.filterCountSpinBox.setEnabled(False)
        self.filterModeComboBox.setEnabled(False)

    def unlock(self):
        self.filterEnableCheckBox.setEnabled(True)
        self.filterCountSpinBox.setEnabled(True)
        self.filterModeComboBox.setEnabled(True)

    def config(self):
        params = {}
        params["filter.enable"] = self.filterEnableCheckBox.isChecked()
        params["filter.count"] = self.filterCountSpinBox.value()
        params["filter.mode"] = self.filterModeComboBox.currentData()
        return params

    def setConfig(self, config):
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


class K2657APanel(InstrumentPanel):

    def __init__(self, parent=None):
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

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.filterGroupBox)
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)

        layout = QtWidgets.QVBoxLayout(self.filterGroupBox)
        layout.addWidget(self.filterEnableCheckBox)
        layout.addWidget(self.filterCountLabel)
        layout.addWidget(self.filterCountSpinBox)
        layout.addWidget(self.filterModeLabel)
        layout.addWidget(self.filterModeComboBox)
        layout.addStretch()

    def lock(self):
        self.filterEnableCheckBox.setEnabled(False)
        self.filterCountSpinBox.setEnabled(False)
        self.filterModeComboBox.setEnabled(False)

    def unlock(self):
        self.filterEnableCheckBox.setEnabled(True)
        self.filterCountSpinBox.setEnabled(True)
        self.filterModeComboBox.setEnabled(True)

    def config(self):
        params = {}
        params["filter.enable"] = self.filterEnableCheckBox.isChecked()
        params["filter.count"] = self.filterCountSpinBox.value()
        params["filter.mode"] = self.filterModeComboBox.currentData()
        return params

    def setConfig(self, config):
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


class K2700Panel(InstrumentPanel):

    def __init__(self, parent=None):
        super().__init__("K2700", parent)


class K6514Panel(InstrumentPanel):

    def __init__(self, parent=None):
        super().__init__("K6514", parent)


class K6517BPanel(InstrumentPanel):

    def __init__(self, parent=None):
        super().__init__("K6517B", parent)


class E4285Panel(InstrumentPanel):

    def __init__(self, parent=None):
        super().__init__("E4285", parent)


class E4980APanel(InstrumentPanel):

    def __init__(self, parent=None):
        super().__init__("E4980A", parent)
