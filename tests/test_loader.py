import unittest

import pyparsing

from xwatc_zwei import LEVELS, loader

class TestLoader(unittest.TestCase):
    def test_header(self):
        loader.Header.parse_string("/faa/ Hier bist du also", parse_all=True)
        with self.assertRaises(pyparsing.ParseException):
            loader.Header.parse_string("hhaga")
    
    def test_sprung(self):
        loader.Sprung.parse_string(">faa", parse_all=True)
        with self.assertRaises(pyparsing.ParseException):
            loader.Sprung.parse_string(">hhaga aha", parse_all=True)
    
    def test_entscheidung(self):
        loader.Entscheidung.parse_string("""\
:süd: Süden
    / Ich will Monster jagen!
""", parse_all=True)
        loader.Entscheidung.parse_string("""\
:süd<blut>:
    / Ich will Monster jagen!
""", parse_all=True)
        with self.assertRaises((pyparsing.ParseBaseException)):
            loader.Entscheidung.parse_string("""\
:süd
    / Ich will Monster jagen!
""", parse_all=True)
    
    def test_hat(self):
        loader.Bedingung.parse_string("hat(speer)", parse_all=True)
        loader.Bedingungskopf.parse_string("<hat(speer)>", parse_all=True)
        loader.Entscheidung.parse_string("""\
:süd<hat(speer)>: Süd
    / Ich will Monster jagen!
""", parse_all=True)
    
    def test_bedingung(self):
        loader.Bedingungskopf.parse_string("<hat(speer), flink(70), glück(67)>", parse_all=True)
    
    def test_recursive(self):
        try:
            loader.Zeile.parse_string("""\
:süd: Süden
    :nord: Zurück
        / Willkommen zurück, Wanderer!
""", parse_all=True)
        except pyparsing.ParseException as exc:
            print(exc.explain())
            raise
    
    def test_start(self):
        loader.GeschichteBody.parse_string("""\
/Norden/ Du kommst ans Meer!
:luft: Die Luft einatmen
    /Die Luft schmeckt salzig. Dir ist hungrig.""")
    

    
    def test_szenario(self):
        print(loader.load_scenario(LEVELS / "scenario1.cfg"))