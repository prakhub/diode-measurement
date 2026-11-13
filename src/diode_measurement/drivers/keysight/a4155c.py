"""Agilent (Keysight) 4155C Semiconductor Parameter Analyzer.

This driver uses a single SMU of the analyzer as an electrometer: the selected
SMU is defined as a constant voltage source (0 V by default) and its current
reading is returned by :meth:`measure_i`. The same driver serves as voltage
source (SMU role), in which case the measurement sets the voltage level.

Several roles may share one analyzer using different SMUs, eg. SMU1 as source
and SMU2 as electrometer. Every role opens its own session, so none of them may
reset the analyzer or disable the other channels while configuring.

The instrument is driven in its native SCPI command mode using a sampling
measurement with a small number of sample points. A reading is acquired by

.. code::

    :PAGE:SCON:MEAS:SING     # trigger a single sampling measurement
    *OPC                     # request operation complete
    *ESR?                    # poll until bit 0 is set
    :DATA? 'I1'              # read the sample values of the SMU

Note that the analyzer only applies the constant source value while a
measurement is running unless the channel is declared a *standby* channel.
Standby is enabled while zero check is disabled, so that the device under test
stays connected to a defined potential between readings.

Command notes, verified against a 4155C with firmware 03.10:

* The measurement mode lives on the channel definition page
  (``:PAGE:CHAN:MODE``) and must be set to ``SAMP`` before any
  ``:PAGE:MEAS:SAMP:...`` command, which is otherwise rejected with
  ``+147 Ineffective page in this setup``.
* Measurement ranging is per channel (``:PAGE:MEAS:MSET:SMU<n>:RANG``) and only
  accepted once the channel is defined, otherwise the analyzer replies
  ``+181 Illegal setup. Invalid command``. Ranges below the lowest range of the
  unit are silently clamped.
* ASCII data returned by ``:DATA?`` carries no status character on this
  firmware, so compliance is detected by comparing the reading against the
  compliance setting, see :meth:`compliance_tripped`.

An SMU reports current flowing *out of* its force terminal as positive, while
an electrometer such as the K6514 reports current flowing *into* its input as
positive. Sitting at the same place in a circuit the analyzer therefore returns
the opposite sign of the electrometer it replaces, which is compensated by
default, see :meth:`set_invert_sign_enabled`.
"""

import time
from collections.abc import Mapping
from typing import Any

from diode_measurement.core.driver import InstrumentError, handle_exception
from diode_measurement.core.resource import Resource
from diode_measurement.core.scpi import parse_scpi_error

__all__ = ["A4155CAdapter"]


def parse_value(text: str) -> tuple[str, float]:
    """Return status character and value of a measurement data item.

    The analyzer prefixes every ASCII data item with a status character, eg.
    ``N+1.23456E-09``. An empty status character is returned if absent.
    """
    text = text.strip()
    status = ""
    if text[:1].isalpha():
        status, text = text[0], text[1:]
    try:
        value = float(text)
    except ValueError as exc:
        raise RuntimeError(f"Failed to parse reading: {text!r}") from exc
    return status, value


class A4155CAdapter:
    CHANNELS: tuple[str, ...] = ("SMU1", "SMU2", "SMU3", "SMU4")
    """Available source monitor units."""

    INTEGRATION_TIMES: tuple[str, ...] = ("SHOR", "MED", "LONG")
    """Available integration times (short, medium, long)."""

    RANGE_MODES: tuple[str, ...] = ("AUTO", "LIM", "FIX")
    """Available ranging modes (auto, limited auto, fixed)."""

    COMPLIANCE_STATES: tuple[str, ...] = ("C", "T")
    """Status characters indicating a reached compliance."""

    MAX_VOLTAGE: float = 100.0
    """Output voltage limit of the medium power SMUs (SMU1 to SMU4)."""

    measurement_timeout: float = 60.0
    """Timeout in seconds while waiting for a measurement to complete."""

    def __init__(self, resource: Resource) -> None:
        self._resource: Resource = resource
        self.channel: str = self.CHANNELS[0]
        self._use_standby: bool = True
        self._invert_sign: bool = True
        self._voltage_level: float = 0.0
        self._current_compliance: float = 0.0
        self._status_compliance: bool = False
        self._compliance_tripped: bool = False
        self._channel_defined: bool = False

    # Channel

    def set_channel(self, channel: str) -> None:
        """Select the SMU used as electrometer, eg. ``SMU1``."""
        channel = format(channel).upper().strip()
        if channel not in self.CHANNELS:
            raise ValueError(f"Invalid SMU channel: {channel!r}")
        self.channel = channel

    @property
    def channel_index(self) -> int:
        """Return the one based index of the selected SMU."""
        return self.CHANNELS.index(self.channel) + 1

    @property
    def current_name(self) -> str:
        return f"I{self.channel_index:d}"

    @property
    def voltage_name(self) -> str:
        return f"V{self.channel_index:d}"

    # Common commands

    def identify(self) -> str:
        return self._query("*IDN?").strip()

    def reset(self) -> None:
        self._write("*RST")
        self._channel_defined = False

    def clear(self) -> None:
        self._write("*CLS")

    def next_error(self) -> InstrumentError | None:
        return parse_scpi_error(self._query(":SYST:ERR?"))

    def define_channel(self) -> None:
        """Define the selected SMU as constant voltage source.

        The measurement mode selects which measurement setup pages are
        effective and must be set before any of them is accessed.
        """
        self.set_measurement_mode("SAMP")
        self.set_channel_voltage_name(self.voltage_name)
        self.set_channel_current_name(self.current_name)
        self.set_channel_mode("V")
        self.set_channel_function("CONS")
        self._channel_defined = True

    def ensure_channel_defined(self) -> None:
        """Define the channel unless this was already done.

        The measurement is set up by :meth:`configure`, but the application
        may set a source level or take a reading before that, which the
        analyzer rejects while the sampling page is not yet effective.
        """
        if not self._channel_defined:
            self.define_channel()

    def configure(self, options: Mapping[str, Any]) -> None:
        self.set_channel(options.get("smu.channel", self.CHANNELS[0]))

        self._use_standby = options.get("channel.standby", True)

        self.set_invert_sign_enabled(options.get("sense.invert_sign", True))

        if options.get("channel.disable_others", True):
            self.disable_all_channels()

        self.define_channel()

        # Start with a disconnected output, see set_zero_check_enabled()
        if self._use_standby:
            self.set_channel_standby(False)

        # Ranging is only accepted for a defined channel
        range_mode = options.get("sense.range_mode", "AUTO")
        self.set_range_mode(range_mode)

        if range_mode != "AUTO":
            self.set_range(options.get("sense.range", 1e-9))

        integration_time = options.get("integration.time", "MED")
        self.set_integration_time(integration_time)

        if integration_time == "LONG":
            self.set_integration_time_long(options.get("integration.nplc", 1))

        self.set_sampling_points(options.get("sampling.points", 1))
        self.set_sampling_interval(options.get("sampling.interval", 2e-3))
        self.set_sampling_hold_time(options.get("sampling.hold_time", 0.0))

        # Used as SMU the source level and compliance are set by the measurement
        if "source.voltage" in options:
            self.set_voltage_level(options["source.voltage"])
        if "source.current_compliance" in options:
            self.set_current_compliance_level(options["source.current_compliance"])

        self.set_format_data("ASC")

    # Channel definition

    def disable_all_channels(self) -> None:
        self._write(":PAGE:CHAN:ALL:DIS")

    def set_channel_mode(self, mode: str) -> None:
        self._write(f":PAGE:CHAN:{self.channel}:MODE {mode}")

    def set_channel_function(self, function: str) -> None:
        self._write(f":PAGE:CHAN:{self.channel}:FUNC {function}")

    def set_channel_voltage_name(self, name: str) -> None:
        self._write(f":PAGE:CHAN:{self.channel}:VNAME '{name}'")

    def set_channel_current_name(self, name: str) -> None:
        self._write(f":PAGE:CHAN:{self.channel}:INAME '{name}'")

    def set_channel_standby(self, enabled: bool) -> None:
        """Keep the constant source value applied between measurements."""
        state = "ON" if enabled else "OFF"
        self._write(f":PAGE:CHAN:{self.channel}:STAN {state}")

    def get_channel_standby(self) -> bool:
        return bool(int(self._query(f":PAGE:CHAN:{self.channel}:STAN?")))

    # Measurement setup

    def set_measurement_mode(self, mode: str) -> None:
        """Select the measurement mode, eg. ``SWE`` or ``SAMP``.

        The mode lives on the channel definition page and decides which
        measurement setup pages are effective.
        """
        self._write(f":PAGE:CHAN:MODE {mode}")

    def set_integration_time(self, integration_time: str) -> None:
        integration_time = format(integration_time).upper().strip()
        if integration_time not in self.INTEGRATION_TIMES:
            raise ValueError(f"Invalid integration time: {integration_time!r}")
        self._write(f":PAGE:MEAS:MSET:ITIM {integration_time}")

    def set_integration_time_long(self, nplc: int) -> None:
        """Set number of power line cycles (1 to 100) for long integration."""
        nplc = int(nplc)
        if not 1 <= nplc <= 100:
            raise ValueError("Integration time must be between 1 and 100 PLC")
        self._write(f":PAGE:MEAS:MSET:ITIM:LONG {nplc:d}")

    def set_range_mode(self, mode: str) -> None:
        """Set the measurement ranging mode of the selected channel."""
        mode = format(mode).upper().strip()
        if mode not in self.RANGE_MODES:
            raise ValueError(f"Invalid range mode: {mode!r}")
        self._write(f":PAGE:MEAS:MSET:{self.channel}:RANG:MODE {mode}")

    def set_range(self, level: float) -> None:
        """Set the fixed, respectively lowest measurement range in Ampere.

        Values below the lowest range of the unit are clamped by the analyzer.
        """
        self._write(f":PAGE:MEAS:MSET:{self.channel}:RANG {level:.5E}")

    def get_range(self) -> float:
        return float(self._query(f":PAGE:MEAS:MSET:{self.channel}:RANG?"))

    def set_sampling_points(self, points: int) -> None:
        points = int(points)
        if not 1 <= points <= 1201:
            raise ValueError("Number of samples must be between 1 and 1201")
        self._write(f":PAGE:MEAS:SAMP:POIN {points:d}")

    def set_sampling_interval(self, interval: float) -> None:
        if not 2e-3 <= interval <= 65.535:
            raise ValueError("Sampling interval must be between 2 ms and 65.535 s")
        self._write(f":PAGE:MEAS:SAMP:IINT {interval:.5E}")

    def set_sampling_hold_time(self, hold_time: float) -> None:
        if not 0.0 <= hold_time <= 655.35:
            raise ValueError("Hold time must be between 0 s and 655.35 s")
        self._write(f":PAGE:MEAS:SAMP:HTIM {hold_time:.5E}")

    def set_format_data(self, format_data: str) -> None:
        self._write(f":FORM:DATA {format_data}")

    # Source

    def get_voltage_level(self) -> float:
        return self._voltage_level

    def set_voltage_level(self, level: float) -> None:
        if abs(level) > self.MAX_VOLTAGE:
            raise ValueError(
                f"Voltage {level:G} V exceeds {self.channel} limit of ±{self.MAX_VOLTAGE:G} V"
            )
        self.ensure_channel_defined()
        self._write(f":PAGE:MEAS:SAMP:CONS:{self.channel} {level:.5E}")
        self._voltage_level = level

    def set_voltage_range(self, level: float) -> None: ...  # auto ranging only

    def set_current_compliance_level(self, level: float) -> None:
        self.ensure_channel_defined()
        self._write(f":PAGE:MEAS:SAMP:CONS:{self.channel}:COMP {level:.5E}")
        self._current_compliance = level

    def compliance_tripped(self) -> bool:
        return self._compliance_tripped

    def _detect_compliance(self, current: float) -> bool:
        """Return True if a reading indicates a reached current compliance.

        The analyzer returns ASCII data without a status character, so a
        reading at the compliance level is the only available indication.
        """
        if self._status_compliance:
            return True
        compliance = abs(self._current_compliance)
        if not compliance:
            return False
        return abs(current) >= compliance * 0.999

    def get_output_enabled(self) -> bool:
        return self.get_channel_standby()

    def set_output_enabled(self, enabled: bool) -> None:
        if self._use_standby:
            self.set_channel_standby(enabled)

    def set_zero_check_enabled(self, enabled: bool) -> None:
        """Disconnect (enabled) or apply (disabled) the constant source value."""
        if self._use_standby:
            self.set_channel_standby(not enabled)

    # Measurement

    def set_invert_sign_enabled(self, enabled: bool) -> None:
        """Return currents with the sign convention of an electrometer.

        The analyzer counts current sourced out of the force terminal as
        positive, an electrometer counts current flowing into its input as
        positive. Inverting matches readings taken with an electrometer at the
        same place in the circuit.
        """
        self._invert_sign = enabled

    def is_invert_sign_enabled(self) -> bool:
        return self._invert_sign

    def _apply_sign(self, current: float) -> float:
        if not self._invert_sign:
            return current
        # avoid turning a zero reading into a negative zero
        return -current if current else current

    def measure_i(self) -> float:
        self._trigger_measurement()
        current = self._fetch(self.current_name)
        self._compliance_tripped = self._detect_compliance(current)
        return self._apply_sign(current)

    def measure_iv(self) -> tuple[float, float]:
        self._trigger_measurement()
        current = self._fetch(self.current_name)
        self._compliance_tripped = self._detect_compliance(current)
        return self._apply_sign(current), self._fetch(self.voltage_name)

    def measure_v(self) -> float:
        self._trigger_measurement()
        return self._fetch(self.voltage_name)

    def _trigger_measurement(self, interval: float = 0.100) -> None:
        self.ensure_channel_defined()
        timeout = self.measurement_timeout
        self._write_nowait("*CLS")
        self._write_nowait(":PAGE:SCON:MEAS:SING")
        # Request operation complete
        self._write_nowait("*OPC")
        threshold = time.time() + timeout
        interval = min(timeout, interval)
        while time.time() < threshold:
            # Read event status
            if int(self._query("*ESR?")) & 0x1:
                return
            time.sleep(interval)
        self._write_nowait(":PAGE:SCON:STOP")
        raise RuntimeError(f"Measurement timeout, exceeded {timeout:G} s")

    def _fetch(self, name: str) -> float:
        result = self._query(f":DATA? '{name}'")
        items = [item for item in result.split(",") if item.strip()]
        if not items:
            raise RuntimeError(f"Failed to fetch reading {name!r}: {result!r}")
        values = []
        status_compliance = False
        for item in items:
            status, value = parse_value(item)
            if status in self.COMPLIANCE_STATES:
                status_compliance = True
            values.append(value)
        self._status_compliance = status_compliance
        return sum(values) / len(values)

    # Resource

    @handle_exception
    def _write(self, message):
        self._resource.write(message)
        self._resource.query("*OPC?")

    @handle_exception
    def _write_nowait(self, message):
        self._resource.write(message)

    @handle_exception
    def _query(self, message):
        return self._resource.query(message).strip()
