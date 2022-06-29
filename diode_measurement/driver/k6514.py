import time

from .driver import Electrometer, handle_exception

__all__ = ["K6514"]


class K6514(Electrometer):

    def identity(self) -> str:
        return self._query("*IDN?").strip()

    def reset(self) -> None:
        self._write("*RST")

    def clear(self) -> None:
        self._write("*CLS")

    def error_state(self) -> tuple:
        code, message = self._query(":SYST:ERR?").split(",")
        code = int(code)
        message = message.strip().strip('"')
        return code, message

    def configure(self, **options) -> None:
        pass

    def get_output_enabled(self) -> bool:
        return False

    def set_output_enabled(self, enabled: bool) -> None:
        pass

    def get_voltage_level(self) -> float:
        return 0

    def set_voltage_level(self, level: float) -> None:
        pass

    def set_voltage_range(self, level: float) -> None:
        pass

    def set_current_compliance_level(self, level: float) -> None:
        self._write(f":SENS:CURR:PROT:LEV {level:.3E}")

    def compliance_tripped(self) -> bool:
        return self._query(":SENS:CURR:PROT:TRIP?") == "1"

    def read_current(self, timeout=10.0, interval=0.250):
        # Select sense function
        self._write(":FUNC CURR")
        # Request operation complete
        self.resource.write("*CLS")
        self.resource.write("*OPC")
        # Initiate measurement
        self._write(":INIT")
        threshold = time.time() + timeout
        interval = min(timeout, interval)
        while time.time() < threshold:
            # Read event status
            if int(self._query("*ESR?")) & 0x1:
                try:
                    result = self._query(":FETCH?")
                    return float(result.split(",")[0])
                except Exception as exc:
                    raise RuntimeError(f"Failed to fetch ELM reading: {exc}") from exc
            time.sleep(interval)
        raise RuntimeError(f"Electrometer reading timeout, exceeded {timeout:G} s")

    @handle_exception
    def _write(self, message):
        self.resource.write(message)
        self.resource.query("*OPC?")

    @handle_exception
    def _query(self, message):
        return self.resource.query(message).strip()
