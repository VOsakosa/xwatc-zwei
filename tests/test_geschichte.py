
import unittest
from xwatc_zwei import LEVELS, geschichte, loader
from xwatc_zwei.verteiler import Geschichtsmodul, Verteiler


class TestVerteiler(unittest.TestCase):

    def test_modul_by_id(self) -> None:
        vert = Verteiler([
            Geschichtsmodul("a", [geschichte.Text("a")]),
            Geschichtsmodul("b", [geschichte.Text("b")]),
            Geschichtsmodul("C2PO", [geschichte.Text("R2-D2!")]),
        ])
        self.assertEqual(vert.modul_by_id("a").id, "a")
        self.assertEqual(vert.modul_by_id("C2PO").id, "C2PO")
        with self.assertRaises(KeyError):
            vert.modul_by_id("C")

        # Not case-insensitive
        with self.assertRaises(KeyError):
            vert.modul_by_id("A")
    
    def test_disallow_doubled_id(self) -> None:
        with self.assertRaises(ValueError):
            Verteiler([
                Geschichtsmodul("a", [geschichte.Text("a")]),
                Geschichtsmodul("a", [geschichte.Text("nichts zu tun")])
            ])

class TestGModul(unittest.TestCase):

    def test_getitem(self) -> None:
        parse_bed = lambda s:s
        modul = Geschichtsmodul("test", [
            geschichte.Text("Du bist im Wald"),
            geschichte.IfElif(fälle=[
                (parse_bed("has(schwert)"), [
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
        self.assertEqual(modul[0], geschichte.Text("Du bist im Wald"))
        self.assertEqual(modul[0,], geschichte.Text("Du bist im Wald"))
        self.assertIsInstance(modul[1], geschichte.IfElif)
        self.assertEqual(modul[1,0,0], geschichte.Text("Du hast ein Schwert!"))
        self.assertEqual(modul[1,0,0], geschichte.Text("Du hast ein Schwert!"))
        self.assertEqual(modul[2,0,1,0,1], geschichte.Sprung("test"))