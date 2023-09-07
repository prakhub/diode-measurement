from diode_measurement.driver.brandbox import BrandBox

from . import FakeResource


class TestDriverBrandBox:

    def test_driver_brandbox(self):
        res = FakeResource()
        d = BrandBox(res)

        res.buffer = ["BrandBox V1.1\r"]
        assert d.identity() == "BrandBox V1.1"
        assert res.buffer == ["*IDN?"]

        res.buffer = []
        assert d.reset() is None
        assert res.buffer == []

        res.buffer = []
        assert d.clear() is None
        assert res.buffer == []
