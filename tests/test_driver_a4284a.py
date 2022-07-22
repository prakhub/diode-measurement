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

        res.buffer = ["1"]
        assert d.set_function_impedance_type("CPRP") is None
        assert res.buffer == [":FUNC:IMP:TYPE CPRP", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_aperture("MED", 42) is None
        assert res.buffer == [":APER MED,42", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_correction_length(2) is None
        assert res.buffer == [":CORR:LENG 2", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_correction_open_state(True) is None
        assert res.buffer == [":CORR:OPEN:STAT 1", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_correction_short_state(True) is None
        assert res.buffer == [":CORR:SHOR:STAT 1", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_amplitude_voltage(4.2) is None
        assert res.buffer == [":VOLT 4.200000E+00", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_amplitude_frequency(1.2e3) is None
        assert res.buffer == [":FREQ 1.200000E+03", "*OPC?"]

        res.buffer = ["1"]
        assert d.set_amplitude_alc(True) is None
        assert res.buffer == [":AMPL:ALC 1", "*OPC?"]
