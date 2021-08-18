import os
import unittest

from diode_measurement import functions

class ResourceTest(unittest.TestCase):

    def test_linear_range(self):
        r = functions.LinearRange(0., 1., 0.25)
        self.assertEqual(r.begin, 0)
        self.assertEqual(r.end, 1)
        self.assertEqual(r.step, 0.25)
        self.assertEqual(len(r), 4)
        self.assertEqual(list(r), [0, 0.25, 0.5, 0.75, 1])
