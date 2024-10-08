
import unittest

from pyparsing import ParseBaseException
from xwatc_zwei import LEVELS, geschichte, loader
from xwatc_zwei import verteiler
from xwatc_zwei.verteiler import Geschichtsblock, Spielzustand, VarTypError, Geschichte


class TestVerteiler(unittest.TestCase):

    def test_modul_by_id(self) -> None:
        vert = Geschichte([
            Geschichtsblock("a", [geschichte.Text("a")]),
            Geschichtsblock("b", [geschichte.Text("b")]),
            Geschichtsblock("C2PO", [geschichte.Text("R2-D2!")]),
        ])
        self.assertEqual(vert.block_by_id("a").id, "a")
        self.assertEqual(vert.block_by_id("C2PO").id, "C2PO")
        with self.assertRaises(KeyError):
            vert.block_by_id("C")

        # Not case-insensitive
        with self.assertRaises(KeyError):
            vert.block_by_id("A")

    def test_disallow_doubled_id(self) -> None:
        with self.assertRaises(ValueError):
            Geschichte([
                Geschichtsblock("a", [geschichte.Text("a")]),
                Geschichtsblock("a", [geschichte.Text("nichts zu tun")])
            ])


TEST_MODUL = Geschichtsblock("test", [
    geschichte.Text("Du bist im Wald"),
    geschichte.IfElif(fälle=[
        (loader.parse_bedingung("hat(schwert)"), [
            geschichte.Text("Du hast ein Schwert!")
        ])
    ]),
    geschichte.Entscheidung([
        geschichte.Wahlmöglichkeit("a", "hin", block=[
            geschichte.Text("Du gehst hin."),
            geschichte.Entscheidung([
                geschichte.Wahlmöglichkeit("z", "zurück", block=[
                    geschichte.Text("Und du bist wieder zurück"),
                    geschichte.Sprung("test"),
                ]),
                geschichte.Wahlmöglichkeit("w", "weiter", block=[
                    geschichte.Text("Und du gehst weiter"),
                    geschichte.Text("Ende!!"),
                ]),
            ])
        ]),
        geschichte.Wahlmöglichkeit("b", "her", block=[
            geschichte.Text("Hallo Alter!")
        ]),
    ])
])


class TestGModul(unittest.TestCase):

    def test_getitem(self) -> None:
        modul = TEST_MODUL
        self.assertEqual(modul[0], geschichte.Text("Du bist im Wald"))
        self.assertEqual(modul[0,], geschichte.Text("Du bist im Wald"))
        self.assertIsInstance(modul[1], geschichte.IfElif)
        self.assertEqual(modul[1, 0, 0], geschichte.Text("Du hast ein Schwert!"))
        self.assertEqual(modul[1, 0, 0], geschichte.Text("Du hast ein Schwert!"))
        self.assertEqual(modul[2, 0, 1, 0, 1], geschichte.Sprung("test"))
        with self.assertRaises(IndexError):
            modul[5, 0, 0]
        with self.assertRaises(IndexError):
            modul[0, 5, 0]


class TestSpielzustand(unittest.TestCase):

    def test_run(self) -> None:
        modul = TEST_MODUL
        zustand = Spielzustand.aus_geschichte(Geschichte([modul]))
        with self.assertRaises(ValueError):
            zustand.run("wahl")
        outputs, input = zustand.run("")
        outputs = list(outputs)
        self.assertListEqual(outputs, [geschichte.Text("Du bist im Wald")])
        # Mänx hat kein Schwert.
        self.assertIsInstance(input, geschichte.Entscheidung)
        with self.assertRaises(KeyError):
            zustand.run("")
        outputs, input = zustand.run("b")
        self.assertEqual(outputs[0], geschichte.Text("Hallo Alter!"))

    def test_modulvariable_bedingung(self) -> None:
        zustand = Spielzustand.aus_geschichte(Geschichte([TEST_MODUL]))
        zustand._position = verteiler.Weltposition.start(
            zustand.verteiler.nächste_geschichte(zustand))
        zustand._position.modul_vars["dritte_frau_tot"] = True
        self.assertTrue(zustand.eval_bedingung(loader.parse_bedingung("dritte_frau_tot")))
        self.assertFalse(zustand.eval_bedingung(loader.parse_bedingung("!(dritte_frau_tot)")))
        self.assertFalse(zustand.eval_bedingung(loader.parse_bedingung("zweite_frau_tot")))
        self.assertTrue(zustand.eval_bedingung(loader.parse_bedingung("!zweite_frau_tot")))

    def test_weltvariable_bedingung(self) -> None:
        zustand = Spielzustand.aus_geschichte(Geschichte([TEST_MODUL]))
        assert zustand._welt
        zustand._welt.setze_variable("dritte_frau_tot", True)
        with self.assertRaises(ParseBaseException):
            loader.parse_bedingung(". dritte_frau_tot")
        self.assertTrue(zustand.eval_bedingung(loader.parse_bedingung(".dritte_frau_tot")))
        self.assertFalse(zustand.eval_bedingung(loader.parse_bedingung("!(.dritte_frau_tot)")))
        self.assertFalse(zustand.eval_bedingung(loader.parse_bedingung(".zweite_frau_tot")))
        self.assertTrue(zustand.eval_bedingung(loader.parse_bedingung("!.zweite_frau_tot")))

    def test_eigenschaft_bedingung(self) -> None:
        zustand = Spielzustand.aus_geschichte(Geschichte([TEST_MODUL]))
        zustand.assert_get_mänx()._werte["schlau"] = 12
        self.assertTrue(zustand.eval_bedingung(loader.parse_bedingung("schlau(1)")))
        self.assertTrue(zustand.eval_bedingung(loader.parse_bedingung("schlau(12)")))
        self.assertFalse(zustand.eval_bedingung(loader.parse_bedingung("schlau(13)")))
        self.assertFalse(zustand.eval_bedingung(loader.parse_bedingung("stabil(12)")))
        self.assertTrue(zustand.eval_bedingung(loader.parse_bedingung("stabil(10)")))
        self.assertTrue(zustand.eval_bedingung(loader.parse_bedingung("stabil(10), schlau(12)")))
        self.assertTrue(zustand.eval_bedingung(loader.parse_bedingung("stabil(10), !schlau(13)")))

    def test_fähigkeit_bedingung(self) -> None:
        zustand = Spielzustand.aus_geschichte(Geschichte([TEST_MODUL]))
        assert zustand._mänx
        zustand.assert_get_mänx().set_fähigkeit("fliegen", 3)
        self.assertTrue(zustand.eval_bedingung(loader.parse_bedingung("f(fliegen,1)")))
        self.assertTrue(zustand.eval_bedingung(loader.parse_bedingung("f(fliegen,3)")))
        self.assertFalse(zustand.eval_bedingung(loader.parse_bedingung("f(fliegen,5)")))
        self.assertFalse(zustand.eval_bedingung(loader.parse_bedingung("f(liegen,1)")))
        with self.assertRaises(VarTypError):
            zustand.eval_bedingung(loader.parse_bedingung("f(fliegen, -1)"))
        with self.assertRaises(VarTypError):
            zustand.eval_bedingung(loader.parse_bedingung("f(fliegen, 0)"))

    def test_setze_variable(self) -> None:
        zustand = Spielzustand.aus_geschichte(Geschichte([Geschichtsblock("test", [
            geschichte.SetzeVariable("testvar", "blubb"),
            geschichte.SetzeVariable(".testvar", "globalblubb"),
            geschichte.Entscheidung([geschichte.Wahlmöglichkeit("w", "Weiter", [
                geschichte.Text("ff")]
            )]),
            geschichte.SetzeVariable("othervar", 4),
            geschichte.SetzeVariable("testvar", 4)
        ])]))
        outputs, input = zustand.run("")
        self.assertFalse(outputs)
        self.assertIsInstance(input, geschichte.Entscheidung)
        self.assertEqual(zustand.assert_get_welt().get_variable("testvar", ""), "globalblubb")
        assert zustand._position
        self.assertEqual(zustand._position.modul_vars["testvar"], "blubb")
        with self.assertRaises(VarTypError):
            zustand.run("w")

    # def test_bedingungen(selfself) ->None:
        # Was ist das für ein Fehlertyp?
        # with self.assertRaises():
        # geschichte.IfElif(parse_bed("hat()"))
