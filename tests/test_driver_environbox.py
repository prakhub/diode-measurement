from diode_measurement.driver.environbox import EnvironBox, parse_error, parse_pc_data

from . import FakeResource


class TestDriverEnvironBox:

    def test_driver_environbox(self):
        res = FakeResource()
        d = EnvironBox(res)

        res.buffer = ["Environment Box v1.0\r"]
        assert d.identity() == "Environment Box v1.0"
        assert res.buffer == ["*IDN?"]

        res.buffer = []
        assert d.reset() is None
        assert res.buffer == []

        res.buffer = []
        assert d.clear() is None
        assert res.buffer == []

    def test_parse_error(self):
        error = parse_error("err0")
        assert error.code == 0
        assert error.message == "Unknown error"

        error = parse_error("err80")
        assert error.code == 80
        assert error.message == "DAC not found"

    def test_parse_pc_data(self):
        response = "0,1.23,2.34,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,85,1,0,0,0,0,0,0,3.45,0.21,0.23,0.34,0,0,0,0"
        data = parse_pc_data(response)
        assert data["box_humidity"] == 1.23
        assert data["box_temperature"] == 2.34
        assert data["power_microscope_ctrl"] == True
        assert data["power_box_light"] == False
        assert data["power_probecard_light"] == True
        assert data["power_laser_sensor"] == False
        assert data["power_probecard_camera"] == True
        assert data["power_microscope_camera"] == False
        assert data["power_microscope_light"] == True
        assert data["box_light"] == True
        assert data["box_door"] == False
        assert data["discharge_time"] == 3.45
        assert data["box_lux"] == 0.21
        assert data["pt100_1"] == 0.23
        assert data["pt100_2"] == 0.34
