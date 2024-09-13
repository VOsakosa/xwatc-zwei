import inspect
from typing import Any
import unittest

import pyparsing

from xwatc_zwei import LEVELS, geschichte, loader, verteiler


def rule_test(rule: pyparsing.ParserElement, text: str) -> Any:
    """Test a rule """
    # rule.set_debug(True)
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
    
    def test_if_elif(self) -> None:
        gmodule = rule_test(loader.GeschichteBody, """
        /test/
        <hat(speer)>
            / Ich steche dich ab!
        <hat(schwert)>
            / Ich bringe dich um!
        <>
            / Ich werde dich irgendwie umbringen!
        """)
        self.assertEqual(len(gmodule), 1)
        gmodul: verteiler.Geschichtsmodul = gmodule[0]
        self.assertIsInstance(gmodul, verteiler.Geschichtsmodul)
        self.assertEqual(len(gmodul.zeilen), 1)
        ifelif = gmodul.zeilen[0]
        assert isinstance(ifelif, geschichte.IfElif)
        self.assertEqual(len(ifelif.fälle), 3)
        self.assertIsNone(ifelif.fälle[2][0])
        self.assertEqual(ifelif.fälle[0][0], geschichte.FuncBedingung("hat", ["speer"]))

    def test_hat(self):
        loader.Bedingung.parse_string("hat(speer)", parse_all=True)
        loader.Bedingungskopf.parse_string("<hat(speer)>", parse_all=True)
        loader.Entscheidungsblock.parse_string("""\
:süd<hat(speer)>: Süd
    / Ich will Monster jagen!
""", parse_all=True)

    def test_und_bedingung(self):
        bed = loader.parse_bedingung("hat(speer), flink(70), glück(67)")
        self.assertIsInstance(bed, geschichte.UndBedingung)
        self.assertEqual(len(bed.bedingungen), 3)
        self.assertEqual(bed.bedingungen[0], geschichte.FuncBedingung("hat", ["speer"]))
    
    def test_oder_bedingung(self):
        bed = loader.parse_bedingung("hat(speer) | flink(70) | glück(67)")
        self.assertIsInstance(bed, geschichte.OderBedingung)
        self.assertEqual(len(bed.bedingungen), 3)
        self.assertEqual(bed.bedingungen[2], geschichte.FuncBedingung("glück", [67]))
    
    def test_und_oder_bedingung(self):
        bed = loader.Bedingungskopf.parse_string("<hat(speer) , flink(70) | !glück(67)>",
                                                 parse_all=True)
        self.assertIsInstance(bed[0], geschichte.OderBedingung)
        self.assertEqual(len(bed[0].bedingungen), 2)
        self.assertEqual(bed[0].bedingungen[0], geschichte.UndBedingung(
            [geschichte.FuncBedingung("hat", ["speer"]), geschichte.FuncBedingung("flink", [70])]
        ))
        self.assertEqual(bed[0].bedingungen[1], geschichte.NichtBedingung(
            geschichte.FuncBedingung("glück", [67])
        ))

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
        loader.load_scenario(LEVELS / "scenario1.cfg")
    
    def test_szenario_pilzfee(self):
        loader.load_scenario(LEVELS / "Die_Pilzfee.cfg")
