from .driver import SourceMeter, handle_exception

__all__ = ['K2470']


class K2470(SourceMeter):

    def identity(self) -> str:
        return self._query('*IDN?')

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
        route_terminals = options.get('route.terminals', 'FRON')
        self._write(f':ROUT:TERM {route_terminals}')

        self._write(f':SOUR:FUNC VOLT')

        filter_mode = options.get('filter.mode', 'MOV')
        self._write(f':SENS:CURR:AVER:TCON {filter_mode}')

        filter_count = options.get('filter.count', 1)
        self._write(f':SENS:CURR:AVER:COUN {filter_count:d}')

        filter_enable = options.get('filter.enable', False)
        self._write(f':SENS:CURR:AVER:STAT {filter_enable:d}')

        nplc = options.get('nplc', 1.0)
        self._write(f':SENS:CURR:NPLC {nplc:E}')

    def get_output_enabled(self) -> bool:
        return self._query(':OUTP:STAT?') == '1'

    def set_output_enabled(self, enabled: bool) -> None:
        value = {False: '0', True: '1'}[enabled]
        self._write(f':OUTP:STAT {value}')

    def get_voltage_level(self) -> float:
        return float(self._query(':SOUR:VOLT:LEV?'))

    def set_voltage_level(self, level: float) -> None:
        self._write(f':SOUR:VOLT:LEV {level:.3E}')

    def set_voltage_range(self, level: float) -> None:
        self._write(f':SOUR:VOLT:RANG {level:.3E}')

    def set_current_compliance_level(self, level: float) -> None:
        self._write(f':SOUR:VOLT:ILIM:LEV {level:.3E}')

    def compliance_tripped(self) -> bool:
        return self._query(':SOUR:VOLT:ILIM:LEV:TRIP?') == '1'

    def read_current(self) -> float:
        return float(self._query(':MEAS:CURR?'))

    @handle_exception
    def _write(self, message):
        self.resource.write(message)
        self.resource.query('*OPC?')

    @handle_exception
    def _query(self, message):
        return self.resource.query(message).strip()
