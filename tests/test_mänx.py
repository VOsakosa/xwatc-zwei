import unittest

from xwatc_zwei.mänx import Mänx

class TestMänx(unittest.TestCase):
    def test_get_wert(self):
        self.assertEqual(Mänx.default().get_wert("flink"), 10)
        self.assertEqual(Mänx.default().get_wert("stabil"), 10)
        with self.assertRaises(KeyError):
            Mänx.default().get_wert("blubb")
    
    def test_get_set_fähigkeit(self):
        m = Mänx.default()
        self.assertEqual(m.get_fähigkeit("fliegen"), 0)
        m.set_fähigkeit("fliegen", 2)
        with self.assertRaises(ValueError):
            m.set_fähigkeit("fliegen", -1)
        with self.assertRaises(ValueError):
            m.set_fähigkeit("fliegen", 6)
        with self.assertRaises(ValueError):
            m.set_fähigkeit("fliegen", -80)
        self.assertEqual(m.get_fähigkeit("fliegen"), 2)
        self.assertEqual(m.get_fähigkeit("liegen"), 0)

        m.set_fähigkeit("fliegen", 5)
        self.assertEqual(m.get_fähigkeit("fliegen"), 5)
        m.set_fähigkeit("fliegen", 0)
        self.assertEqual(m.get_fähigkeit("fliegen"), 0)

