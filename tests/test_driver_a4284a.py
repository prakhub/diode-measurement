from diode_measurement.driver.a4284a import A4284A

from . import FakeResource


class TestDriverA4284A:

    def test_driver_a4284a(self):
        res = FakeResource()
        d = A4284A(res)

        res.buffer = ["Agilent Model A4284A\r"]
        assert d.identity() == "Agilent Model A4284A"
        assert res.buffer == ["*IDN?"]

        res.buffer = ["1"]
        assert d.reset() is None
        assert res.buffer == ["*RST", "*OPC?"]

        res.buffer = ["1"]
        assert d.clear() is None
        assert res.buffer == ["*CLS", "*OPC?"]
