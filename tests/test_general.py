import pytest

from diode_measurement.gui.general import GeneralWidget


@pytest.fixture
def widget(qtbot):
    widget = GeneralWidget()
    qtbot.addWidget(widget)
    return widget


def test_general_filename_defaults_empty(widget):
    assert widget.filename() == ""
    assert widget.filename_suffix() == ""


def test_general_filename_is_stripped(widget):
    widget.set_filename("  A1_irrad_iv  ")
    widget.set_filename_suffix("  iv_reverse  ")
    assert widget.filename() == "A1_irrad_iv"
    assert widget.filename_suffix() == "iv_reverse"
