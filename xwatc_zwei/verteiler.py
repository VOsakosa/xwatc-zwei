"""Die Verteiler wählen Geschichtsmodule"""
from collections.abc import Sequence
from typing import Any, Self
from attrs import define, field, Factory
from xwatc_zwei.geschichte import Bedingung, Entscheidung, IfElif, Sonderziel, Sprung, Zeile
from xwatc_zwei import mänx as mänx_mod


@define
class Geschichtsmodul:
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
class Verteiler:
    """Ein Verteiler hält mehrere Geschichtsmodule, die am gleichen 'Ort' sind, z.B. im Wald.
    """
    module: Sequence[Geschichtsmodul] = field()

    @module.validator
    def _validate_module(self, _attribute, value: Sequence[Geschichtsmodul]) -> None:
        """Validate that all modules' ids are unique."""
        seen = set()
        for mod in value:
            if mod.id in seen:
                raise ValueError(f"Doppelt vergebene Geschichtsmodul-Id {mod.id}")
            seen.add(mod.id)

    def modul_by_id(self, name: str) -> Geschichtsmodul:
        """Finde ein Modul mithilfe seiner Id."""
        for modul in self.module:
            if modul.id == name:
                return modul
        raise KeyError("Unbekanntes Modul", name)


@define
class Weltposition:
    """Eine Position in der Geschichte."""
    modul: Geschichtsmodul
    pos: tuple[int, ...] | None = None


@define
class Spielzustand:
    """Modelliert das ganze Spiel, ohne Darstellung."""
    verteiler: Verteiler
    _position: Weltposition
    mänx: None | mänx_mod.Mänx = None
    _variablen: dict[str, Any] = Factory(dict)

    @classmethod
    def from_verteiler(cls, verteiler: Verteiler) -> Self:
        return cls(verteiler, position=Weltposition(verteiler.module[0]),
                   mänx=mänx_mod.Mänx.default())

    def aktuelle_zeile(self) -> Zeile | None:
        """Gebe die aktuelle Zeile aus."""
        if self._position.pos is None:
            return None
        while True:
            try:
                zeile = self._position.modul[self._position.pos] 
            except KeyError:
                if len(self._position.pos) > 1:
                    self._position.pos = (*self._position.pos[:-3], self._position.pos[-2] + 1)
                else:
                    # Springe zu nächstem Modul
                    raise NotImplementedError()
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
                self._position.modul = self.verteiler.modul_by_id(ans.ziel)
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
        return False

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
