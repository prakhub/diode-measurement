import json

from diode_measurement.plugins.rpcserver import (
    ConfigureEvent,
    RPCHandler,
    StartEvent,
    collect_parameters,
    is_finite,
    json_dict,
)
from diode_measurement.state import FSMState


def test_is_finite():
    assert is_finite(0)
    assert is_finite(-42.)
    assert is_finite("foo")
    assert not is_finite(float("nan"))
    assert not is_finite(float("+inf"))
    assert not is_finite(float("-inf"))


def test_json_dict():
    data_in = {"a": float("nan"), "b": 42., "c": "42"}
    data_out = {"a": None, "b": 42., "c": "42"}
    assert json_dict(data_in) == data_out


def test_collect_parameters_omits_unspecified():
    assert collect_parameters() == {}


def test_collect_parameters_renames_measurement_instruments():
    parameters = collect_parameters(measurement_instruments=["smu", "lcr"])
    assert parameters == {"measurement_roles": ["smu", "lcr"]}


def test_collect_parameters_output_and_lcr():
    parameters = collect_parameters(
        measurement_type="cv_diode",
        end_voltage=-200.0,
        step_voltage=1.0,
        compliance=25e-6,
        sample="A1",
        output_enabled=True,
        output_dir="/data/A1",
        filename="A1_irrad_cv",
        filename_suffix="10kHz",
        lcr_amplitude=0.5,
        lcr_frequency=10e3,
    )
    assert parameters == {
        "measurement_type": "cv_diode",
        "end_voltage": -200.0,
        "step_voltage": 1.0,
        "compliance": 25e-6,
        "sample": "A1",
        "output_enabled": True,
        "output_dir": "/data/A1",
        "filename": "A1_irrad_cv",
        "filename_suffix": "10kHz",
        "lcr_amplitude": 0.5,
        "lcr_frequency": 10e3,
    }


def test_collect_parameters_keeps_falsy_values():
    """Zero volt and disabled output must not be dropped as unspecified."""
    parameters = collect_parameters(
        begin_voltage=0.0, output_enabled=False, filename_suffix=""
    )
    assert parameters == {
        "begin_voltage": 0.0,
        "output_enabled": False,
        "filename_suffix": "",
    }


class FakeAction:
    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled
        self.triggered = False

    def isEnabled(self) -> bool:
        return self._enabled

    def trigger(self) -> None:
        self.triggered = True


class FakeMainWindow:
    def __init__(self, enabled: bool = True) -> None:
        self.start_action = FakeAction(enabled)


class FakeController:
    def __init__(self, enabled: bool = True) -> None:
        self.main_window = FakeMainWindow(enabled)
        self.configured: dict = {}

    def configure(self, parameters) -> None:
        self.configured.update(parameters)

    def snapshot(self) -> dict:
        return {
            "state": FSMState.RAMPING,
            "running": True,
            "last_error": None,
            "smu_current": float("nan"),
        }


class FakeEventHandler:
    """Runs events synchronously, as the Qt timer would on the main thread."""

    def __init__(self, controller) -> None:
        self.controller = controller

    def notify(self, event):
        from concurrent.futures import Future

        future: Future = Future()
        try:
            future.set_result(event(self.controller))
        except Exception as exc:
            future.set_exception(exc)
        return future


def test_configure_event_does_not_start_measurement():
    controller = FakeController()
    ConfigureEvent({"filename": "A1_irrad_iv"})(controller)

    assert controller.configured == {"filename": "A1_irrad_iv"}
    assert not controller.main_window.start_action.triggered


def test_start_event_triggers_start_action():
    controller = FakeController()
    StartEvent({"end_voltage": -200.0})(controller)

    assert controller.configured == {"end_voltage": -200.0}
    assert controller.main_window.start_action.triggered


def test_start_event_refuses_while_measurement_active():
    controller = FakeController(enabled=False)

    try:
        StartEvent({})(controller)
    except RuntimeError as exc:
        assert "still active" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")

    assert not controller.configured


def handle(controller, request) -> dict:
    rpc_handler = RPCHandler(FakeEventHandler(controller))
    response = rpc_handler.handle(json.dumps(request))
    return json.loads(response.json)


def test_rpc_start_applies_parameters():
    controller = FakeController()
    response = handle(
        controller,
        {
            "jsonrpc": "2.0",
            "method": "start",
            "params": {
                "measurement_type": "iv",
                "end_voltage": 3.0,
                "step_voltage": 0.01,
                "compliance": 1e-3,
                "output_dir": "/data/A1",
                "filename": "A1_irrad_iv",
                "filename_suffix": "iv_forward",
            },
            "id": 1,
        },
    )
    assert "error" not in response
    assert controller.configured["filename"] == "A1_irrad_iv"
    assert controller.configured["filename_suffix"] == "iv_forward"
    assert controller.main_window.start_action.triggered


def test_rpc_configure_applies_parameters_without_starting():
    controller = FakeController()
    response = handle(
        controller,
        {
            "jsonrpc": "2.0",
            "method": "configure",
            "params": {"lcr_frequency": 100e3},
            "id": 1,
        },
    )
    assert "error" not in response
    assert controller.configured == {"lcr_frequency": 100e3}
    assert not controller.main_window.start_action.triggered


def test_rpc_start_while_active_returns_error():
    controller = FakeController(enabled=False)
    response = handle(controller, {"jsonrpc": "2.0", "method": "start", "id": 1})

    assert response["error"]["data"]["message"].endswith("still active.")


def test_rpc_rejects_unknown_parameter():
    controller = FakeController()
    response = handle(
        controller,
        {"jsonrpc": "2.0", "method": "start", "params": {"no_such": 1}, "id": 1},
    )
    assert "error" in response
    assert not controller.main_window.start_action.triggered


def test_rpc_state_serializes_enum_and_nan():
    controller = FakeController()
    response = handle(controller, {"jsonrpc": "2.0", "method": "state", "id": 1})

    assert response["result"]["state"] == "ramping"
    assert response["result"]["running"] is True
    assert response["result"]["last_error"] is None
    assert response["result"]["smu_current"] is None
