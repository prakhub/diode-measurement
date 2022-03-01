import unittest

from diode_measurement import utils

class UtilsTest(unittest.TestCase):

    def test_get_resource(self):
        self.assertEqual(utils.get_resource('16'), ('GPIB0::16::INSTR', ''))
        self.assertEqual(utils.get_resource('GPIB::13::INSTR'), ('GPIB::13::INSTR', ''))
        self.assertEqual(utils.get_resource('localhost:10001'), ('TCPIP0::localhost::10001::SOCKET', '@py'))
        self.assertEqual(utils.get_resource('192.168.0.1:10002'), ('TCPIP0::192.168.0.1::10002::SOCKET', '@py'))
        self.assertEqual(utils.get_resource('TCPIP::192.168.0.1::1080::SOCKET'), ('TCPIP::192.168.0.1::1080::SOCKET', '@py'))

    def test_safe_filename(self):
        self.assertEqual(utils.safe_filename('Monty Python\'s!'), 'Monty_Python_s_')
        self.assertEqual(utils.safe_filename('$2020-02-22 13:14:25'), '_2020-02-22_13_14_25')

    def test_auto_scale(self):
        self.assertEqual(utils.auto_scale(1024), (1e3, 'k', 'kilo'))
        self.assertEqual(utils.auto_scale(256), (1e0, '', ''))
        self.assertEqual(utils.auto_scale(0), (1e0, '', ''))
        self.assertEqual(utils.auto_scale(0.042), (1e-3, 'm', 'milli'))
        self.assertEqual(utils.auto_scale(0.00042), (1e-6, 'u', 'micro'))

    def test_format_metric(self):
        self.assertEqual(utils.format_metric(0.0042, 'A'), '4.200 mA')
        self.assertEqual(utils.format_metric(0.0042, 'A', 1), '4.2 mA')

    def test_format_switch(self):
        self.assertEqual(utils.format_switch(0), 'OFF')
        self.assertEqual(utils.format_switch(1), 'ON')

    def test_limits(self):
        self.assertEqual(utils.limits([]), tuple())
        self.assertEqual(utils.limits([[4, 2]]), (4, 4, 2, 2))
        self.assertEqual(utils.limits([[4, 5], [4, 3], [-1, 2]]), (-1, 4, 2, 5))
        self.assertEqual(utils.limits([[-1, 2], [4, 5], [4, 3]]), (-1, 4, 2, 5))
        self.assertEqual(utils.limits([[1, -2], [4, -5], [4, -3]]), (1, 4, -5, -2))

    def test_inverse_square(self):
        with self.assertRaises(ZeroDivisionError):
            utils.inverse_square(0)
        self.assertEqual(utils.inverse_square(1), 1)
        self.assertEqual(utils.inverse_square(2), .25)
        self.assertEqual(utils.inverse_square(8), .015625)
