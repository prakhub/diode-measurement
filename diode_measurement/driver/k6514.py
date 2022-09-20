import time
from typing import Any, Dict, List, Optional

from .driver import Electrometer, InstrumentError, handle_exception, parse_scpi_error

__all__ = ["K6514"]


class K6514(Electrometer):

    def identity(self) -> str:
        return self._query("*IDN?").strip()

    def reset(self) -> None:
        self._write("*RST")

    def clear(self) -> None:
        self._write("*CLS")

    def next_error(self) -> Optional[InstrumentError]:
        return parse_scpi_error(self._query(":SYST:ERR?"))

    def configure(self, options: Dict[str, Any]) -> None:
        self.set_format_elements(["READ"])
        self.set_sense_function("CURR")

        sense_range = options.get("sense.range", 200e-6)
        self.set_sense_current_range(sense_range)

        sense_auto_range = options.get("sense.auto_range", True)
        self.set_sense_current_range_auto(sense_auto_range)

        filter_mode = options.get("filter.mode", "MOV")
        self.set_sense_average_tcontrol(filter_mode)

        filter_count = options.get("filter.count", 1)
        self.set_sense_average_count(filter_count)

        filter_enable = options.get("filter.enable", False)
        self.set_sense_average_state(filter_enable)

        nplc = options.get("nplc", 5.0)
        self.set_sense_current_nplcycles(nplc)

    def get_output_enabled(self) -> bool:
        return False

    def set_output_enabled(self, enabled: bool) -> None:
        ...

    def get_voltage_level(self) -> float:
        return 0

    def set_voltage_level(self, level: float) -> None:
        ...

    def set_voltage_range(self, level: float) -> None:
        ...

    def set_current_compliance_level(self, level: float) -> None:
        ...

    def compliance_tripped(self) -> bool:
        return False

    def read_current(self, timeout=10.0, interval=0.250):
        # Request operation complete
        self._write("*CLS")
        self.resource.write("*OPC")
        # Initiate measurement
        self.resource.write(":INIT")
        threshold = time.time() + timeout
        interval = min(timeout, interval)
        while time.time() < threshold:
            # Read event status
            if int(self._query("*ESR?")) & 0x1:
                try:
                    result = self._query(":FETC?")
                    return float(result.split(",")[0])
                except Exception as exc:
                    raise RuntimeError(f"Failed to fetch ELM reading: {exc}") from exc
            time.sleep(interval)
        raise RuntimeError(f"Electrometer reading timeout, exceeded {timeout:G} s")

    def set_format_elements(self, elements: List[str]) -> None:
        value = ",".join(elements)
        self._write(f":FORM:ELEM {value}")

    def set_sense_function(self, function: str) -> None:
        self._write(f":SENS:FUNC '{function}'")

    def set_sense_current_range(self, level: float) -> None:
        self._write(f":SENS:CURR:RANG {level:E}")

    def set_sense_current_range_auto(self, enabled: bool) -> None:
        self._write(f":SENS:CURR:RANG:AUTO {enabled:d}")

    def set_sense_average_tcontrol(self, tcontrol: str) -> None:
        self._write(f":SENS:AVER:TCON {tcontrol}")

    def set_sense_average_count(self, count: int) -> None:
        self._write(f":SENS:AVER:COUN {count:d}")

    def set_sense_average_state(self, state: bool) -> None:
        self._write(f":SENS:AVER:STAT {state:d}")

    def set_sense_current_nplcycles(self, nplc: float) -> None:
        self._write(f":SENS:CURR:NPLC {nplc:E}")

    def set_zero_check_enabled(self, enabled: bool) -> None:
        self._write(f":SYST:ZCH {enabled:d}")

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
