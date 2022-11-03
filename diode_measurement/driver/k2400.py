from .driver import SourceMeter, handle_exception

__all__ = ["K2400"]


class K2400(SourceMeter):

    _format_element = None

    def identity(self) -> str:
        return self._query("*IDN?")

    def reset(self) -> None:
        self._write("*RST")

    def clear(self) -> None:
        self._write("*CLS")

    def error_state(self) -> tuple:
        code, message = self._query(":SYST:ERR?").split(",")
        code = int(code)
        message = message.strip().strip('"')
        return code, message

    def configure(self, options: dict) -> None:
        beeper_state = options.get("beeper.state", False)
        self.set_system_beeper_state(beeper_state)

        route_terminals = options.get("route.terminals", "FRON")
        self.set_route_terminals(route_terminals)

        self.set_source_function("VOLT")

        self._write(":FORM:ELEM CURR")  # return only current for read/fetch
        self._format_element = "CURR"

        filter_mode = options.get("filter.mode", "MOV")
        self.set_sense_average_tcontrol(filter_mode)

        filter_count = options.get("filter.count", 10)
        self.set_sense_average_count(filter_count)

        filter_enable = options.get("filter.enable", False)
        self.set_sense_average_state(filter_enable)

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
        self._write(f":SENS:CURR:PROT:LEV {level:.3E}")

    def compliance_tripped(self) -> bool:
        return self._query(":SENS:CURR:PROT:TRIP?") == "1"

    def read_current(self) -> float:
        if self._format_element != "CURR":
            self._write(":FORM:ELEM CURR")
            self._format_element = "CURR"
        return float(self._query(":READ?").split(",")[0])

    def read_voltage(self) -> float:
        if self._format_element != "VOLT":
            self._write(":FORM:ELEM VOLT")
            self._format_element = "VOLT"
        return float(self._query(":READ?").split(",")[0])

    def set_system_beeper_state(self, state: bool) -> None:
        self._write(f":SYST:BEEP:STAT {state:d}")

    def set_route_terminals(self, terminal: str) -> None:
        self._write(f":ROUT:TERM {terminal}")

    def set_source_function(self, function: str) -> None:
        self._write(f":SOUR:FUNC {function}")

    def set_sense_average_tcontrol(self, tcontrol: str) -> None:
        self._write(f":SENS:AVER:TCON {tcontrol}")

    def set_sense_average_count(self, count: int) -> None:
        self._write(f":SENS:AVER:COUN {count:d}")

    def set_sense_average_state(self, state: bool) -> None:
        self._write(f":SENS:AVER:STAT {state:d}")

    def set_sense_current_nplc(self, nplc: float) -> None:
        self._write(f":SENS:CURR:NPLC {nplc:E}")

    @handle_exception
    def _write(self, message):
        self.resource.write(message)
        self.resource.query("*OPC?")

    @handle_exception
    def _query(self, message):
        return self.resource.query(message).strip()
