import unittest

from diode_measurement.driver.k237 import K237

from . import FakeResource


class DriverK237Test(unittest.TestCase):

    def test_driver_k237(self):
        res = FakeResource()
        d = K237(res)

        res.buffer = ['K237A1 ']
        self.assertEqual(d.identity(), 'K237A1')
        self.assertEqual(res.buffer, ['U0X'])

        res.buffer = []
        self.assertEqual(d.reset(), None)
        self.assertEqual(res.buffer, [])

        res.buffer = []
        self.assertEqual(d.clear(), None)
        self.assertEqual(res.buffer, [])

        res.buffer = ['23701000000000000000000000000']
        self.assertEqual(d.error_state(), (1, 'IDDC'))
        self.assertEqual(res.buffer, ['U1X'])
