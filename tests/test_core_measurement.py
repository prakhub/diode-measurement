from queue import Queue
from threading import Event

import pytest

from diode_measurement.core.context import State
from diode_measurement.core.measurement import Measurement
from diode_measurement.core.role import Role, RoleConfig
from diode_measurement.core.station import Station


def role_config(
    resource_name: str,
    channel: str = "SMU1",
    disable_others: bool = False,
    reset_instrument: bool = False,
    enabled: bool = True,
) -> RoleConfig:
    return RoleConfig(
        enabled=enabled,
        model="A4155C",
        resource_name=resource_name,
        visa_library="",
        termination="\n",
        timeout=8.0,
        reset_instrument=reset_instrument,
        options={"smu.channel": channel, "channel.disable_others": disable_others},
    )


def create_measurement(roles: dict[Role, RoleConfig]) -> Measurement:
    # Only the role configurations are of interest, no resources are opened
    return Measurement.create(
        state=State(roles=roles),
        station=Station(),
        outbox_queue=Queue(),
        inbox_queue=Queue(),
        abort_event=Event(),
    )


def shared_measurement(smu: dict, elm: dict) -> Measurement:
    """Return a measurement with SMU and ELM roles on the same analyzer."""
    return create_measurement(
        {
            Role.SMU: role_config("GPIB1::18::INSTR", **smu),
            Role.ELM: role_config("GPIB1::18", **elm),
        }
    )


def test_shared_resources_valid():
    measurement = shared_measurement({"channel": "SMU1"}, {"channel": "SMU2"})
    assert measurement.check_shared_resources() is None


def test_shared_resources_same_channel():
    measurement = shared_measurement({"channel": "SMU1"}, {"channel": "SMU1"})
    with pytest.raises(RuntimeError, match="SMU1 selected more than once"):
        measurement.check_shared_resources()


def test_shared_resources_disable_others():
    measurement = shared_measurement(
        {"channel": "SMU1"},
        {"channel": "SMU2", "disable_others": True},
    )
    with pytest.raises(RuntimeError, match="disable other channels"):
        measurement.check_shared_resources()


def test_shared_resources_reset():
    measurement = shared_measurement(
        {"channel": "SMU1", "reset_instrument": True},
        {"channel": "SMU2"},
    )
    with pytest.raises(RuntimeError, match="reset instrument"):
        measurement.check_shared_resources()


def test_shared_resources_ignores_disabled_roles():
    measurement = shared_measurement(
        {"channel": "SMU1"},
        {"channel": "SMU1", "enabled": False},
    )
    assert measurement.check_shared_resources() is None


def test_separate_resources_not_checked():
    measurement = create_measurement(
        {
            Role.SMU: role_config("GPIB1::18::INSTR", reset_instrument=True),
            Role.ELM: role_config("GPIB1::14::INSTR", reset_instrument=True),
        }
    )
    assert measurement.check_shared_resources() is None
