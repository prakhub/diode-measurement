from diode_measurement.driver.k595 import K595

from . import FakeResource


class TestDriverK595:

    def test_driver_k595(self):
        res = FakeResource()
        d = K595(res)

        res.buffer = ["595\r"]
        assert d.identity() == "595"
        assert res.buffer == ["U0X"]

        res.buffer = []
        assert d.reset() is None
        assert res.buffer == []

        res.buffer = []
        assert d.clear() is None
        assert res.buffer == []

        res.buffer = ["59500000000000000000000000000"]
        assert d.error_state() == (0, "No Error")
        assert res.buffer == ["U1X"]

        res.buffer = ["59510000000000000000000000000"]
        assert d.error_state() == (100, "IDDC")
        assert res.buffer == ["U1X"]

        res.buffer = ["59501000000000000000000000000"]
        assert d.error_state() == (101, "IDDCO")
        assert res.buffer == ["U1X"]
