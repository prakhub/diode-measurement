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
