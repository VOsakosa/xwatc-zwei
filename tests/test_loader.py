import unittest

import pyparsing

from xwatc_zwei import loader

class TestLoader(unittest.TestCase):
    def test_header(self):
        loader.Header.parse_string("/faa/ Hier bist du also", parse_all=True)
        with self.assertRaises(pyparsing.ParseException):
            loader.Header.parse_string("hhaga")
    
    def test_entscheidung(self):
        loader.Entscheidung.parse_string("""\
:süd:
    / Ich will Monster jagen!
""", parse_all=True)
        loader.Entscheidung.parse_string("""\
:süd<blut>:
    / Ich will Monster jagen!
""", parse_all=True)
        with self.assertRaises(pyparsing.ParseException):
            loader.Entscheidung.parse_string("""\
:süd
    / Ich will Monster jagen!
""", parse_all=True)
    
    def test_hat(self):
        loader.Entscheidung.parse_string("""\
:süd<hat(speer)>:
    / Ich will Monster jagen!
""", parse_all=True)