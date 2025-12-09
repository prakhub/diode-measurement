from typing import List, Tuple

from .driver import SourceMeter, handle_exception

__all__ = ["K6847"]


class K6847(SourceMeter):

    def identity(self) -> str:
        return self._query("*IDN?")

    def reset(self) -> None:
        self._write("*RST")

    def clear(self) -> None:
        self._write("*CLS")

    def next_error(self) -> Tuple[int, str]:
        result = self._query(":SYST:ERR?")
        try:
            code, message = result.split(",", 1)
            code = int(code)
            message = message.strip().strip('"')
            return code, message
        except Exception as exc:
            raise RuntimeError(f"Failed to parse error message: {result!r}") from exc

    def configure(self, options: dict) -> None:
        self.set_sense_function("CURR")
        sense_range = options.get("sense.range", 20e-6)
        self.set_current_range(sense_range)

        sense_auto_range = options.get("sense.auto_range", True)
        self.set_current_range_auto(sense_auto_range)

        # K6487 averaging and NPLC may not be supported or use different commands
        nplc = options.get("nplc", 1.0)
        self.set_sense_current_nplc(nplc)
        filter_mode = options.get("filter.mode", "MOV")
        self.set_sense_current_average_tcontrol(filter_mode)
        filter_count = options.get("filter.count", 10)
        self.set_sense_current_average_count(filter_count)
        filter_enable = options.get("filter.enable", False)
        self.set_sense_current_average_enable(filter_enable)

    def get_output_enabled(self) -> bool:
        return self._query(":SOUR:VOLT:STAT?") == "1"

    def set_output_enabled(self, enabled: bool) -> None:
        value = "ON" if enabled else "OFF"
        self._write(f":SOUR:VOLT:STAT {value}")

    def get_voltage_level(self) -> float:
        return float(self._query(":SOUR:VOLT:LEV?"))

    def set_voltage_level(self, level: float) -> None:
        self._write(f":SOUR:VOLT:LEV {level:E}")

    def set_voltage_range(self, level: float) -> None:
        self._write(f":SOUR:VOLT:RANG {level:E}")

    def set_current_compliance_level(self, level: float) -> None:
        self._write(f":SOUR:VOLT:ILIM {level:E}")

    def compliance_tripped(self) -> bool:
        return self._query(":SOUR:VOLT:INT:FAIL?") == "1"

    def measure_i(self) -> float:
        result = self._query(":READ?")
        print(f"DEBUG: K6847 measure_i raw result: {result}")
        # Format appears to be: CURRENT,TIMESTAMP,OTHER
        parts = result.split(",")
        current_str = parts[0].rstrip("A")  # Remove the 'A' suffix
        return float(current_str)

    def measure_v(self) -> float:
        # K6847 doesn't measure actual voltage, return the set voltage level
        return self.get_voltage_level()

    def measure_iv(self) -> Tuple[float, float]:
        i = self.measure_i()
        v = self.measure_v()
        return i, v

    def set_sense_function(self, function: str) -> None:
        self._write(f":SENS:FUNC '{function}'")

    def set_current_range(self, level: float) -> None:
        self._write(f":CURR:RANG {level:E}")

    def set_current_range_auto(self, enabled: bool) -> None:
        value = "ON" if enabled else "OFF"
        self._write(f":CURR:RANG:AUTO {value}")

    def set_zero_check_enabled(self, enabled: bool) -> None:
        value = "ON" if enabled else "OFF"
        self._write(f":SYST:ZCH {value}")

    def acquire_zero_correction(self) -> None:
        """Acquire zero correction value."""
        self._write(":SYST:ZCOR:ACQ")

    def set_zero_correction_enabled(self, enabled: bool) -> None:
        value = "ON" if enabled else "OFF"
        self._write(f":SYST:ZCOR {value}")

    def set_format_elements(self, elements: List[str]) -> None:
        value = ",".join(elements)
        self._write(f":FORM:ELEM {value}")

    def set_sense_current_average_tcontrol(self, tcontrol: str) -> None:
        self._write(f":SENS:CURR:AVER:TCON {tcontrol}")

    def set_sense_current_average_count(self, count: int) -> None:
        self._write(f":SENS:CURR:AVER:COUN {count:d}")

    def set_sense_current_average_enable(self, state: bool) -> None:
        value = "ON" if state else "OFF"
        self._write(f":SENS:CURR:AVER:STAT {value}")

    def set_sense_current_nplc(self, nplc: float) -> None:
        self._write(f":SENS:CURR:NPLC {nplc:E}")

    def is_interlock(self) -> bool:
        """Return status of the interlock."""
        return not bool(int(self._query(":SOUR:VOLT:INT:FAIL?")))

    @handle_exception
    def _write(self, message):
        self.resource.write(message)
        self.resource.query("*OPC?")

    @handle_exception
    def _query(self, message):
        return self.resource.query(message).strip()
