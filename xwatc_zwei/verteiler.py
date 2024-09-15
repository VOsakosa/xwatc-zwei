"""Die Verteiler wählen Geschichtsmodule"""
from collections.abc import Sequence
from queue import PriorityQueue
from typing import Any, Self, cast

from attrs import Factory, define, field

from xwatc_zwei import bedingung
from xwatc_zwei import mänx as mänx_mod
from xwatc_zwei.geschichte import (Bedingung, Bedingungsobjekt, Entscheidung,
                                   IfElif, Sonderziel, Sprung, VarTypError, Zeile)


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

    def nächste_geschichte(self, daten: bedingung.Bedingungsdaten) -> Geschichte:
        """Hole die nächste Geschichte raus."""


@define
class Weltposition:
    """Eine Position in der Geschichte."""
    situation: Situation
    geschichte: Geschichte
    block: Geschichtsblock
    pos: tuple[int, ...] | None = None
    modul_vars: 'dict[str, mänx_mod.VarTyp]' = Factory(dict)


@define
class Spielzustand(bedingung.Bedingungsdaten):
    """Modelliert das ganze Spiel, ohne Darstellung."""
    verteiler: Verteiler
    _position: Weltposition
    _mänx: None | mänx_mod.Mänx = None
    _welt: None | mänx_mod.Welt = None

    @classmethod
    def from_verteiler(cls, verteiler: Verteiler) -> Self:
        return cls(verteiler, position=Weltposition(),
                   mänx=mänx_mod.Mänx.default(), welt=mänx_mod.Welt())

    def get_mänx(self) -> mänx_mod.Mänx | None:
        return self._mänx

    def get_welt(self) -> mänx_mod.Welt | None:
        return self._welt

    def aktuelle_zeile(self) -> Zeile | None:
        """Gebe die aktuelle Zeile aus."""
        if self._position.pos is None:
            return None
        while True:
            try:
                zeile = self._position.block[self._position.pos]
            except IndexError:
                if len(self._position.pos) > 1:
                    self._position.pos = (*self._position.pos[:-3], self._position.pos[-3] + 1)
                else:
                    # Springe zu nächstem Modul
                    raise NotImplementedError("Kann noch nicht zu neuem Modul springen.")
            else:
                if isinstance(zeile, IfElif):
                    for j, (bed, _fall) in enumerate(zeile.fälle):
                        if not bed or self.eval_bedingung(bed):
                            self._position.pos = (*self._position.pos, j, 0)
                            break
                    else:
                        self._position.pos = (*self._position.pos[:-1], self._position.pos[-1]+1)
                else:
                    return zeile

    def next(self) -> Zeile:
        """Gehe zur nächsten Zeile.
        Wenn eine Entscheidung ansteht, nutze :py:`Spielzustand.entscheide`.

        :raises ValueError: wenn eine Entscheidung ansteht.
        """
        pos = self._position.pos
        ans = self.aktuelle_zeile()
        # Advance
        if pos is None:
            self._position.pos = (0,)
        elif isinstance(ans, Entscheidung):
            raise ValueError("Entscheidung steht an, kann `next` nicht verwenden.")
        elif isinstance(ans, Sprung):
            if ans.ziel == Sonderziel.Self:
                self._position.pos = (0,)
            else:
                self._position.block = self._position.geschichte.block_by_id(ans.ziel)
                self._position.pos = (0,)
        elif isinstance(ans, IfElif):
            raise AssertionError("aktuelle_zeile sollte nie IfElif zurückgeben")
        else:
            self._position.pos = (*pos[:-1], pos[-1] + 1)

        ans = self.aktuelle_zeile()
        assert ans, "After advance, Zeile should be set."
        return ans

    def eval_bedingung(self, bed: Bedingung) -> bool:
        """Evaluiere eine Bedingung zum jetzigen Zustand."""
        zustand: Bedingungsobjekt = self
        return bed.test(zustand)

    def ist_variable(self, variable: str) -> bool:
        """Teste, ob eine Variable gesetzt ist."""
        if variable.startswith("."):
            if not self._welt:
                raise ValueError("Welt ist None, kann keine Weltvariablen abfragen.")
            value = self._welt.get_variable(variable[1:], False)
        else:
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

    def entscheide(self, id: str) -> Zeile:
        """Treffe eine Entscheidung und gebe die folgende Zeile zurück.
        Wenn keine Entscheidung ansteht, nutze :py:`Spielzustand.next`.

        :raises ValueError: wenn gerade keine Entscheidung ansteht.
        """
        ans = self.aktuelle_zeile()
        if not self._position.pos:
            raise ValueError("Keine Entscheidung steht an, es hat nicht mal angefangen.")
        if not isinstance(ans, Entscheidung):
            raise ValueError("Keine Entscheidung steht an, kann `entscheide` nicht verwenden.")
        for i, wahl in enumerate(ans.wahlen):
            if wahl.id == id:
                if wahl.bedingung and not self.eval_bedingung(wahl.bedingung):
                    raise KeyError(f"Entscheidung {id} ist nicht freigeschaltet.")
                break
        else:
            raise KeyError(f"Entscheidung {id} stand nicht zur Wahl.")
        self._position.pos = (*self._position.pos, i, 0)
        ans = self.aktuelle_zeile()
        assert ans
        return ans
