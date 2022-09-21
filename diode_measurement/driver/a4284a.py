import time
from typing import Any, Dict, Optional

from .driver import LCRMeter, InstrumentError, handle_exception, parse_scpi_error

__all__ = ["A4284A"]


class A4284A(LCRMeter):

    def identity(self) -> str:
        return self._query("*IDN?").strip()

    def reset(self) -> None:
        self._write("*RST")

    def clear(self) -> None:
        self._write("*CLS")

    def next_error(self) -> Optional[InstrumentError]:
        return parse_scpi_error(self._query(":SYST:ERR?"))

    def configure(self, options: Dict[str, Any]) -> None:
        self._write(":INIT:CONT OFF")
        self._write(":TRIG:SOUR BUS")

        function_type = options.get("function.type", "CPRP")
        self.set_function_impedance_type(function_type)

        # Apterture
        integration_time = options.get("aperture.integration_time", "MED")
        averaging_rate = options.get("aperture.averaging_rate", 1)
        self.set_aperture(integration_time, averaging_rate)

        # Correction cable length
        correction_length = options.get("correction.length", 0)
        self.set_correction_length(correction_length)

        # Enable open correction
        correction_open_enabled = options.get("correction.open.enabled", False)
        self.set_correction_open_state(correction_open_enabled)

        # Enable short correction
        correction_short_enabled = options.get("correction.short.enabled", False)
        self.set_correction_short_state(correction_short_enabled)

        voltage = options.get("voltage", 1.0)
        self.set_amplitude_voltage(voltage)

        frequency = options.get("frequency", 1000.)
        self.set_amplitude_frequency(frequency)

        amplitude_alc = options.get("amplitude.alc", False)
        self.set_amplitude_alc(amplitude_alc)

    def get_output_enabled(self) -> bool:
        return self._query(":BIAS:STAT?") == "1"

    def set_output_enabled(self, enabled: bool) -> None:
        value = {False: "0", True: "1"}[enabled]
        self._write(f":BIAS:STAT {value}")

    def get_voltage_level(self) -> float:
        return float(self._query(":BIAS:VOLT:LEV?"))

    def set_voltage_level(self, level: float) -> None:
        self._write(f":BIAS:VOLT:LEV {level:.3E}")

    def set_voltage_range(self, level: float) -> None:
        pass  # TODO

    def set_current_compliance_level(self, level: float) -> None:
        raise RuntimeError("current compliance not supported")

    def compliance_tripped(self) -> bool:
        raise RuntimeError("current compliance not supported")

    def read_current(self):
        return 0

    def read_capacity(self) -> float:
        return self._fetch()

    def _fetch(self, timeout=10.0, interval=0.250) -> float:
        # Request operation complete
        self._write("*CLS")
        self._write_nowait("*OPC")
        # Initiate measurement
        self._write_nowait(":TRIG:IMM")
        threshold = time.time() + timeout
        interval = min(timeout, interval)
        while time.time() < threshold:
            # Read event status
            if int(self._query("*ESR?")) & 0x1:
                try:
                    result = self._query(":FETC?")
                    return float(result.split(",")[0])
                except Exception as exc:
                    raise RuntimeError(f"Failed to fetch LCR reading: {exc}") from exc
            time.sleep(interval)
        raise RuntimeError(f"LCR reading timeout, exceeded {timeout:G} s")

    def set_function_impedance_type(self, impedance_type: str) -> None:
        self._write(f":FUNC:IMP:TYPE {impedance_type}")

    def set_aperture(self, integration_time: str, averaging_rate: int) -> None:
        assert integration_time in ["SHOR", "MED", "LONG"]
        assert 1 <= averaging_rate <= 128
        self._write(f":APER {integration_time},{averaging_rate:d}")

    def set_correction_length(self, correction_length: int) -> None:
        assert correction_length in [0, 1, 2]
        self._write(f":CORR:LENG {correction_length:d}")

    def set_correction_open_state(self, state: bool) -> None:
        self._write(f":CORR:OPEN:STAT {state:d}")

    def set_correction_short_state(self, state: bool) -> None:
        self._write(f":CORR:SHOR:STAT {state:d}")

    def set_amplitude_voltage(self, voltage: float) -> None:
        self._write(f":VOLT {voltage:E}")

    def set_amplitude_frequency(self, frequency: float) -> None:
        self._write(f":FREQ {frequency:E}")

    def set_amplitude_alc(self, enabled: bool) -> None:
        self._write(f":AMPL:ALC {enabled:d}")

    @handle_exception
    def _write(self, message):
        self.resource.write(message)
        self.resource.query("*OPC?")

    @handle_exception
    def _write_nowait(self, message):
        self.resource.write(message)

    @handle_exception
    def _query(self, message):
        return self.resource.query(message).strip()
