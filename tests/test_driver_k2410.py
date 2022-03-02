import unittest

from diode_measurement.driver.k2410 import K2410

from . import FakeResource


class DriverK2410Test(unittest.TestCase):

    def test_driver_k2400(self):
        res = FakeResource()
        K2410(res)
