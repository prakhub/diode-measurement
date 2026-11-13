import os
from datetime import datetime

import pytest

from diode_measurement.controller import Controller
from diode_measurement.gui.mainwindow import MainWindow
from diode_measurement.state import FSMState


@pytest.fixture
def controller(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    controller = Controller(window)
    yield controller
    controller.state_machine.stop()


def test_create_filename_from_sample_and_timestamp(controller):
    general_widget = controller.main_window.general_widget
    general_widget.set_output_dir(os.path.join("data", "A1"))
    general_widget.set_filename("")
    general_widget.set_filename_suffix("")
    controller.state.update({"sample": "A1", "timestamp": 1629455368.29})

    timestamp = datetime.fromtimestamp(1629455368.29).strftime("%Y-%m-%dT%H-%M-%S")
    filename = controller.create_filename()
    assert os.path.basename(filename) == f"A1-{timestamp}.txt"
    assert os.path.dirname(filename) == os.path.join("data", "A1")


def test_create_filename_with_filename_and_suffix(controller):
    general_widget = controller.main_window.general_widget
    general_widget.set_output_dir(os.path.join("data", "A1"))
    general_widget.set_filename("A1_irrad_iv")
    general_widget.set_filename_suffix("iv_reverse")
    controller.state.update({"sample": "A1", "timestamp": 1629455368.29})

    filename = controller.create_filename()
    assert os.path.basename(filename) == "A1_irrad_iv_iv_reverse.txt"


def test_create_filename_without_suffix(controller):
    general_widget = controller.main_window.general_widget
    general_widget.set_filename("A1_irrad_cv")
    general_widget.set_filename_suffix("")

    assert os.path.basename(controller.create_filename()) == "A1_irrad_cv.txt"


def test_create_filename_sanitizes_unsafe_characters(controller):
    general_widget = controller.main_window.general_widget
    general_widget.set_filename("A1 irrad:iv")
    general_widget.set_filename_suffix("")

    assert os.path.basename(controller.create_filename()) == "A1_irrad_iv.txt"


def test_configure_output_parameters(controller):
    controller.configure(
        {
            "sample": "A1",
            "output_enabled": True,
            "output_dir": os.path.join("data", "A1"),
            "filename": "A1_irrad_iv",
            "filename_suffix": "iv_forward",
        }
    )
    general_widget = controller.main_window.general_widget
    assert general_widget.sample_name() == "A1"
    assert general_widget.is_output_enabled()
    assert general_widget.output_dir() == os.path.join("data", "A1")
    assert general_widget.filename() == "A1_irrad_iv"
    assert general_widget.filename_suffix() == "iv_forward"


def test_configure_applies_measurement_type_first(controller):
    """Selecting a measurement type resets voltages to its defaults, it must
    not overwrite values applied within the same request.
    """
    controller.configure(
        {
            "begin_voltage": 0.0,
            "end_voltage": -200.0,
            "step_voltage": 1.0,
            "compliance": 25e-6,
            "measurement_type": "iv",
        }
    )
    general_widget = controller.main_window.general_widget
    assert general_widget.begin_voltage() == pytest.approx(0.0)
    assert general_widget.end_voltage() == pytest.approx(-200.0)
    assert general_widget.step_voltage() == pytest.approx(1.0)
    assert general_widget.current_compliance() == pytest.approx(25e-6)


def test_configure_lcr_parameters(controller):
    role = controller.main_window.find_role("LCR")
    role.set_model("E4980A")

    controller.configure({"lcr_amplitude": 0.5, "lcr_frequency": 10e3})

    config = role.find_instrument_panel("E4980A").config()
    assert config["voltage"] == pytest.approx(0.5)
    assert config["frequency"] == pytest.approx(10e3)


def test_configure_lcr_parameter_unsupported_by_model(controller):
    """K595 has no adjustable AC amplitude frequency."""
    role = controller.main_window.find_role("LCR")
    role.set_model("K595")

    with pytest.raises(KeyError):
        controller.configure({"lcr_frequency": 10e3})


def test_configure_rejects_unknown_key(controller):
    with pytest.raises(KeyError):
        controller.configure({"no_such_key": 42})


def test_snapshot_reports_idle_application(controller):
    snapshot = controller.snapshot()
    assert snapshot["state"] == FSMState.IDLE
    assert snapshot["running"] is False
    assert snapshot["last_error"] is None


def test_snapshot_reports_fsm_state_updates(controller):
    controller.on_update({"fsm_state": FSMState.RAMPING})
    assert controller.snapshot()["state"] == FSMState.RAMPING


def test_last_error_recorded_and_cleared(controller):
    assert controller.last_error() is None

    controller.record_error(RuntimeError("Source compliance tripped!"))
    assert controller.snapshot()["last_error"] == (
        "RuntimeError: Source compliance tripped!"
    )

    controller.clear_last_error()
    assert controller.last_error() is None
