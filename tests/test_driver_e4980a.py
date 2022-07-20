from diode_measurement.driver.e4980a import E4980A

from . import FakeResource


class TestDriverE4980A:

    def test_driver_e4980a(self):
        res = FakeResource()
        d = E4980A(res)

        res.buffer = ["Agilent Model 4980A\r"]
        assert d.identity() == "Agilent Model 4980A"
        assert res.buffer == ["*IDN?"]

        res.buffer = ["1"]
        assert d.reset() is None
        assert res.buffer == ["*RST", "*OPC?"]

        res.buffer = ["1"]
        assert d.clear() is None
        assert res.buffer == ["*CLS", "*OPC?"]
