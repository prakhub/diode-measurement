from diode_measurement.driver.k237 import K237

from . import FakeResource


class TestDriverK237:

    def test_driver_k237(self):
        res = FakeResource()
        d = K237(res)

        res.buffer = ["K237A1\r"]
        assert d.identity() == "K237A1"
        assert res.buffer == ["U0X"]

        res.buffer = []
        assert d.reset() is None
        assert res.buffer == []

        res.buffer = []
        assert d.clear() is None
        assert res.buffer == []

        res.buffer = ["23700000000000000000000000000"]
        assert d.next_error() is None
        assert res.buffer == ["U1X"]

        res.buffer = ["23701000000000000000000000000"]
        assert d.next_error() == (1, "IDDC")
        assert res.buffer == ["U1X"]

        res.buffer = ["23700000000001000000000000000"]
        assert d.next_error() == (10, "In Standby")
        assert res.buffer == ["U1X"]
