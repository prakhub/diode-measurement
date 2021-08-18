import os
import unittest

from diode_measurement.driver.k2657a import K2657A

from . import FakeResource

class DriverK2657ATest(unittest.TestCase):

    def test_driver_k2657a(self):
        res = FakeResource()
        d = K2657A(res)

        res.buffer = ['Keithley 2657A']
        self.assertEqual(d.identity(), 'Keithley 2657A')
        self.assertEqual(res.buffer, ['*IDN?'])

        res.buffer = ['1']
        self.assertEqual(d.reset(), None)
        self.assertEqual(res.buffer, ['reset()', '*OPC?'])

        res.buffer = ['1']
        self.assertEqual(d.clear(), None)
        self.assertEqual(res.buffer, ['status.reset()', '*OPC?'])

        res.buffer = ['0\tno error\t123\t0']
        self.assertEqual(d.error_state(), (0, 'no error'))
        self.assertEqual(res.buffer, ['print(errorqueue.next())'])
