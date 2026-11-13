from PySide6 import QtWidgets

from ...drivers.keysight.a4155c import A4155CAdapter
from ..metric import MetricWidget
from ..panel import FSMState, InstrumentPanel, WidgetParameter

__all__ = ["A4155CPanel"]


class A4155CPanel(InstrumentPanel):
    def __init__(
        self, is_source: bool = False, parent: QtWidgets.QWidget | None = None
    ) -> None:
        super().__init__("A4155C", "Agilent 4155C", parent)

        # Used as voltage source (SMU role) the measurement controls the source
        # level, compliance and output state, otherwise used as electrometer.
        self._is_source = is_source

        # Channel

        self.channel_group_box = QtWidgets.QGroupBox()
        self.channel_group_box.setTitle("Channel")

        self.channel_label = QtWidgets.QLabel("SMU")

        self.channel_combo_box = QtWidgets.QComboBox()
        self.channel_combo_box.setStatusTip(
            "Source monitor unit used as voltage source."
            if is_source
            else "Source monitor unit used as electrometer."
        )
        for channel in A4155CAdapter.CHANNELS:
            self.channel_combo_box.addItem(channel, channel)

        self.disable_others_check_box = QtWidgets.QCheckBox("Disable Other Channels")
        self.disable_others_check_box.setStatusTip(
            "Clear all channel definitions of the analyzer before configuring the selected SMU. "
            "Must be disabled if another role uses the same analyzer."
        )

        self.standby_check_box = QtWidgets.QCheckBox("Standby Output")
        self.standby_check_box.setStatusTip(
            "Keep the source value applied between readings (used as zero check)."
        )

        self.invert_sign_check_box = QtWidgets.QCheckBox("Invert Current Sign")
        self.invert_sign_check_box.setStatusTip(
            "Report currents with electrometer polarity, matching a K6514 at the "
            "same place in the circuit."
        )

        channel_layout = QtWidgets.QVBoxLayout(self.channel_group_box)
        channel_layout.addWidget(self.channel_label)
        channel_layout.addWidget(self.channel_combo_box)
        channel_layout.addWidget(self.disable_others_check_box)
        channel_layout.addWidget(self.standby_check_box)
        channel_layout.addWidget(self.invert_sign_check_box)
        channel_layout.addStretch()

        # Source

        self.source_group_box = QtWidgets.QGroupBox()
        self.source_group_box.setTitle("Source")

        self.voltage_label = QtWidgets.QLabel("Voltage")

        self.voltage_metric = MetricWidget()
        self.voltage_metric.setStatusTip("Constant voltage applied by the SMU.")
        self.voltage_metric.set_decimals(3)
        self.voltage_metric.set_range(-A4155CAdapter.MAX_VOLTAGE, A4155CAdapter.MAX_VOLTAGE)
        self.voltage_metric.set_unit("V")
        self.voltage_metric.set_prefixes("1m")

        self.compliance_label = QtWidgets.QLabel("Current Compliance")

        self.compliance_metric = MetricWidget()
        self.compliance_metric.setStatusTip("Current compliance of the SMU.")
        self.compliance_metric.set_decimals(3)
        self.compliance_metric.set_range(0, 999)
        self.compliance_metric.set_unit("A")
        self.compliance_metric.set_prefixes("munp")

        source_layout = QtWidgets.QVBoxLayout(self.source_group_box)
        source_layout.addWidget(self.voltage_label)
        source_layout.addWidget(self.voltage_metric)
        source_layout.addWidget(self.compliance_label)
        source_layout.addWidget(self.compliance_metric)
        source_layout.addStretch()

        # The output is always kept applied while used as source
        self.standby_check_box.setHidden(is_source)
        self.source_group_box.setHidden(is_source)

        # Sense Range

        self.range_group_box = QtWidgets.QGroupBox()
        self.range_group_box.setTitle("Sense Range")

        self.range_mode_combo_box = QtWidgets.QComboBox()
        self.range_mode_combo_box.setStatusTip("Current measurement ranging mode.")
        self.range_mode_combo_box.addItem("Auto", "AUTO")
        self.range_mode_combo_box.addItem("Limited Auto", "LIM")
        self.range_mode_combo_box.addItem("Fixed", "FIX")
        self.range_mode_combo_box.currentIndexChanged.connect(
            self.on_range_mode_changed
        )

        self.range_label = QtWidgets.QLabel("Range")

        self.range_metric = MetricWidget()
        self.range_metric.setStatusTip(
            "Fixed range, respectively lowest range used by limited auto ranging."
        )
        self.range_metric.set_decimals(3)
        self.range_metric.set_range(0, 999)
        self.range_metric.set_unit("A")
        self.range_metric.set_prefixes("munp")

        range_layout = QtWidgets.QVBoxLayout(self.range_group_box)
        range_layout.addWidget(self.range_mode_combo_box)
        range_layout.addWidget(self.range_label)
        range_layout.addWidget(self.range_metric)
        range_layout.addStretch()

        # Integration Time

        self.integration_time_group_box = QtWidgets.QGroupBox()
        self.integration_time_group_box.setTitle("Integration Time")

        self.integration_time_combo_box = QtWidgets.QComboBox()
        self.integration_time_combo_box.addItem("Short", "SHOR")
        self.integration_time_combo_box.addItem("Medium", "MED")
        self.integration_time_combo_box.addItem("Long", "LONG")
        self.integration_time_combo_box.currentIndexChanged.connect(
            self.on_integration_time_changed
        )

        self.nplc_label = QtWidgets.QLabel("NPLC")

        self.nplc_spin_box = QtWidgets.QSpinBox()
        self.nplc_spin_box.setStatusTip(
            "Number of Power Line Cycles for long integration time (1 to 100)."
        )
        self.nplc_spin_box.setRange(1, 100)

        integration_time_layout = QtWidgets.QVBoxLayout(self.integration_time_group_box)
        integration_time_layout.addWidget(self.integration_time_combo_box)
        integration_time_layout.addWidget(self.nplc_label)
        integration_time_layout.addWidget(self.nplc_spin_box)
        integration_time_layout.addStretch()

        # Sampling

        self.sampling_group_box = QtWidgets.QGroupBox()
        self.sampling_group_box.setTitle("Sampling")

        self.points_label = QtWidgets.QLabel("Samples")

        self.points_spin_box = QtWidgets.QSpinBox()
        self.points_spin_box.setStatusTip(
            "Number of samples averaged for a single reading (1 to 1201)."
        )
        self.points_spin_box.setRange(1, 1201)

        self.interval_label = QtWidgets.QLabel("Interval")

        self.interval_metric = MetricWidget()
        self.interval_metric.setStatusTip(
            "Sampling interval, must not be shorter than the integration time."
        )
        self.interval_metric.set_decimals(3)
        self.interval_metric.set_range(0, 999)
        self.interval_metric.set_unit("s")
        self.interval_metric.set_prefixes("1m")

        self.hold_time_label = QtWidgets.QLabel("Hold Time")

        self.hold_time_metric = MetricWidget()
        self.hold_time_metric.setStatusTip("Delay before the first sample is taken.")
        self.hold_time_metric.set_decimals(3)
        self.hold_time_metric.set_range(0, 999)
        self.hold_time_metric.set_unit("s")
        self.hold_time_metric.set_prefixes("1m")

        sampling_layout = QtWidgets.QVBoxLayout(self.sampling_group_box)
        sampling_layout.addWidget(self.points_label)
        sampling_layout.addWidget(self.points_spin_box)
        sampling_layout.addWidget(self.interval_label)
        sampling_layout.addWidget(self.interval_metric)
        sampling_layout.addWidget(self.hold_time_label)
        sampling_layout.addWidget(self.hold_time_metric)
        sampling_layout.addStretch()

        # Layout

        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(self.channel_group_box)
        left_layout.addWidget(self.source_group_box)

        middle_layout = QtWidgets.QVBoxLayout()
        middle_layout.addWidget(self.range_group_box)
        middle_layout.addWidget(self.integration_time_group_box)

        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(self.sampling_group_box)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(left_layout)
        layout.addLayout(middle_layout)
        layout.addLayout(right_layout)
        layout.setStretch(0, 1)
        layout.setStretch(1, 1)
        layout.setStretch(2, 1)

        # Parameters

        self.bind_parameter("smu.channel", WidgetParameter(self.channel_combo_box))
        self.bind_parameter(
            "channel.disable_others", WidgetParameter(self.disable_others_check_box)
        )
        self.bind_parameter(
            "sense.invert_sign", WidgetParameter(self.invert_sign_check_box)
        )
        if not is_source:
            self.bind_parameter(
                "channel.standby", WidgetParameter(self.standby_check_box)
            )
            self.bind_parameter("source.voltage", WidgetParameter(self.voltage_metric))
            self.bind_parameter(
                "source.current_compliance", WidgetParameter(self.compliance_metric)
            )
        self.bind_parameter(
            "sense.range_mode", WidgetParameter(self.range_mode_combo_box)
        )
        self.bind_parameter("sense.range", WidgetParameter(self.range_metric))
        self.bind_parameter(
            "integration.time", WidgetParameter(self.integration_time_combo_box)
        )
        self.bind_parameter("integration.nplc", WidgetParameter(self.nplc_spin_box))
        self.bind_parameter("sampling.points", WidgetParameter(self.points_spin_box))
        self.bind_parameter("sampling.interval", WidgetParameter(self.interval_metric))
        self.bind_parameter(
            "sampling.hold_time", WidgetParameter(self.hold_time_metric)
        )

        self.restore_defaults()

    def restore_defaults(self) -> None:
        self.channel_combo_box.setCurrentIndex(0)
        self.disable_others_check_box.setChecked(True)
        self.standby_check_box.setChecked(True)
        # A source reports currents with SMU polarity like the other SMUs
        self.invert_sign_check_box.setChecked(not self._is_source)
        self.voltage_metric.set_value(0.0)
        self.compliance_metric.set_value(1e-3)
        self.range_mode_combo_box.setCurrentIndex(0)
        self.range_metric.set_value(1e-9)
        self.integration_time_combo_box.setCurrentIndex(1)
        self.nplc_spin_box.setValue(1)
        self.points_spin_box.setValue(1)
        self.interval_metric.set_value(2e-3)
        self.hold_time_metric.set_value(0.0)
        self.on_integration_time_changed(
            self.integration_time_combo_box.currentIndex()
        )
        self.on_range_mode_changed(self.range_mode_combo_box.currentIndex())

    def set_fsm_state(self, state: FSMState) -> None:
        enabled = state == FSMState.IDLE
        self.channel_combo_box.setEnabled(enabled)
        self.disable_others_check_box.setEnabled(enabled)
        self.standby_check_box.setEnabled(enabled)
        self.invert_sign_check_box.setEnabled(enabled)
        self.voltage_metric.setEnabled(enabled)
        self.compliance_metric.setEnabled(enabled)
        self.range_mode_combo_box.setEnabled(enabled)
        self.range_metric.setEnabled(enabled)
        self.integration_time_combo_box.setEnabled(enabled)
        self.nplc_spin_box.setEnabled(enabled)
        self.points_spin_box.setEnabled(enabled)
        self.interval_metric.setEnabled(enabled)
        self.hold_time_metric.setEnabled(enabled)
        self.on_integration_time_changed(
            self.integration_time_combo_box.currentIndex()
        )
        self.on_range_mode_changed(self.range_mode_combo_box.currentIndex())

    def on_integration_time_changed(self, index: int) -> None:
        enabled = self.integration_time_combo_box.isEnabled()
        is_long = self.integration_time_combo_box.itemData(index) == "LONG"
        self.nplc_label.setEnabled(enabled and is_long)
        self.nplc_spin_box.setEnabled(enabled and is_long)

    def on_range_mode_changed(self, index: int) -> None:
        enabled = self.range_mode_combo_box.isEnabled()
        is_auto = self.range_mode_combo_box.itemData(index) == "AUTO"
        self.range_label.setEnabled(enabled and not is_auto)
        self.range_metric.setEnabled(enabled and not is_auto)
