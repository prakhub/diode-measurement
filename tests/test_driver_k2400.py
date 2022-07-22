from diode_measurement.driver.k2400 import K2400

from . import FakeResource


class TestDriverK2400:

    def test_driver_k2400(self):
        res = FakeResource()
        d = K2400(res)

        res.buffer = ["Keithley Model 2400\r"]
        assert d.identity() == "Keithley Model 2400"
        assert res.buffer == ["*IDN?"]

        res.buffer = ["1"]
        assert d.reset() is None
        assert res.buffer == ["*RST", "*OPC?"]

        res.buffer = ["1"]
        assert d.clear() is None
        assert res.buffer == ["*CLS", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_system_beeper_state(True) is None
        assert res.buffer == [":SYST:BEEP:STAT 1", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_route_terminals("REAR") is None
        assert res.buffer == [":ROUT:TERM REAR", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_source_function("VOLT") is None
        assert res.buffer == [":SOUR:FUNC VOLT", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_sense_average_tcontrol("REP") is None
        assert res.buffer == [":SENS:AVER:TCON REP", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_sense_average_count(42) is None
        assert res.buffer == [":SENS:AVER:COUN 42", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_sense_average_state(True) is None
        assert res.buffer == [":SENS:AVER:STAT 1", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_sense_current_nplc(4.2) is None
        assert res.buffer == [":SENS:CURR:NPLC 4.200000E+00", "*OPC?"]
