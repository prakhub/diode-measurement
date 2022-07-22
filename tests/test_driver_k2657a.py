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

        res.buffer = ["1"]
        assert d.set_beeper_enable(True) is None
        assert res.buffer == ["beeper.enable = beeper.ON", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_source_function("DCVOLTS") is None
        assert res.buffer == ["smua.source.func = smua.OUTPUT_DCVOLTS", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_measure_filter_type("REPEAT_AVG") is None
        assert res.buffer == ["smua.measure.filter.type = smua.FILTER_REPEAT_AVG", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_measure_filter_count(42) is None
        assert res.buffer == ["smua.measure.filter.count = 42", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_measure_filter_enable(True) is None
        assert res.buffer == ["smua.measure.filter.enable = 1", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_measure_nplc(4.2) is None
        assert res.buffer == ["smua.measure.nplc = 4.200000E+00", "*OPC?"]
