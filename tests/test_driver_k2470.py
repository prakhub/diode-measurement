import os
import unittest

from diode_measurement.driver.k2470 import K2470

from . import FakeResource

class DriverK2470Test(unittest.TestCase):

    def test_driver_k2470(self):
        res = FakeResource()
        d = K2470(res)

        res.buffer = ['Keithley 2470']
        self.assertEqual(d.identity(), 'Keithley 2470')
        self.assertEqual(res.buffer, ['*IDN?'])

        res.buffer = ['1']
        self.assertEqual(d.reset(), None)
        self.assertEqual(res.buffer, ['*RST', '*OPC?'])

        res.buffer = ['1']
        self.assertEqual(d.clear(), None)
        self.assertEqual(res.buffer, ['*CLS', '*OPC?'])

        res.buffer = ['0,"no error;;"']
        self.assertEqual(d.error_state(), (0, 'no error;;'))
        self.assertEqual(res.buffer, [':SYST:ERR?'])
