from diode_measurement.driver.k6517b import K6517B

from . import FakeResource


class TestDriverK6517b:

    def test_driver_k6517b(self):
        res = FakeResource()
        d = K6517B(res)

        res.buffer = ["Keithley Model 6517B\r"]
        assert d.identity() == "Keithley Model 6517B"
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
