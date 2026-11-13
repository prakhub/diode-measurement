import pytest

from diode_measurement.drivers.keysight.a4155c import A4155CAdapter
from diode_measurement.gui.panel import FSMState
from diode_measurement.gui.panels.a4155c import A4155CPanel


@pytest.fixture
def panel(qtbot):
    widget = A4155CPanel()
    qtbot.addWidget(widget)
    return widget


def test_panel_a4155c_defaults(panel):
    assert panel.model() == "A4155C"
    assert panel.config() == {
        "smu.channel": "SMU1",
        "channel.disable_others": True,
        "channel.standby": True,
        "sense.invert_sign": True,
        "source.voltage": 0.0,
        "source.current_compliance": pytest.approx(1e-3),
        "sense.range_mode": "AUTO",
        "sense.range": pytest.approx(1e-9),
        "integration.time": "MED",
        "integration.nplc": 1,
        "sampling.points": 1,
        "sampling.interval": pytest.approx(2e-3),
        "sampling.hold_time": 0.0,
    }


def test_panel_a4155c_channels(panel):
    channels = [
        panel.channel_combo_box.itemData(index)
        for index in range(panel.channel_combo_box.count())
    ]
    assert channels == list(A4155CAdapter.CHANNELS)


def test_panel_a4155c_apply_config(panel):
    panel.apply_config(
        {
            "smu.channel": "SMU3",
            "integration.time": "LONG",
            "integration.nplc": 10,
            "sampling.points": 16,
        }
    )
    config = panel.config()
    assert config["smu.channel"] == "SMU3"
    assert config["integration.time"] == "LONG"
    assert config["integration.nplc"] == 10
    assert config["sampling.points"] == 16

    panel.restore_defaults()
    assert panel.config()["smu.channel"] == "SMU1"


def test_panel_a4155c_nplc_enabled_for_long_integration(panel):
    assert not panel.nplc_spin_box.isEnabled()

    panel.apply_config({"integration.time": "LONG"})
    assert panel.nplc_spin_box.isEnabled()

    panel.apply_config({"integration.time": "SHOR"})
    assert not panel.nplc_spin_box.isEnabled()


def test_panel_a4155c_range_enabled_for_non_auto(panel):
    assert not panel.range_metric.isEnabled()

    panel.apply_config({"sense.range_mode": "LIM"})
    assert panel.range_metric.isEnabled()

    panel.apply_config({"sense.range_mode": "FIX"})
    assert panel.range_metric.isEnabled()

    panel.apply_config({"sense.range_mode": "AUTO"})
    assert not panel.range_metric.isEnabled()


def test_panel_a4155c_fsm_state(panel):
    panel.set_fsm_state(FSMState.RAMPING)
    assert not panel.channel_combo_box.isEnabled()
    assert not panel.integration_time_combo_box.isEnabled()
    assert not panel.nplc_spin_box.isEnabled()

    panel.set_fsm_state(FSMState.IDLE)
    assert panel.channel_combo_box.isEnabled()
    assert panel.integration_time_combo_box.isEnabled()


def test_panel_a4155c_config_accepted_by_driver(panel, res):
    """Panel parameters must match the options read by the driver."""
    d = A4155CAdapter(res)
    res.buffer = ["1"] * 32
    assert d.configure(panel.config()) is None
    assert d.channel == "SMU1"


@pytest.fixture
def source_panel(qtbot):
    widget = A4155CPanel(is_source=True)
    qtbot.addWidget(widget)
    return widget


def test_panel_a4155c_source_defaults(source_panel):
    assert source_panel.config() == {
        "smu.channel": "SMU1",
        "channel.disable_others": True,
        "sense.invert_sign": False,
        "sense.range_mode": "AUTO",
        "sense.range": pytest.approx(1e-9),
        "integration.time": "MED",
        "integration.nplc": 1,
        "sampling.points": 1,
        "sampling.interval": pytest.approx(2e-3),
        "sampling.hold_time": 0.0,
    }
    assert source_panel.standby_check_box.isHidden()
    assert source_panel.source_group_box.isHidden()


def test_panel_a4155c_source_config_accepted_by_driver(source_panel, res):
    d = A4155CAdapter(res)
    res.buffer = ["1"] * 32
    assert d.configure(source_panel.config()) is None
    assert not d.is_invert_sign_enabled()
    messages = [message for message in res.buffer if message.startswith(":")]
    # Output stays disconnected until the measurement enables it
    assert ":PAGE:CHAN:SMU1:STAN OFF" in messages
    assert not any(":PAGE:MEAS:SAMP:CONS:" in message for message in messages)
