import json
from concurrent.futures import Future
from typing import Any, cast

import pytest

from diode_measurement.controller import GeneralConfig, Snapshot
from diode_measurement.core.measurement import FSMState
from diode_measurement.core.role import Role
from diode_measurement.plugins.rpcserver import (
    ConfigureEvent,
    RPCHandler,
    StartEvent,
    create_general_config,
    is_finite,
    json_dict,
)


def test_is_finite():
    assert is_finite(0)
    assert is_finite(-42.0)
    assert is_finite("foo")
    assert not is_finite(float("nan"))
    assert not is_finite(float("+inf"))
    assert not is_finite(float("-inf"))


def test_json_dict():
    data_in = {"a": float("nan"), "b": 42.0, "c": "42"}
    data_out = {"a": None, "b": 42.0, "c": "42"}
    assert json_dict(data_in) == data_out


def test_create_general_config_leaves_unspecified():
    assert create_general_config() == GeneralConfig()


def test_create_general_config_converts_instruments_to_roles():
    config = create_general_config(
        measurement_instruments=["smu", "lcr"],
        source_instrument="smu2",
        bias_source_instrument="smu",
    )
    assert config.measurement_roles == [Role.SMU, Role.LCR]
    assert config.source_role == Role.SMU2
    assert config.bias_source_role == Role.SMU


def test_create_general_config_output_and_lcr():
    config = create_general_config(
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
    assert config == GeneralConfig(
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


def test_create_general_config_keeps_falsy_values():
    """Zero volt and disabled output must not be dropped as unspecified."""
    config = create_general_config(
        begin_voltage=0.0, output_enabled=False, filename_suffix=""
    )
    assert config.begin_voltage == 0.0
    assert config.output_enabled is False
    assert config.filename_suffix == ""


def test_create_general_config_rejects_unknown_parameter():
    with pytest.raises(TypeError):
        create_general_config(no_such=1)  # type: ignore[call-arg]


class FakeAction:
    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled

    def isEnabled(self) -> bool:
        return self._enabled


class FakeMainWindow:
    def __init__(self, enabled: bool = True) -> None:
        self.start_action = FakeAction(enabled)


class FakeController:
    """Stands in for the parts of the controller used by RPC events."""

    def __init__(self, enabled: bool = True) -> None:
        self.main_window = FakeMainWindow(enabled)
        self.configs: list[GeneralConfig] = []
        self.started = False

    def configure(self, config: GeneralConfig) -> None:
        self.configs.append(config)

    def request_start(self) -> None:
        self.started = True

    def snapshot(self) -> Snapshot:
        return Snapshot(
            state=FSMState.RAMPING,
            measurement_type="iv",
            sample="A1",
            running=True,
            filename=None,
            last_error=None,
            source_voltage=None,
            smu_voltage=None,
            smu_current=float("nan"),
            smu2_voltage=None,
            smu2_current=None,
            elm_current=None,
            elm2_current=None,
            lcr_capacity=None,
            dmm_temperature=None,
            tcu_temperature=None,
            tcu_humidity=None,
        )


class FakeEventHandler:
    """Runs events synchronously, as the Qt timer would on the main thread."""

    def __init__(self, controller) -> None:
        self.controller = controller

    def notify(self, event):
        future: Future = Future()
        try:
            future.set_result(event(self.controller))
        except Exception as exc:
            future.set_exception(exc)
        return future


def test_configure_event_does_not_start_measurement():
    controller = FakeController()
    ConfigureEvent(GeneralConfig(filename="A1_irrad_iv"))(cast(Any, controller))

    assert controller.configs == [GeneralConfig(filename="A1_irrad_iv")]
    assert not controller.started


def test_start_event_starts_measurement():
    controller = FakeController()
    StartEvent(GeneralConfig(end_voltage=-200.0))(cast(Any, controller))

    assert controller.configs == [GeneralConfig(end_voltage=-200.0)]
    assert controller.started


def test_start_event_refuses_while_measurement_active():
    controller = FakeController(enabled=False)

    with pytest.raises(RuntimeError, match="still active"):
        StartEvent(GeneralConfig())(cast(Any, controller))

    assert not controller.configs
    assert not controller.started


def handle(controller: FakeController, request: dict[str, Any]) -> dict[str, Any]:
    rpc_handler = RPCHandler(cast(Any, FakeEventHandler(controller)))
    # handle() returns the JSON-RPC response object, despite its annotation
    response: Any = rpc_handler.handle(json.dumps(request))
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
                "source_instrument": "smu",
                "output_dir": "/data/A1",
                "filename": "A1_irrad_iv",
                "filename_suffix": "iv_forward",
            },
            "id": 1,
        },
    )
    assert "error" not in response
    (config,) = controller.configs
    assert config.source_role == Role.SMU
    assert config.filename == "A1_irrad_iv"
    assert config.filename_suffix == "iv_forward"
    assert controller.started


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
    assert controller.configs == [GeneralConfig(lcr_frequency=100e3)]
    assert not controller.started


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
    assert not controller.started


def test_rpc_state_serializes_enum_and_nan():
    controller = FakeController()
    response = handle(controller, {"jsonrpc": "2.0", "method": "state", "id": 1})

    assert response["result"]["state"] == "ramping"
    assert response["result"]["running"] is True
    assert response["result"]["last_error"] is None
    assert response["result"]["smu_current"] is None
