import inspect
from typing import Any
import unittest

import pyparsing

from xwatc_zwei import LEVELS, geschichte, loader, verteiler


def rule_test(rule: pyparsing.ParserElement, text: str) -> Any:
    """Test a rule """
    rule.set_debug(True)
    return rule.parse_string(inspect.cleandoc(text), parse_all=True)


class TestLoader(unittest.TestCase):
    def test_header(self):
        loader.Header.parse_string("/faa/ Hier bist du also", parse_all=True)
        with self.assertRaises(pyparsing.ParseException):
            loader.Header.parse_string("hhaga")

    def test_sprung(self):
        loader.Sprung.parse_string(">faa", parse_all=True)
        with self.assertRaises(pyparsing.ParseException):
            loader.Sprung.parse_string(">hhaga aha", parse_all=True)
        self.assertEqual(rule_test(loader.Sprung, "> dort")[0], geschichte.Sprung("dort"))
        self.assertEqual(rule_test(loader.Sprung, "> SELF")[0],
                         geschichte.Sprung(geschichte.Sonderziel.Self))

    def test_entscheidung(self):
        loader.Entscheidungsblock.parse_string("""\
:süd: Süden
    / Ich will Monster jagen!
""", parse_all=True)
        loader.Entscheidungsblock.parse_string("""\
:süd<blut>:
    / Ich will Monster jagen!
""", parse_all=True)
        with self.assertRaises((pyparsing.ParseBaseException)):
            loader.Entscheidungsblock.parse_string("""\
:süd
    / Ich will Monster jagen!
""", parse_all=True)

    def test_hat(self):
        loader.Bedingung.parse_string("hat(speer)", parse_all=True)
        loader.Bedingungskopf.parse_string("<hat(speer)>", parse_all=True)
        loader.Entscheidungsblock.parse_string("""\
:süd<hat(speer)>: Süd
    / Ich will Monster jagen!
""", parse_all=True)

    def test_bedingung(self):
        loader.Bedingungskopf.parse_string("<hat(speer), flink(70), glück(67)>", parse_all=True)

    def test_recursive(self):
        loader.Zeile.parse_string("""\
:süd: Süden
    :nord: Zurück
        / Willkommen zurück, Wanderer!
""", parse_all=True)
        block: verteiler.Geschichtsmodul = rule_test(loader.Modul, """
            /test/ Du kannst nach Süden.
            :süd: Süden
                :nord: Zurück
                    / You're back!
                :weiter: Weiter
                    / Du fällst in eine Grube
            :dings: Nicht Süden
                / Ich will nicht mehr!
        """)[0]
        self.assertIsInstance(block, verteiler.Geschichtsmodul)
        assert isinstance(block.zeilen[1], geschichte.Entscheidung)
        self.assertListEqual([w.id for w in block.zeilen[1].wahlen], ["süd", "dings"])

    def test_start(self):
        loader.GeschichteBody.parse_string("""\
/Norden/ Du kommst ans Meer!
:luft: Die Luft einatmen
    /Die Luft schmeckt salzig. Dir ist hungrig.""")

    def test_szenario(self):
        print(loader.load_scenario(LEVELS / "scenario1.cfg"))
    
    def test_szenario_pilzfee(self):
        print(loader.load_scenario(LEVELS / "Die_Pilzfee.cfg"))
