from diode_measurement.driver.k2470 import K2470

from . import FakeResource


class TestDriverK2470:

    def test_driver_k2470(self):
        res = FakeResource()
        d = K2470(res)

        res.buffer = ["Keithley Model 2470\r"]
        assert d.identity() == "Keithley Model 2470"
        assert res.buffer == ["*IDN?"]

        res.buffer = ["1"]
        assert d.reset() is None
        assert res.buffer == ["*RST", "*OPC?"]

        res.buffer = ["1"]
        assert d.clear() is None
        assert res.buffer == ["*CLS", "*OPC?"]

        res.buffer = ["0,\"no error;;\""]
        assert d.error_state() == (0, "no error;;")
        assert res.buffer == [":SYST:ERR?"]

        res.buffer = ["1"]
        assert d.set_route_terminals("REAR") is None
        assert res.buffer == [":ROUT:TERM REAR", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_source_function("VOLT") is None
        assert res.buffer == [":SOUR:FUNC VOLT", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_sense_current_average_tcontrol("MOV") is None
        assert res.buffer == [":SENS:CURR:AVER:TCON MOV", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_sense_current_average_count(42) is None
        assert res.buffer == [":SENS:CURR:AVER:COUN 42", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_sense_current_average_enable(True) is None
        assert res.buffer == [":SENS:CURR:AVER:STAT 1", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_sense_current_nplc(4.2) is None
        assert res.buffer == [":SENS:CURR:NPLC 4.200000E+00", "*OPC?"]
