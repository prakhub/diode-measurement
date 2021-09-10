import time

from .driver import Electrometer, handle_exception

class E4980A(Electrometer):

    @handle_exception
    def _write(self, message):
        self.resource.write(message)
        self.resource.query('*OPC?')

    @handle_exception
    def _query(self, message):
        return self.resource.query(message).strip()

    def identity(self) -> str:
        return self._query('*IDN?').strip()

    def reset(self) -> None:
        self._write('*RST')

    def clear(self) -> None:
        self._write('*CLS')

    def error_state(self) -> tuple:
        code, message = self._query(':SYST:ERR?').split(',')
        code = int(code)
        message = message.strip().strip('"')
        return code, message

    def configure(self, **options) -> None:
        self._write(':SYST:BEEP:STAT 0')
        self._write(':BIAS:RANG:AUTO 1')

    def get_output_enabled(self) -> bool:
        return self._query(':BIAS:STAT?') == '1'

    def set_output_enabled(self, enabled: bool) -> None:
        value = {False: '0', True: '1'}[enabled]
        self._write(f':BIAS:STAT {value}')

    def get_voltage_level(self) -> float:
        return float(self._query(':BIAS:VOLT:LEV?'))

    def set_voltage_level(self, level: float) -> None:
        self._write(f':BIAS:VOLT:LEV {level:.3E}')

    def set_voltage_range(self, level: float) -> None:
        pass # TODO

    def set_current_compliance_level(self, level: float) -> None:
        self._write(f':SENS:CURR:PROT:LEV {level:.3E}')

    def compliance_tripped(self) -> bool:
        return self._query(':SENS:CURR:PROT:TRIP?') == '1'

    def read_current(self):
        return 0

    def read_capacity(self) -> float:
        self._write(':FUN:IMP:TYPE CPRP')
        return self._fetch()

    def _fetch(self, timeout=10.0, interval=0.250):
        # Select sense function
        # Request operation complete
        self.resource.write('*CLS')
        self.resource.write('*OPC')
        # Initiate measurement
        self._write(":INIT")
        threshold = time.time() + timeout
        interval = min(timeout, interval)
        while time.time() < threshold:
            # Read event status
            if int(self._query('*ESR?')) & 0x1:
                try:
                    result = self._query(":FETCH?")
                    return float(result.split(',')[0])
                except Exception as exc:
                    raise RuntimeError(f"Failed to fetch ELM reading: {exc}") from exc
            time.sleep(interval)
        raise RuntimeError(f"Electrometer reading timeout, exceeded {timeout:G} s")
