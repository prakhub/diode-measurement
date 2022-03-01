import unittest

from diode_measurement.resource import Resource

class ResourceTest(unittest.TestCase):

    def test_resource(self):
        res = Resource('TCPIP::localhost:8080::SOCKET', '@sim')
        self.assertEqual(res.resource_name, 'TCPIP::localhost:8080::SOCKET')
        self.assertEqual(res.visa_library, '@sim')
        self.assertEqual(res.options, {
            'read_termination': '\r\n',
            'write_termination': '\r\n',
            'timeout': 8000
        })
