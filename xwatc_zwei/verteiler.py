"""Die Verteiler wählen Geschichtsmodule"""
from collections.abc import Sequence
from queue import PriorityQueue
import random
from typing import Any, Self, assert_never, cast

from attrs import Factory, define, field

from xwatc_zwei import bedingung
from xwatc_zwei import mänx as mänx_mod
from xwatc_zwei import geschichte
from xwatc_zwei.geschichte import (Bedingung, Bedingungsobjekt, Entscheidung, FunktionsZeile,
                                   IfElif, InputZeile, OutputZeile, Sonderziel, Sprung, VarTypError, Zeile)


@define
class Geschichtsblock:
    """Ein einzelner, ununterbrochener Geschichtsstrang."""
    id: str
    zeilen: list[Zeile]

    def __getitem__(self, key: int | Sequence[int]) -> Zeile:
        if isinstance(key, int):
            return self.zeilen[key]
        elif isinstance(key, Sequence):
            if len(key) % 2 == 0:
                raise TypeError("Keys must have an odd number of positions.")
            start: Sequence[Zeile] = self.zeilen
            key_iter = iter(key)
            for index, subpart in zip(key_iter, key_iter, strict=False):
                start = start[index].blocks[subpart]
            return start[key[-1]]
        raise TypeError("Unexpected key type")


@define(frozen=True)
class Geschichte:
    """Eine Geschichte ist eine einzige Sache, die dem Abenteurer passiert.
    """
    module: Sequence[Geschichtsblock] = field()
    pfad: str = ""

    @module.validator
    def _validate_module(self, _attribute, value: Sequence[Geschichtsblock]) -> None:
        """Validate that all modules' ids are unique."""
        seen = set()
        for mod in value:
            if mod.id in seen:
                raise ValueError(f"Doppelt vergebene Geschichtsmodul-Id {mod.id}")
            seen.add(mod.id)

    def block_by_id(self, name: str) -> Geschichtsblock:
        """Finde ein Modul mithilfe seiner Id."""
        for modul in self.module:
            if modul.id == name:
                return modul
        raise KeyError("Unbekanntes Modul", name)


@define(frozen=True)
class Situation:
    """Eine Situation ist eine Sammlung von Geschichten, die am selben Ort abspielen."""
    id: str
    geschichten: Sequence[Geschichte]


@define(frozen=False)
class Verteiler:
    """Der Verteiler gibt die Geschichten aus, die dem Spieler passieren."""
    _situationen: list[Situation]
    _situation: Situation
    _warteliste: PriorityQueue[tuple[int, str, str]] = Factory(PriorityQueue)
    _geschichten: dict[str, Geschichte] = Factory(dict)
    zeit: int = 1

    def __attrs_post_init__(self):
        self._update_geschichten()

    def _update_geschichten(self):
        """Update den Cache für Geschichten aus den gegebenen Situationen."""
        for situation in self._situationen:
            for geschichte in situation.geschichten:
                if geschichte.pfad:
                    self._geschichten[geschichte.pfad] = geschichte

    @classmethod
    def aus_geschichte(cls, geschichte: Geschichte) -> Self:
        """Mache einen Test-Verteiler aus einer einzigen Geschichte."""
        situation = Situation("test", [geschichte])
        return cls([situation], situation)

    def geschichte_by_id(self, name: str) -> Geschichte:
        """Hole die Geschichte mit ihrem Pfad."""
        return self._geschichten[name]

    def nächste_geschichte(self, daten: bedingung.Bedingungsdaten) -> Geschichte:
        """Hole die nächste Geschichte raus."""
        return random.choice(self._situation.geschichten)


@define
class Weltposition:
    """Eine Position in der Geschichte."""
    geschichte: Geschichte
    block: Geschichtsblock
    pos: tuple[int, ...] = (0,)
    modul_vars: 'dict[str, mänx_mod.VarTyp]' = Factory(dict)

    @staticmethod
    def start(geschichte: Geschichte) -> 'Weltposition':
        return Weltposition(geschichte, geschichte.module[0])

    def aktuelle_zeile(self) -> Zeile | None:
        """Gebe die aktuelle Zeile aus. Wenn die aktuelle Position hinter
        dem Ende ist, gebe None zurück."""
        while True:
            try:
                return self.block[self.pos]
            except IndexError:
                if len(self.pos) > 1:
                    self.pos = (*self.pos[:-3], self.pos[-3] + 1)
                else:
                    return None

    def advance(self) -> None:
        self.pos = (*self.pos[:-1], self.pos[-1] + 1)


@define
class Spielzustand(bedingung.Bedingungsdaten):
    """Modelliert das ganze Spiel, ohne Darstellung."""
    verteiler: Verteiler
    _position: Weltposition | None = None
    _mänx: None | mänx_mod.Mänx = None
    _welt: None | mänx_mod.Welt = None

    @classmethod
    def from_verteiler(cls, verteiler: Verteiler) -> Self:
        return cls(verteiler, mänx=mänx_mod.Mänx.default(), welt=mänx_mod.Welt())

    def get_mänx(self) -> mänx_mod.Mänx | None:
        return self._mänx

    def get_welt(self) -> mänx_mod.Welt | None:
        return self._welt

    def run(self, input: str) -> tuple[Sequence[OutputZeile], InputZeile]:
        """Lasse die Geschichte bis zur nächsten Entscheidung laufen."""
        self._entscheide(input)
        outputs = list[OutputZeile]()
        while True:
            if not self._position:
                self._position = Weltposition.start(self.verteiler.nächste_geschichte(self))
            zeile = self._position.aktuelle_zeile()
            if not zeile:  # Ende der Geschichte
                self._position = None
                continue
            if isinstance(zeile, OutputZeile):
                outputs.append(zeile)
            if isinstance(zeile, InputZeile):
                return outputs, zeile
            else:
                self._run_line()

    def _entscheide(self, id: str) -> None:
        """Treffe eine Entscheidung und gebe die folgende Zeile zurück.
        Wenn keine Entscheidung ansteht, nutze :py:`Spielzustand.next`.

        :raises ValueError: wenn gerade keine Entscheidung ansteht.
        """
        if not self._position:
            assert not id, "Kein Rückgabewert zum Start der Geschichte!"
            self._position = Weltposition.start(self.verteiler.nächste_geschichte(self))
            return
        zeile = self._position.aktuelle_zeile()
        if not isinstance(zeile, Entscheidung):
            raise ValueError("Keine Entscheidung steht an, kann `entscheide` nicht verwenden.")
        for i, wahl in enumerate(zeile.wahlen):
            if wahl.id == id:
                if wahl.bedingung and not self.eval_bedingung(wahl.bedingung):
                    raise KeyError(f"Entscheidung {id} ist nicht freigeschaltet.")
                break
        else:
            raise KeyError(f"Entscheidung {id} stand nicht zur Wahl.")
        self._position.pos = (*self._position.pos, i, 0)

    def _run_line(self) -> None:
        """Führe eine Zeile aus.

        :param zeile: Die Zeile zum ausführen
        :param advance: Ob nach dem Ausführen der Zeile, wenn es keinen Sprung gab, die Position
        erhöht werden soll.
        """
        assert self._position, "Kann _run_line nicht verwenden, wenn keine Position."
        zeile = self._position.aktuelle_zeile()
        assert zeile, "Kann _run_line nicht verwenden, wenn hinter der letzten Zeile."
        assert not isinstance(zeile, InputZeile), ("Kann _run_line nicht "
                                                   "verwenden, wenn auf InputZeile")
        jump = False
        if isinstance(zeile, IfElif):
            for j, (bed, _fall) in enumerate(zeile.fälle):
                if not bed or self.eval_bedingung(bed):
                    self._position.pos = (*self._position.pos, j, 0)
                    jump = True
                    break
        elif isinstance(zeile, Sprung):
            if zeile.ziel == Sonderziel.Self:
                self._position.pos = (0,)
            else:
                self._position.block = self._position.geschichte.block_by_id(zeile.ziel)
                self._position.pos = (0,)
            jump = True
        elif isinstance(zeile, geschichte.Text):
            pass
        elif isinstance(zeile, geschichte.Erhalten):
            pass  # TODO Gebe dem Mänxen Zeugs
        else:
            assert_never(zeile)
        if not jump:
            self._position.advance()

    def eval_bedingung(self, bed: Bedingung) -> bool:
        """Evaluiere eine Bedingung zum jetzigen Zustand."""
        zustand: Bedingungsobjekt = self
        return bed.test(zustand)

    def ist_variable(self, variable: str) -> bool:
        """Teste, ob eine Variable gesetzt ist."""
        if variable.startswith("."):
            if not self._welt:
                raise VarTypError("Welt ist None, kann keine Weltvariablen abfragen.")
            value = self._welt.get_variable(variable[1:], False)
        else:
            if not self._position:
                raise VarTypError("In keinem Modul, kann keine Modulvariablen abfragen.")
            value = self._position.modul_vars.get(variable, False)
        if not isinstance(value, bool):
            raise TypeError(f"Normale Variable als Flag verwendet: {variable}")
        return value

    def teste_funktion(self, func_name: str, args: Sequence[str | int | None]) -> bool:
        """Teste eine Bedingungsfunktion."""
        # Variablen auswerten, etc.
        # args = [self.prepare_arg(arg) for arg in args]
        func = bedingung.Bedingungsfunc.by_name(func_name)
        if not func:
            raise VarTypError(f"Unbekannte Regel {func_name}")
        args_parsed: list[Any] = []
        if len(args) > len(func.args):
            raise VarTypError(f"{func_name} hat {len(args)} statt {len(func.args)} Argumente. "
                              "Semikolon statt Komma?")
        args = [*args] + [None] * (len(func.args) - len(args))
        for i, (arg, (arg_t, is_opt)) in enumerate(zip(args, func.args, strict=True)):
            if is_opt and arg is None:
                args_parsed.append(None)
            elif arg is None:
                raise VarTypError(f"{func_name} hat {len(args)} statt {len(func.args)} Argumente. "
                                  "Komma statt Semikolon?")
            if arg_t in (str, int):
                if not isinstance(arg, arg_t):
                    raise VarTypError(
                        f"Das {i+1}-te Argument von {func_name} muss {arg_t.__name__} sein.")
                args_parsed.append(arg)
            else:
                raise ValueError(f"Unbekannter Argumenttyp {arg_t} für {func_name}")
        daten: bedingung.Bedingungsdaten = self
        return func.callable(daten, *args_parsed)
