from typing import Any, Dict, Optional

from .driver import SourceMeter, InstrumentError, handle_exception, parse_scpi_error

__all__ = ["K2470"]


class K2470(SourceMeter):

    def identity(self) -> str:
        return self._query("*IDN?")

    def reset(self) -> None:
        self._write("*RST")

    def clear(self) -> None:
        self._write("*CLS")

    def next_error(self) -> Optional[InstrumentError]:
        return parse_scpi_error(self._query(":SYST:ERR?"))

    def configure(self, options: Dict[str, Any]) -> None:
        route_terminals = options.get("route.terminals", "FRON")
        self.set_route_terminals(route_terminals)

        self.set_source_function("VOLT")

        filter_mode = options.get("filter.mode", "MOV")
        self.set_sense_current_average_tcontrol(filter_mode)

        filter_count = options.get("filter.count", 1)
        self.set_sense_current_average_count(filter_count)

        filter_enable = options.get("filter.enable", False)
        self.set_sense_current_average_enable(filter_enable)

        nplc = options.get("nplc", 1.0)
        self.set_sense_current_nplc(nplc)

    def get_output_enabled(self) -> bool:
        return self._query(":OUTP:STAT?") == "1"

    def set_output_enabled(self, enabled: bool) -> None:
        value = {False: "0", True: "1"}[enabled]
        self._write(f":OUTP:STAT {value}")

    def get_voltage_level(self) -> float:
        return float(self._query(":SOUR:VOLT:LEV?"))

    def set_voltage_level(self, level: float) -> None:
        self._write(f":SOUR:VOLT:LEV {level:.3E}")

    def set_voltage_range(self, level: float) -> None:
        self._write(f":SOUR:VOLT:RANG {level:.3E}")

    def set_current_compliance_level(self, level: float) -> None:
        self._write(f":SOUR:VOLT:ILIM:LEV {level:.3E}")

    def compliance_tripped(self) -> bool:
        return self._query(":SOUR:VOLT:ILIM:LEV:TRIP?") == "1"

    def read_current(self) -> float:
        return float(self._query(":MEAS:CURR?"))

    def read_voltage(self) -> float:
        return float(self._query(":MEAS:VOLT?"))

    def set_route_terminals(self, terminal: str) -> None:
        self._write(f":ROUT:TERM {terminal}")

    def set_source_function(self, function: str) -> None:
        self._write(f":SOUR:FUNC {function}")

    def set_sense_current_average_tcontrol(self, tcontrol: str) -> None:
        self._write(f":SENS:CURR:AVER:TCON {tcontrol}")

    def set_sense_current_average_count(self, count: int) -> None:
        self._write(f":SENS:CURR:AVER:COUN {count:d}")

    def set_sense_current_average_enable(self, state: bool) -> None:
        self._write(f":SENS:CURR:AVER:STAT {state:d}")

    def set_sense_current_nplc(self, nplc: float) -> None:
        self._write(f":SENS:CURR:NPLC {nplc:E}")

    @handle_exception
    def _write(self, message):
        self.resource.write(message)
        self.resource.query("*OPC?")

    @handle_exception
    def _query(self, message):
        return self.resource.query(message).strip()
