from diode_measurement.driver.k6847 import K6847

from . import res


def test_driver_k6847(res):
    d = K6847(res)

    res.buffer = ["Keithley Instruments Inc., Model 6847, 12345678, 1.0.0\r"]
    assert d.identity() == "Keithley Instruments Inc., Model 6847, 12345678, 1.0.0"
    assert res.buffer == ["*IDN?"]

    res.buffer = ["1"]
    assert d.reset() is None
    assert res.buffer == ["*RST", "*OPC?"]

    res.buffer = ["1"]
    assert d.clear() is None
    assert res.buffer == ["*CLS", "*OPC?"]

    res.buffer = ["0,\"no error\""]
    assert d.next_error() == (0, "no error")
    assert res.buffer == [":SYST:ERR?"]

    res.buffer = ["1"]
    assert d.get_output_enabled() is True
    assert res.buffer == [":SOUR:VOLT:STAT?"]

    res.buffer = ["1"]
    assert d.set_output_enabled(True) is None
    assert res.buffer == [":SOUR:VOLT:STAT ON", "*OPC?"]

    res.buffer = ["4.200000E+01"]
    assert d.get_voltage_level() == 42.0
    assert res.buffer == [":SOUR:VOLT:LEV?"]

    res.buffer = ["1"]
    assert d.set_voltage_level(42.0) is None
    assert res.buffer == [":SOUR:VOLT:LEV 4.200000E+01", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_voltage_range(200.0) is None
    assert res.buffer == [":SOUR:VOLT:RANG 2.000000E+02", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_current_compliance_level(0.002) is None
    assert res.buffer == [":SOUR:VOLT:ILIM 2.000000E-03", "*OPC?"]

    res.buffer = ["1"]
    assert d.compliance_tripped() is True
    assert res.buffer == [":SOUR:VOLT:INT:FAIL?"]

    res.buffer = ["+4.210000E-03A,+7.107460E+03,+0.000000E+00"]
    assert d.measure_i() == 0.00421
    assert res.buffer == [":READ?"]

    res.buffer = ["4.200000E+01"]
    assert d.measure_v() == 42.0
    assert res.buffer == [":SOUR:VOLT:LEV?"]

    # measure_iv calls measure_i (which does :READ?) then measure_v (which does :SOUR:VOLT:LEV?)
    res.buffer = ["+4.210000E-03A,+7.107460E+03,+0.000000E+00", "4.200000E+01"]
    i, v = d.measure_iv()
    assert i == 0.00421
    assert v == 42.0
    assert res.buffer == [":READ?", ":SOUR:VOLT:LEV?"]

    res.buffer = ["1"]
    assert d.set_sense_function("CURR") is None
    assert res.buffer == [":SENS:FUNC 'CURR'", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_current_range(20e-6) is None
    assert res.buffer == [":CURR:RANG 2.000000E-05", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_current_range_auto(True) is None
    assert res.buffer == [":CURR:RANG:AUTO ON", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_zero_check_enabled(True) is None
    assert res.buffer == [":SYST:ZCH ON", "*OPC?"]

    res.buffer = ["1"]
    assert d.acquire_zero_correction() is None
    assert res.buffer == [":SYST:ZCOR:ACQ", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_zero_correction_enabled(True) is None
    assert res.buffer == [":SYST:ZCOR ON", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_format_elements(["TIME", "VSO", "READ"]) is None
    assert res.buffer == [":FORM:ELEM TIME,VSO,READ", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_sense_current_average_tcontrol("MOV") is None
    assert res.buffer == [":SENS:CURR:AVER:TCON MOV", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_sense_current_average_count(42) is None
    assert res.buffer == [":SENS:CURR:AVER:COUN 42", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_sense_current_average_enable(True) is None
    assert res.buffer == [":SENS:CURR:AVER:STAT ON", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_sense_current_nplc(4.2) is None
    assert res.buffer == [":SENS:CURR:NPLC 4.200000E+00", "*OPC?"]

    res.buffer = ["0"]
    assert d.is_interlock() is True
    assert res.buffer == [":SOUR:VOLT:INT:FAIL?"]
