from diode_measurement.driver.k2657a import K2657A

from . import FakeResource


class TestDriverK2657A:

    def test_driver_k2657a(self):
        res = FakeResource()
        d = K2657A(res)

        res.buffer = ["Keithley Model 2657A\r"]
        assert d.identity() == "Keithley Model 2657A"
        assert res.buffer == ["*IDN?"]

        res.buffer = ["1"]
        assert d.reset() is None
        assert res.buffer == ["reset()", "*OPC?"]

        res.buffer = ["1"]
        assert d.clear() is None
        assert res.buffer == ["status.reset()", "*OPC?"]

        res.buffer = ["0\tno error\t123\t0"]
        assert d.error_state() == (0, "no error")
        assert res.buffer == ["print(errorqueue.next())"]
