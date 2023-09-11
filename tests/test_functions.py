from diode_measurement import functions


def assert_range(begin, end, step, ref, distance=None):
    r = functions.LinearRange(begin, end, step)
    if distance is not None:
        assert r.distance == distance
    assert list(r) == ref

def test_range():
    assert_range(0, 0, 0, [])
    assert_range(0, 1, 0, [])
    assert_range(1, 0, 0, [])
    assert_range(1, 1, 0, [])

    assert_range(0, 0, 0, [])
    assert_range(0, -1, 0, [])
    assert_range(-1, 0, 0, [])
    assert_range(-1, -1, 0, [])

    assert_range(0, 0, 1, [])
    assert_range(0, 1, 1, [0, 1])
    assert_range(1, 0, 1, [1, 0])  # auto step
    assert_range(1, 1, 1, [])

    assert_range(0, 0, 1, [])
    assert_range(0, -1, 1, [0, -1])  # auto step
    assert_range(-1, 0, 1, [-1, 0])
    assert_range(-1, -1, 1, [])

    assert_range(0, 0, -1, [])
    assert_range(0, 1, -1, [0, 1])  # auto step
    assert_range(1, 0, -1, [1, 0])
    assert_range(1, 1, -1, [])

    assert_range(0, 0, -1, [])
    assert_range(0, -1, -1, [0, -1])
    assert_range(-1, 0, -1, [-1, 0])  # auto step
    assert_range(-1, -1, -1, [])

    assert_range(0, 0, 0, [])
    assert_range(0, 5, 0, [])
    assert_range(5, 0, 0, [])
    assert_range(5, 5, 0, [])

    assert_range(0, 0, 0, [])
    assert_range(0, -5, 0, [])
    assert_range(-5, 0, 0, [])
    assert_range(-5, -5, 0, [])

    assert_range(0, 0, 2.5, [])
    assert_range(0, 5, 2.5, [0, 2.5, 5])
    assert_range(5, 0, 2.5, [5, 2.5, 0])  # auto step
    assert_range(5, 5, 2.5, [])

    assert_range(0, 0, 2.5, [])
    assert_range(0, -5, 2.5, [0, -2.5, -5])  # auto step
    assert_range(-5, 0, 2.5, [-5, -2.5, 0])
    assert_range(-5, -5, 2.5, [])

    assert_range(0, 0, -2.5, [])
    assert_range(0, 5, -2.5, [0, 2.5, 5])  # auto step
    assert_range(5, 0, -2.5, [5, 2.5, 0])
    assert_range(5, 5, -2.5, [])

    assert_range(0, 0, -2.5, [], 0)
    assert_range(0, -5, -2.5, [0, -2.5, -5], 5)
    assert_range(-5, 0, -2.5, [-5, -2.5, 0], 5)  # auto step
    assert_range(-5, -5, -2.5, [], 0)

    assert_range(-2.5, 2.5, -2.5, [-2.5, 0, 2.5], 5)  # auto step
    assert_range(-2.5, 2.5, 2.5, [-2.5, 0, 2.5], 5)
    assert_range(2.5, -2.5, 2.5, [2.5, 0, -2.5], 5)  # auto step
    assert_range(2.5, -2.5, -2.5, [2.5, 0, -2.5], 5)

    assert_range(-2.5e-12, 2.5e-12, -2.5e-12, [-2.5e-12, 0, 2.5e-12])  # auto step
    assert_range(-2.5e-12, 2.5e-12, 2.5e-12, [-2.5e-12, 0, 2.5e-12])
    assert_range(2.5e-12, -2.5e-12, 2.5e-12, [2.5e-12, 0, -2.5e-12])  # auto step
    assert_range(2.5e-12, -2.5e-12, -2.5e-12, [2.5e-12, 0, -2.5e-12])

    assert_range(-2.5e-24, 2.5e-24, -2.5e-24, [-2.5e-24, 0, 2.5e-24])  # auto step
    assert_range(-2.5e-24, 2.5e-24, 2.5e-24, [-2.5e-24, 0, 2.5e-24])
    assert_range(2.5e-24, -2.5e-24, 2.5e-24, [2.5e-24, 0, -2.5e-24])  # auto step
    assert_range(2.5e-24, -2.5e-24, -2.5e-24, [2.5e-24, 0, -2.5e-24])

    assert_range(-2.5e+24, 2.5e+24, -2.5e+24, [-2.5e+24, 0, 2.5e+24])  # auto step
    assert_range(-2.5e+24, 2.5e+24, 2.5e+24, [-2.5e+24, 0, 2.5e+24])
    assert_range(2.5e+24, -2.5e+24, 2.5e+24, [2.5e+24, 0, -2.5e+24])  # auto step
    assert_range(2.5e+24, -2.5e+24, -2.5e+24, [2.5e+24, 0, -2.5e+24])

    assert_range(0, 0, 5.0, [], 0)
    assert_range(0, 1, 5.0, [0, 1], 1)  # limited step
    assert_range(1, 0, 5.0, [1, 0], 1)  # limited step
