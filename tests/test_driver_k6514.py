from diode_measurement.driver.k6514 import K6514

from . import FakeResource


class TestDriverK6514:

    def test_driver_k6514(self):
        res = FakeResource()
        d = K6514(res)

        res.buffer = ["Keithley Model 6514\r"]
        assert d.identity() == "Keithley Model 6514"
        assert res.buffer == ["*IDN?"]

        res.buffer = ["1"]
        assert d.reset() is None
        assert res.buffer == ["*RST", "*OPC?"]

        res.buffer = ["1"]
        assert d.clear() is None
        assert res.buffer == ["*CLS", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_zero_check_enabled(False) is None
        assert res.buffer == [":SYST:ZCH 0", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_zero_check_enabled(True) is None
        assert res.buffer == [":SYST:ZCH 1", "*OPC?"]
