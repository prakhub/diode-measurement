import unittest

from diode_measurement import functions


class FunctionsTest(unittest.TestCase):

    def assertRange(self, begin, end, step, ref, distance=None):
        r = functions.LinearRange(begin, end, step)
        if distance is not None:
            self.assertEqual(r.distance, distance)
        self.assertEqual(list(r), ref)

    def test_range(self):
        self.assertRange(0, 0, 0, [])
        self.assertRange(0, 1, 0, [])
        self.assertRange(1, 0, 0, [])
        self.assertRange(1, 1, 0, [])

        self.assertRange(0, 0, 0, [])
        self.assertRange(0, -1, 0, [])
        self.assertRange(-1, 0, 0, [])
        self.assertRange(-1, -1, 0, [])

        self.assertRange(0, 0, 1, [])
        self.assertRange(0, 1, 1, [0, 1])
        self.assertRange(1, 0, 1, [1, 0])  # auto step
        self.assertRange(1, 1, 1, [])

        self.assertRange(0, 0, 1, [])
        self.assertRange(0, -1, 1, [0, -1])  # auto step
        self.assertRange(-1, 0, 1, [-1, 0])
        self.assertRange(-1, -1, 1, [])

        self.assertRange(0, 0, -1, [])
        self.assertRange(0, 1, -1, [0, 1])  # auto step
        self.assertRange(1, 0, -1, [1, 0])
        self.assertRange(1, 1, -1, [])

        self.assertRange(0, 0, -1, [])
        self.assertRange(0, -1, -1, [0, -1])
        self.assertRange(-1, 0, -1, [-1, 0])  # auto step
        self.assertRange(-1, -1, -1, [])

        self.assertRange(0, 0, 0, [])
        self.assertRange(0, 5, 0, [])
        self.assertRange(5, 0, 0, [])
        self.assertRange(5, 5, 0, [])

        self.assertRange(0, 0, 0, [])
        self.assertRange(0, -5, 0, [])
        self.assertRange(-5, 0, 0, [])
        self.assertRange(-5, -5, 0, [])

        self.assertRange(0, 0, 2.5, [])
        self.assertRange(0, 5, 2.5, [0, 2.5, 5])
        self.assertRange(5, 0, 2.5, [5, 2.5, 0])  # auto step
        self.assertRange(5, 5, 2.5, [])

        self.assertRange(0, 0, 2.5, [])
        self.assertRange(0, -5, 2.5, [0, -2.5, -5])  # auto step
        self.assertRange(-5, 0, 2.5, [-5, -2.5, 0])
        self.assertRange(-5, -5, 2.5, [])

        self.assertRange(0, 0, -2.5, [])
        self.assertRange(0, 5, -2.5, [0, 2.5, 5])  # auto step
        self.assertRange(5, 0, -2.5, [5, 2.5, 0])
        self.assertRange(5, 5, -2.5, [])

        self.assertRange(0, 0, -2.5, [], 0)
        self.assertRange(0, -5, -2.5, [0, -2.5, -5], 5)
        self.assertRange(-5, 0, -2.5, [-5, -2.5, 0], 5)  # auto step
        self.assertRange(-5, -5, -2.5, [], 0)

        self.assertRange(-2.5, 2.5, -2.5, [-2.5, 0, 2.5], 5)  # auto step
        self.assertRange(-2.5, 2.5, 2.5, [-2.5, 0, 2.5], 5)
        self.assertRange(2.5, -2.5, 2.5, [2.5, 0, -2.5], 5)  # auto step
        self.assertRange(2.5, -2.5, -2.5, [2.5, 0, -2.5], 5)

        self.assertRange(-2.5e-12, 2.5e-12, -2.5e-12, [-2.5e-12, 0, 2.5e-12])  # auto step
        self.assertRange(-2.5e-12, 2.5e-12, 2.5e-12, [-2.5e-12, 0, 2.5e-12])
        self.assertRange(2.5e-12, -2.5e-12, 2.5e-12, [2.5e-12, 0, -2.5e-12])  # auto step
        self.assertRange(2.5e-12, -2.5e-12, -2.5e-12, [2.5e-12, 0, -2.5e-12])

        self.assertRange(-2.5e-24, 2.5e-24, -2.5e-24, [-2.5e-24, 0, 2.5e-24])  # auto step
        self.assertRange(-2.5e-24, 2.5e-24, 2.5e-24, [-2.5e-24, 0, 2.5e-24])
        self.assertRange(2.5e-24, -2.5e-24, 2.5e-24, [2.5e-24, 0, -2.5e-24])  # auto step
        self.assertRange(2.5e-24, -2.5e-24, -2.5e-24, [2.5e-24, 0, -2.5e-24])
