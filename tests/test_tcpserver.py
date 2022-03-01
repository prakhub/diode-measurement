import unittest

from diode_measurement import tcpserver


class TCPServerTest(unittest.TestCase):

    def test_is_finite(self):
        self.assertTrue(tcpserver.is_finite(0))
        self.assertTrue(tcpserver.is_finite(-42.))
        self.assertTrue(tcpserver.is_finite('foo'))
        self.assertFalse(tcpserver.is_finite(float('nan')))
        self.assertFalse(tcpserver.is_finite(float('+inf')))
        self.assertFalse(tcpserver.is_finite(float('-inf')))

    def test_json_dict(self):
        self.assertEqual(
            tcpserver.json_dict({'a': float('nan'), 'b': 42., 'c': '42'}),
            {'a': None, 'b': 42., 'c': '42'}
        )
