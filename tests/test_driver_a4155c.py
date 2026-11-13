import pytest

from diode_measurement.drivers.a4155c import A4155C, parse_value

from . import res


def defined_driver(res, invert_sign: bool = False) -> A4155C:
    """Return a driver whose channel definition was already sent.

    The driver defines the channel lazily on first use, which would otherwise
    prepend the definition commands to every recorded sequence. Sign inversion
    is off unless requested, so that readings compare against raw instrument
    data; the default is covered by the dedicated sign tests.
    """
    d = A4155C(res)
    d.set_invert_sign_enabled(invert_sign)
    res.buffer = ["1"] * 8
    d.define_channel()
    res.buffer = []
    return d


def sent_commands(res) -> list:
    """Return the instrument commands recorded by the fake resource, without
    the interleaved `*OPC?` queries and unconsumed responses.
    """
    return [message for message in res.buffer if message.startswith(":")]


def test_parse_value():
    assert parse_value("N+1.23456E-09") == ("N", pytest.approx(1.23456e-9))
    assert parse_value(" C-4.20000E-06 ") == ("C", pytest.approx(-4.2e-6))
    assert parse_value("+1.00000E+00") == ("", pytest.approx(1.0))


def test_parse_value_invalid():
    with pytest.raises(RuntimeError):
        parse_value("")
    with pytest.raises(RuntimeError):
        parse_value("N+invalid")


def test_driver_a4155c(res):
    d = A4155C(res)

    res.buffer = ["Agilent Technologies,4155C,0,01.00\r"]
    assert d.identify() == "Agilent Technologies,4155C,0,01.00"
    assert res.buffer == ["*IDN?"]

    res.buffer = ["1"]
    assert d.reset() is None
    assert res.buffer == ["*RST", "*OPC?"]

    res.buffer = ["1"]
    assert d.clear() is None
    assert res.buffer == ["*CLS", "*OPC?"]

    res.buffer = ['0,"No error"']
    assert d.next_error() is None
    assert res.buffer == [":SYST:ERR?"]

    res.buffer = ['-113,"Undefined header, command"']
    error = d.next_error()
    assert error.code == -113
    assert error.message == "Undefined header, command"
    assert res.buffer == [":SYST:ERR?"]


def test_driver_a4155c_channel(res):
    d = A4155C(res)

    assert d.channel == "SMU1"
    assert d.channel_index == 1
    assert d.current_name == "I1"
    assert d.voltage_name == "V1"

    d.set_channel("smu3")
    assert d.channel == "SMU3"
    assert d.channel_index == 3
    assert d.current_name == "I3"
    assert d.voltage_name == "V3"

    with pytest.raises(ValueError):
        d.set_channel("SMU5")


def test_driver_a4155c_commands(res):
    d = defined_driver(res)

    res.buffer = ["1"]
    assert d.disable_all_channels() is None
    assert res.buffer == [":PAGE:CHAN:ALL:DIS", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_channel_mode("V") is None
    assert res.buffer == [":PAGE:CHAN:SMU1:MODE V", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_channel_function("CONS") is None
    assert res.buffer == [":PAGE:CHAN:SMU1:FUNC CONS", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_channel_voltage_name("V1") is None
    assert res.buffer == [":PAGE:CHAN:SMU1:VNAME 'V1'", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_channel_current_name("I1") is None
    assert res.buffer == [":PAGE:CHAN:SMU1:INAME 'I1'", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_channel_standby(True) is None
    assert res.buffer == [":PAGE:CHAN:SMU1:STAN ON", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_channel_standby(False) is None
    assert res.buffer == [":PAGE:CHAN:SMU1:STAN OFF", "*OPC?"]

    res.buffer = ["1"]
    assert d.get_channel_standby() is True
    assert res.buffer == [":PAGE:CHAN:SMU1:STAN?"]

    res.buffer = ["0"]
    assert d.get_output_enabled() is False
    assert res.buffer == [":PAGE:CHAN:SMU1:STAN?"]

    res.buffer = ["1"]
    assert d.set_measurement_mode("SAMP") is None
    assert res.buffer == [":PAGE:CHAN:MODE SAMP", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_range_mode("AUTO") is None
    assert res.buffer == [":PAGE:MEAS:MSET:SMU1:RANG:MODE AUTO", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_range(1e-9) is None
    assert res.buffer == [":PAGE:MEAS:MSET:SMU1:RANG 1.00000E-09", "*OPC?"]

    res.buffer = ["+1.000000E-009"]
    assert d.get_range() == pytest.approx(1e-9)
    assert res.buffer == [":PAGE:MEAS:MSET:SMU1:RANG?"]

    res.buffer = ["1"]
    assert d.set_integration_time("med") is None
    assert res.buffer == [":PAGE:MEAS:MSET:ITIM MED", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_integration_time_long(16) is None
    assert res.buffer == [":PAGE:MEAS:MSET:ITIM:LONG 16", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_sampling_points(8) is None
    assert res.buffer == [":PAGE:MEAS:SAMP:POIN 8", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_sampling_interval(2e-3) is None
    assert res.buffer == [":PAGE:MEAS:SAMP:IINT 2.00000E-03", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_sampling_hold_time(0.5) is None
    assert res.buffer == [":PAGE:MEAS:SAMP:HTIM 5.00000E-01", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_format_data("ASC") is None
    assert res.buffer == [":FORM:DATA ASC", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_voltage_level(0.0) is None
    assert res.buffer == [":PAGE:MEAS:SAMP:CONS:SMU1 0.00000E+00", "*OPC?"]
    assert d.get_voltage_level() == 0.0

    res.buffer = ["1"]
    assert d.set_current_compliance_level(1e-3) is None
    assert res.buffer == [":PAGE:MEAS:SAMP:CONS:SMU1:COMP 1.00000E-03", "*OPC?"]

    # Ranging is left to the analyzer
    res.buffer = []
    assert d.set_voltage_range(100.0) is None
    assert res.buffer == []


def test_driver_a4155c_invalid_values(res):
    d = A4155C(res)

    with pytest.raises(ValueError):
        d.set_range_mode("FAST")
    with pytest.raises(ValueError):
        d.set_integration_time("HUGE")
    with pytest.raises(ValueError):
        d.set_integration_time_long(0)
    with pytest.raises(ValueError):
        d.set_integration_time_long(101)
    with pytest.raises(ValueError):
        d.set_sampling_points(0)
    with pytest.raises(ValueError):
        d.set_sampling_points(1202)
    with pytest.raises(ValueError):
        d.set_sampling_interval(1e-3)
    with pytest.raises(ValueError):
        d.set_sampling_interval(100.0)
    with pytest.raises(ValueError):
        d.set_sampling_hold_time(-1.0)


def test_driver_a4155c_configure(res):
    d = A4155C(res)

    res.buffer = ["1"] * 32
    assert (
        d.configure(
            {
                "smu.channel": "SMU2",
                "channel.disable_others": True,
                "channel.standby": True,
                "sense.range_mode": "LIM",
                "sense.range": 1e-9,
                "integration.time": "LONG",
                "integration.nplc": 4,
                "sampling.points": 4,
                "sampling.interval": 20e-3,
                "sampling.hold_time": 0.0,
                "source.voltage": 0.0,
                "source.current_compliance": 100e-6,
            }
        )
        is None
    )
    assert d.channel == "SMU2"
    assert sent_commands(res) == [
        ":PAGE:CHAN:ALL:DIS",
        ":PAGE:CHAN:MODE SAMP",
        ":PAGE:CHAN:SMU2:VNAME 'V2'",
        ":PAGE:CHAN:SMU2:INAME 'I2'",
        ":PAGE:CHAN:SMU2:MODE V",
        ":PAGE:CHAN:SMU2:FUNC CONS",
        ":PAGE:CHAN:SMU2:STAN OFF",
        ":PAGE:MEAS:MSET:SMU2:RANG:MODE LIM",
        ":PAGE:MEAS:MSET:SMU2:RANG 1.00000E-09",
        ":PAGE:MEAS:MSET:ITIM LONG",
        ":PAGE:MEAS:MSET:ITIM:LONG 4",
        ":PAGE:MEAS:SAMP:POIN 4",
        ":PAGE:MEAS:SAMP:IINT 2.00000E-02",
        ":PAGE:MEAS:SAMP:HTIM 0.00000E+00",
        ":PAGE:MEAS:SAMP:CONS:SMU2 0.00000E+00",
        ":PAGE:MEAS:SAMP:CONS:SMU2:COMP 1.00000E-04",
        ":FORM:DATA ASC",
    ]


def test_driver_a4155c_configure_defaults(res):
    d = A4155C(res)

    res.buffer = ["1"] * 32
    assert d.configure({}) is None
    assert d.channel == "SMU1"
    messages = sent_commands(res)
    assert ":PAGE:CHAN:ALL:DIS" in messages
    assert ":PAGE:MEAS:MSET:ITIM MED" in messages
    assert ":PAGE:MEAS:MSET:SMU1:RANG:MODE AUTO" in messages
    # An explicit range is only applied for limited and fixed ranging
    assert ":PAGE:MEAS:MSET:SMU1:RANG 1.00000E-09" not in messages
    # NPLC is only applied for long integration time
    assert ":PAGE:MEAS:MSET:ITIM:LONG 1" not in messages
    assert ":PAGE:MEAS:SAMP:POIN 1" in messages
    # Source level and compliance are left to the measurement (SMU role)
    assert not any(":PAGE:MEAS:SAMP:CONS:" in message for message in messages)


def test_driver_a4155c_voltage_limit(res):
    d = A4155C(res)

    res.buffer = ["1"] * 32
    assert d.set_voltage_level(-100.0) is None
    assert d.get_voltage_level() == -100.0
    with pytest.raises(ValueError):
        d.set_voltage_level(-100.5)
    with pytest.raises(ValueError):
        d.set_voltage_level(150.0)
    assert d.get_voltage_level() == -100.0


def test_driver_a4155c_configure_keep_channels(res):
    d = A4155C(res)

    res.buffer = ["1"] * 32
    assert d.configure({"channel.disable_others": False}) is None
    assert ":PAGE:CHAN:ALL:DIS" not in sent_commands(res)


def test_driver_a4155c_defines_channel_before_first_use(res):
    """The application sets a source level before configure() is called."""
    d = A4155C(res)

    res.buffer = ["1"] * 32
    d.set_voltage_level(0.0)
    messages = sent_commands(res)
    assert messages == [
        ":PAGE:CHAN:MODE SAMP",
        ":PAGE:CHAN:SMU1:VNAME 'V1'",
        ":PAGE:CHAN:SMU1:INAME 'I1'",
        ":PAGE:CHAN:SMU1:MODE V",
        ":PAGE:CHAN:SMU1:FUNC CONS",
        ":PAGE:MEAS:SAMP:CONS:SMU1 0.00000E+00",
    ]

    # already defined, no repeated definition
    res.buffer = ["1"] * 32
    d.set_voltage_level(1.0)
    assert sent_commands(res) == [":PAGE:MEAS:SAMP:CONS:SMU1 1.00000E+00"]


def test_driver_a4155c_reset_invalidates_channel_definition(res):
    d = A4155C(res)

    res.buffer = ["1"] * 32
    d.configure({})

    res.buffer = ["1"] * 32
    d.reset()
    d.set_voltage_level(0.0)
    assert ":PAGE:CHAN:SMU1:FUNC CONS" in sent_commands(res)


def test_driver_a4155c_measure_defines_channel(res):
    d = A4155C(res)

    res.buffer = ["1"] * 5 + ["1", "+1.00000E-12"]
    assert d.measure_i() == pytest.approx(-1e-12)  # inverted by default
    assert ":PAGE:CHAN:MODE SAMP" in sent_commands(res)


def test_driver_a4155c_zero_check(res):
    d = defined_driver(res)

    res.buffer = ["1"]
    assert d.set_zero_check_enabled(False) is None
    assert res.buffer == [":PAGE:CHAN:SMU1:STAN ON", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_zero_check_enabled(True) is None
    assert res.buffer == [":PAGE:CHAN:SMU1:STAN OFF", "*OPC?"]

    res.buffer = ["1"]
    assert d.set_output_enabled(True) is None
    assert res.buffer == [":PAGE:CHAN:SMU1:STAN ON", "*OPC?"]


def test_driver_a4155c_measurement_mode_precedes_sampling_page(res):
    """The sampling setup page is only effective in sampling mode."""
    d = A4155C(res)

    res.buffer = ["1"] * 32
    d.configure({})
    messages = sent_commands(res)
    mode_index = messages.index(":PAGE:CHAN:MODE SAMP")
    sampling = [i for i, m in enumerate(messages) if m.startswith(":PAGE:MEAS:SAMP")]
    assert sampling
    assert mode_index < min(sampling)


def test_driver_a4155c_range_follows_channel_definition(res):
    """Ranging is rejected by the analyzer for an undefined channel."""
    d = A4155C(res)

    res.buffer = ["1"] * 32
    d.configure({"sense.range_mode": "FIX", "sense.range": 1e-6})
    messages = sent_commands(res)
    assert messages.index(":PAGE:CHAN:SMU1:FUNC CONS") < messages.index(
        ":PAGE:MEAS:MSET:SMU1:RANG:MODE FIX"
    )
    assert ":PAGE:MEAS:MSET:SMU1:RANG 1.00000E-06" in messages


def test_driver_a4155c_zero_check_without_standby(res):
    d = A4155C(res)

    res.buffer = ["1"] * 32
    d.configure({"channel.standby": False})
    assert ":PAGE:CHAN:SMU1:STAN OFF" not in sent_commands(res)

    res.buffer = []
    assert d.set_zero_check_enabled(False) is None
    assert d.set_output_enabled(True) is None
    assert res.buffer == []


def test_driver_a4155c_invert_sign_is_default(res):
    """An SMU counts sourced current positive, an electrometer counts it
    negative, so readings are inverted unless asked otherwise.
    """
    assert A4155C(res).is_invert_sign_enabled() is True

    d = defined_driver(res, invert_sign=True)

    res.buffer = ["1", "+6.35000E-12"]
    assert d.measure_i() == pytest.approx(-6.35e-12)

    res.buffer = ["1", "-4.23000E-10"]
    assert d.measure_i() == pytest.approx(4.23e-10)


def test_driver_a4155c_invert_sign_disabled(res):
    d = defined_driver(res)
    assert d.is_invert_sign_enabled() is False

    res.buffer = ["1", "+6.35000E-12"]
    assert d.measure_i() == pytest.approx(6.35e-12)


def test_driver_a4155c_invert_sign_keeps_zero_positive(res):
    """A negative zero would be written to the data file as -0.000E+00."""
    d = defined_driver(res, invert_sign=True)

    res.buffer = ["1", "+0.00000E+00"]
    current = d.measure_i()
    assert current == 0.0
    assert format(current, "+.3E") == "+0.000E+00"


def test_driver_a4155c_invert_sign_from_config(res):
    d = A4155C(res)

    res.buffer = ["1"] * 32
    d.configure({"sense.invert_sign": False})
    assert d.is_invert_sign_enabled() is False

    res.buffer = ["1"] * 32
    d.configure({})
    assert d.is_invert_sign_enabled() is True


def test_driver_a4155c_invert_sign_leaves_voltage_alone(res):
    d = defined_driver(res, invert_sign=True)

    res.buffer = ["1", "+1.00000E-12", "-2.50000E+02"]
    current, voltage = d.measure_iv()
    assert current == pytest.approx(-1e-12)
    assert voltage == pytest.approx(-250.0)


def test_driver_a4155c_invert_sign_ignored_for_compliance(res):
    d = defined_driver(res, invert_sign=True)

    res.buffer = ["1"]
    d.set_current_compliance_level(1e-5)

    res.buffer = ["1", "+1.00000E-05"]
    assert d.measure_i() == pytest.approx(-1e-5)
    assert d.compliance_tripped() is True


def test_driver_a4155c_measure_i(res):
    d = defined_driver(res)

    res.buffer = ["1", "N+4.20000E-09"]
    assert d.measure_i() == pytest.approx(4.2e-9)
    assert res.buffer == [
        "*CLS",
        ":PAGE:SCON:MEAS:SING",
        "*OPC",
        "*ESR?",
        ":DATA? 'I1'",
    ]
    assert d.compliance_tripped() is False


def test_driver_a4155c_measure_i_averaged(res):
    d = defined_driver(res)

    res.buffer = ["1", "N+1.00000E-09,N+2.00000E-09,N+3.00000E-09"]
    assert d.measure_i() == pytest.approx(2e-9)


def test_driver_a4155c_measure_i_compliance_status(res):
    d = defined_driver(res)

    res.buffer = ["1", "C+1.00000E-03"]
    assert d.measure_i() == pytest.approx(1e-3)
    assert d.compliance_tripped() is True

    res.buffer = ["1", "N+1.00000E-09"]
    assert d.measure_i() == pytest.approx(1e-9)
    assert d.compliance_tripped() is False


def test_driver_a4155c_measure_i_compliance_level(res):
    """Data carries no status character, so the level decides."""
    d = defined_driver(res)

    res.buffer = ["1"]
    d.set_current_compliance_level(1e-3)

    res.buffer = ["1", "+1.00000E-03"]
    assert d.measure_i() == pytest.approx(1e-3)
    assert d.compliance_tripped() is True

    res.buffer = ["1", "-1.00000E-03"]
    assert d.measure_i() == pytest.approx(-1e-3)
    assert d.compliance_tripped() is True

    res.buffer = ["1", "+5.00000E-04"]
    assert d.measure_i() == pytest.approx(5e-4)
    assert d.compliance_tripped() is False


def test_driver_a4155c_compliance_without_level(res):
    """An unconfigured compliance must not report a trip."""
    d = defined_driver(res)

    res.buffer = ["1", "+0.00000E+00"]
    assert d.measure_i() == pytest.approx(0.0)
    assert d.compliance_tripped() is False


def test_driver_a4155c_measure_i_empty(res):
    d = defined_driver(res)

    res.buffer = ["1", ""]
    with pytest.raises(RuntimeError):
        d.measure_i()


def test_driver_a4155c_measure_iv(res):
    d = defined_driver(res)

    res.buffer = ["1", "N+4.20000E-09", "N+0.00000E+00"]
    current, voltage = d.measure_iv()
    assert current == pytest.approx(4.2e-9)
    assert voltage == pytest.approx(0.0)
    assert res.buffer == [
        "*CLS",
        ":PAGE:SCON:MEAS:SING",
        "*OPC",
        "*ESR?",
        ":DATA? 'I1'",
        ":DATA? 'V1'",
    ]


def test_driver_a4155c_measure_v(res):
    d = defined_driver(res)

    res.buffer = ["1", "N+1.00000E+00"]
    assert d.measure_v() == pytest.approx(1.0)
    assert res.buffer == [
        "*CLS",
        ":PAGE:SCON:MEAS:SING",
        "*OPC",
        "*ESR?",
        ":DATA? 'V1'",
    ]


def test_driver_a4155c_measure_timeout(res):
    d = defined_driver(res)
    d.measurement_timeout = 0.5

    # Event status register never reports operation complete
    res.buffer = ["0"] * 200
    with pytest.raises(RuntimeError):
        d._trigger_measurement(interval=0.01)
    assert ":PAGE:SCON:STOP" in res.buffer
