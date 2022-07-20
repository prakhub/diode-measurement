from diode_measurement.resource import Resource


class TestResource:

    def test_resource(self):
        res = Resource("TCPIP::localhost:8080::SOCKET", "@sim")
        assert res.resource_name == "TCPIP::localhost:8080::SOCKET"
        assert res.visa_library == "@sim"
        assert res.options == {
            "read_termination": "\r\n",
            "write_termination": "\r\n",
            "timeout": 8000
        }
