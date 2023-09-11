from diode_measurement.plugins import tcpserver


def test_is_finite():
    assert tcpserver.is_finite(0)
    assert tcpserver.is_finite(-42.)
    assert tcpserver.is_finite("foo")
    assert not tcpserver.is_finite(float("nan"))
    assert not tcpserver.is_finite(float("+inf"))
    assert not tcpserver.is_finite(float("-inf"))


def test_json_dict():
    data_in = {"a": float("nan"), "b": 42., "c": "42"}
    data_out = {"a": None, "b": 42., "c": "42"}
    assert tcpserver.json_dict(data_in) == data_out
