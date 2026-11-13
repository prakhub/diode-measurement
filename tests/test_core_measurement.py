import pytest

from diode_measurement.core.measurement import Measurement
from diode_measurement.state import State


def shared_measurement(smu: dict, elm: dict) -> Measurement:
    """Return a measurement with SMU and ELM roles on the same analyzer."""
    state = State()
    state.update(
        {
            "roles": {
                "smu": {"resource_name": "GPIB1::18::INSTR", **smu},
                "elm": {"resource_name": "GPIB1::18", **elm},
            }
        }
    )
    measurement = Measurement(state)
    # Only the role names are of interest, no resources are opened
    measurement._instruments = {"smu": None, "elm": None}
    return measurement


def options(channel: str, disable_others: bool = False) -> dict:
    return {"smu.channel": channel, "channel.disable_others": disable_others}


def test_shared_resources_valid():
    measurement = shared_measurement(
        {"options": options("SMU1")},
        {"options": options("SMU2")},
    )
    assert measurement.check_shared_resources() is None


def test_shared_resources_same_channel():
    measurement = shared_measurement(
        {"options": options("SMU1")},
        {"options": options("SMU1")},
    )
    with pytest.raises(RuntimeError, match="SMU1 selected more than once"):
        measurement.check_shared_resources()


def test_shared_resources_disable_others():
    measurement = shared_measurement(
        {"options": options("SMU1")},
        {"options": options("SMU2", disable_others=True)},
    )
    with pytest.raises(RuntimeError, match="disable other channels"):
        measurement.check_shared_resources()


def test_shared_resources_reset():
    measurement = shared_measurement(
        {"options": options("SMU1"), "reset_instrument": True},
        {"options": options("SMU2")},
    )
    with pytest.raises(RuntimeError, match="reset instrument"):
        measurement.check_shared_resources()


def test_separate_resources_not_checked():
    state = State()
    state.update(
        {
            "roles": {
                "smu": {"resource_name": "GPIB1::18::INSTR", "reset_instrument": True},
                "elm": {"resource_name": "GPIB1::14::INSTR", "reset_instrument": True},
            }
        }
    )
    measurement = Measurement(state)
    measurement._instruments = {"smu": None, "elm": None}
    assert measurement.check_shared_resources() is None
