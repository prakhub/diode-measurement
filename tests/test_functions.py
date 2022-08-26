from diode_measurement import functions


class TestFunctions:

    def assert_range(self, begin, end, step, ref, distance=None):
        r = functions.LinearRange(begin, end, step)
        if distance is not None:
            assert r.distance == distance
        assert list(r) == ref

    def test_range(self):
        self.assert_range(0, 0, 0, [])
        self.assert_range(0, 1, 0, [])
        self.assert_range(1, 0, 0, [])
        self.assert_range(1, 1, 0, [])

        self.assert_range(0, 0, 0, [])
        self.assert_range(0, -1, 0, [])
        self.assert_range(-1, 0, 0, [])
        self.assert_range(-1, -1, 0, [])

        self.assert_range(0, 0, 1, [])
        self.assert_range(0, 1, 1, [0, 1])
        self.assert_range(1, 0, 1, [1, 0])  # auto step
        self.assert_range(1, 1, 1, [])

        self.assert_range(0, 0, 1, [])
        self.assert_range(0, -1, 1, [0, -1])  # auto step
        self.assert_range(-1, 0, 1, [-1, 0])
        self.assert_range(-1, -1, 1, [])

        self.assert_range(0, 0, -1, [])
        self.assert_range(0, 1, -1, [0, 1])  # auto step
        self.assert_range(1, 0, -1, [1, 0])
        self.assert_range(1, 1, -1, [])

        self.assert_range(0, 0, -1, [])
        self.assert_range(0, -1, -1, [0, -1])
        self.assert_range(-1, 0, -1, [-1, 0])  # auto step
        self.assert_range(-1, -1, -1, [])

        self.assert_range(0, 0, 0, [])
        self.assert_range(0, 5, 0, [])
        self.assert_range(5, 0, 0, [])
        self.assert_range(5, 5, 0, [])

        self.assert_range(0, 0, 0, [])
        self.assert_range(0, -5, 0, [])
        self.assert_range(-5, 0, 0, [])
        self.assert_range(-5, -5, 0, [])

        self.assert_range(0, 0, 2.5, [])
        self.assert_range(0, 5, 2.5, [0, 2.5, 5])
        self.assert_range(5, 0, 2.5, [5, 2.5, 0])  # auto step
        self.assert_range(5, 5, 2.5, [])

        self.assert_range(0, 0, 2.5, [])
        self.assert_range(0, -5, 2.5, [0, -2.5, -5])  # auto step
        self.assert_range(-5, 0, 2.5, [-5, -2.5, 0])
        self.assert_range(-5, -5, 2.5, [])

        self.assert_range(0, 0, -2.5, [])
        self.assert_range(0, 5, -2.5, [0, 2.5, 5])  # auto step
        self.assert_range(5, 0, -2.5, [5, 2.5, 0])
        self.assert_range(5, 5, -2.5, [])

        self.assert_range(0, 0, -2.5, [], 0)
        self.assert_range(0, -5, -2.5, [0, -2.5, -5], 5)
        self.assert_range(-5, 0, -2.5, [-5, -2.5, 0], 5)  # auto step
        self.assert_range(-5, -5, -2.5, [], 0)

        self.assert_range(-2.5, 2.5, -2.5, [-2.5, 0, 2.5], 5)  # auto step
        self.assert_range(-2.5, 2.5, 2.5, [-2.5, 0, 2.5], 5)
        self.assert_range(2.5, -2.5, 2.5, [2.5, 0, -2.5], 5)  # auto step
        self.assert_range(2.5, -2.5, -2.5, [2.5, 0, -2.5], 5)

        self.assert_range(-2.5e-12, 2.5e-12, -2.5e-12, [-2.5e-12, 0, 2.5e-12])  # auto step
        self.assert_range(-2.5e-12, 2.5e-12, 2.5e-12, [-2.5e-12, 0, 2.5e-12])
        self.assert_range(2.5e-12, -2.5e-12, 2.5e-12, [2.5e-12, 0, -2.5e-12])  # auto step
        self.assert_range(2.5e-12, -2.5e-12, -2.5e-12, [2.5e-12, 0, -2.5e-12])

        self.assert_range(-2.5e-24, 2.5e-24, -2.5e-24, [-2.5e-24, 0, 2.5e-24])  # auto step
        self.assert_range(-2.5e-24, 2.5e-24, 2.5e-24, [-2.5e-24, 0, 2.5e-24])
        self.assert_range(2.5e-24, -2.5e-24, 2.5e-24, [2.5e-24, 0, -2.5e-24])  # auto step
        self.assert_range(2.5e-24, -2.5e-24, -2.5e-24, [2.5e-24, 0, -2.5e-24])

        self.assert_range(-2.5e+24, 2.5e+24, -2.5e+24, [-2.5e+24, 0, 2.5e+24])  # auto step
        self.assert_range(-2.5e+24, 2.5e+24, 2.5e+24, [-2.5e+24, 0, 2.5e+24])
        self.assert_range(2.5e+24, -2.5e+24, 2.5e+24, [2.5e+24, 0, -2.5e+24])  # auto step
        self.assert_range(2.5e+24, -2.5e+24, -2.5e+24, [2.5e+24, 0, -2.5e+24])

        self.assert_range(0, 0, 5.0, [], 0)
        self.assert_range(0, 1, 5.0, [0, 1], 1)  # limited step
        self.assert_range(1, 0, 5.0, [1, 0], 1)  # limited step
