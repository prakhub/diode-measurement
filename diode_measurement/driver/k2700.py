from typing import Any, Dict, Optional

from .driver import DMM, InstrumentError, handle_exception, parse_scpi_error

__all__ = ["K2700"]


class K2700(DMM):

    def identity(self) -> str:
        return self._query("*IDN?")

    def reset(self) -> None:
        pass  # prevent reset

    def clear(self) -> None:
        self._write("*CLS")

    def next_error(self) -> Optional[InstrumentError]:
        return parse_scpi_error(self._query(":SYST:ERR?"))

    def configure(self, options: Dict[str, Any]) -> None:
        ...

    def read_temperature(self) -> float:
        self._write(":FORM:ELEM READ")  # select reading as return value
        return float(self._query(":FETC?"))

    @handle_exception
    def _write(self, message):
        self.resource.write(message)
        self.resource.query("*OPC?")

    @handle_exception
    def _query(self, message):
        return self.resource.query(message).strip()
