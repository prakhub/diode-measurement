import time

from .driver import LCRMeter, handle_exception

__all__ = ["A4284A"]


class A4284A(LCRMeter):

    @handle_exception
    def _write(self, message):
        self.resource.write(message)
        self.resource.query("*OPC?")

    @handle_exception
    def _query(self, message):
        return self.resource.query(message).strip()

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
        self._write(":INIT:CONT OFF")

        function_type = options.get("function.type", "CPRP")
        self._write(f":FUNC:IMP:TYPE {function_type}")

        # Apterture
        integration_time = options.get("aperture.integration_time", "MED")
        assert integration_time in ["SHOR", "MED", "LONG"]
        averaging_rate = options.get("aperture.averaging_rate", 1)
        assert 1 <= averaging_rate <= 128
        self._write(f":APER {integration_time},{averaging_rate:d}")

        # Correction cable length
        correction_length = options.get("correction.length", 0)
        assert correction_length in [0, 1, 2]
        self._write(f":CORR:LENG {correction_length:d}")

        # Enable open correction
        correction_open_enabled = options.get("correction.open.enabled", False)
        self._write(f":CORR:OPEN:STAT {correction_open_enabled:d}")

        # Enable short correction
        correction_short_enabled = options.get("correction.short.enabled", False)
        self._write(f":CORR:SHOR:STAT {correction_short_enabled:d}")

        voltage = options.get("voltage", 1.0)
        self._write(f":VOLT {voltage:E}")

        frequency = options.get("frequency", 1000.)
        self._write(f":FREQ {frequency:E}")

        amplitude_alc = options.get("amplitude.alc", False)
        self._write(f":AMPL:ALC {frequency:E}")


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
        # Select sense function
        # Request operation complete
        self.resource.write("*CLS")
        self.resource.write("*OPC")
        # Initiate measurement
        self.resource.(":INIT:IMM")
        threshold = time.time() + timeout
        interval = min(timeout, interval)
        while time.time() < threshold:
            # Read event status
            if int(self._query("*ESR?")) & 0x1:
                try:
                    result = self._query(":FETCH?")
                    return float(result.split(",")[0])
                except Exception as exc:
                    raise RuntimeError(f"Failed to fetch LCR reading: {exc}") from exc
            time.sleep(interval)
        raise RuntimeError(f"LCR reading timeout, exceeded {timeout:G} s")
