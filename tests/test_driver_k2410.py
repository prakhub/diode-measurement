from diode_measurement.driver.k2410 import K2410

from . import FakeResource


class TestDriverK2410:

    def test_driver_k2410(self):
        res = FakeResource()
        d = K2410(res)

        res.buffer = ["Keithley Model 2410\r"]
        assert d.identity() == "Keithley Model 2410"
        assert res.buffer == ["*IDN?"]

        res.buffer = ["1"]
        assert d.reset() is None
        assert res.buffer == ["*RST", "*OPC?"]

        res.buffer = ["1"]
        assert d.clear() is None
        assert res.buffer == ["*CLS", "*OPC?"]
