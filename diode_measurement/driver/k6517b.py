import time

from .driver import Electrometer, handle_exception

__all__ = ["K6517B"]


class K6517B(Electrometer):

    def identity(self) -> str:
        return self._query("*IDN?").strip()

    def reset(self) -> None:
        self._write("*RST")
        self._query("*OPC?")

    def clear(self) -> None:
        self._write("*CLS")
        self._query("*OPC?")

    def error_state(self) -> tuple:
        code, message = self._query(":SYST:ERR?").split(",")
        code = int(code)
        message = message.strip().strip('"')
        return code, message

    def configure(self, **options) -> None:
        # Select sense function
        self._write(":SENS:FUNC 'CURR'")

        # Select reading format
        self._write(":FORM:ELEM READ")

        filter_mode = options.get("filter.mode", "MOV")
        self._write(f":SENS:CURR:AVER:TCON {filter_mode}")

        filter_count = options.get("filter.count", 1)
        self._write(f":SENS:CURR:AVER:COUN {filter_count:d}")

        filter_enable = options.get("filter.enable", False)
        self._write(f":SENS:CURR:AVER:STAT {filter_enable:d}")

        nplc = options.get("nplc", 1.0)
        self._write(f":SENS:CURR:NPLC {nplc:E}")

        self._query("*OPC?")

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
        self._write("*OPC")
        # Initiate measurement
        self._write(":INIT")
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

    def set_zero_check_enabled(self, enabled: bool) -> None:
        self._write(f":SYST:ZCH {enabled:d}")
        self._query("*OPC?")

    @handle_exception
    def _write(self, message):
        self.resource.write(message)

    @handle_exception
    def _query(self, message):
        return self.resource.query(message).strip()
