import unittest

from xwatc_zwei.mänx import Mänx

class TestMänx(unittest.TestCase):
    def test_get_wert(self):
        self.assertEqual(Mänx.default().get_wert("flink"), 10)
        self.assertEqual(Mänx.default().get_wert("stabil"), 10)
        with self.assertRaises(KeyError):
            Mänx.default().get_wert("blubb")