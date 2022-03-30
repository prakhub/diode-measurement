from .driver import SourceMeter, handle_exception

__all__ = ['K2657A']


class K2657A(SourceMeter):

    def identity(self) -> str:
        return self._query('*IDN?')

    def reset(self) -> None:
        self._write('reset()')

    def clear(self) -> None:
        self._write('status.reset()')

    def error_state(self) -> tuple:
        code, message, *_ = self._print('errorqueue.next()').split('\t')
        code = int(float(code))
        message = message.strip().strip('"')
        return code, message

    def configure(self, **options) -> None:
        self._write('beeper.enable = 0')
        self._write('smua.source.func = smua.OUTPUT_DCVOLTS')

        filter_mode = options.get('filter.mode', 'REPEAT_AVG')
        self._write(f'smua.measure.filter.type = smua.FILTER_{filter_mode}')

        filter_count = options.get('filter.count', 1)
        self._write(f'smua.measure.filter.count = {filter_count:d}')

        filter_enable = options.get('filter.enable', False)
        self._write(f'smua.measure.filter.enable = {filter_enable:d}')

        nplc = options.get('nplc', 1.0)
        self._write(f'smua.measure.nplc = {nplc:E}')

    def get_output_enabled(self) -> bool:
        return self._print('smua.source.output') == '1'

    def set_output_enabled(self, enabled: bool) -> None:
        value = {False: 'OFF', True: 'ON'}[enabled]
        self._write(f'smua.source.output = smua.OUTPUT_{value}')

    def get_voltage_level(self) -> float:
        return float(self._print('smua.source.levelv'))

    def set_voltage_level(self, level: float) -> None:
        self._write(f'smua.source.levelv = {level:.3E}')

    def set_voltage_range(self, level: float) -> None:
        self._write(f'smua.source.rangev = {level:.3E}')

    def set_current_compliance_level(self, level: float) -> None:
        self._write(f'smua.source.limiti = {level:.3E}')

    def compliance_tripped(self) -> bool:
        return self._print('smua.source.compliance').lower() == 'true'

    def read_current(self) -> float:
        return float(self._print('smua.measure.i()'))

    @handle_exception
    def _write(self, message):
        self.resource.write(message)
        self.resource.query('*OPC?')

    @handle_exception
    def _query(self, message):
        return self.resource.query(message).strip()

    def _print(self, message):
        return self._query(f'print({message})')
