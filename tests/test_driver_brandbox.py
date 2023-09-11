from diode_measurement.driver.brandbox import BrandBox

from . import res


def test_driver_brandbox(res):
    d = BrandBox(res)

    assert d.CHANNELS == ["A1", "A2", "B1", "B2", "C1", "C2"]

    res.buffer = ["BrandBox V1.1\r"]
    assert d.identity() == "BrandBox V1.1"
    assert res.buffer == ["*IDN?"]

    res.buffer = []
    assert d.reset() is None
    assert res.buffer == []

    res.buffer = ["OK"]
    assert d.clear() is None
    assert res.buffer == ["*CLS"]

    res.buffer = []
    assert d.next_error() == (0, "No Error")
    assert res.buffer == []

    res.buffer = ["OK"]
    assert d.close_channels(["A1", "C2"]) is None
    assert res.buffer == [":CLOS A1,C2"]

    res.buffer = ["OK"]
    assert d.open_channels(["B2", "C2"]) is None
    assert res.buffer == [":OPEN B2,C2"]

    res.buffer = ["OK"]
    assert d.open_all_channels() is None
    assert res.buffer == [":OPEN A1,A2,B1,B2,C1,C2"]

    res.buffer = ["B1,C1,C2"]
    assert d.closed_channels() == ["B1", "C1", "C2"]
    assert res.buffer == [":CLOS:STAT?"]
