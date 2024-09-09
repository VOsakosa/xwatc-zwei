"""Die Verteiler wählen Geschichtsmodule"""
from collections.abc import Sequence
from typing import Any, Self
from attrs import define, field, Factory
from xwatc_zwei.geschichte import Zeile
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
    pos: tuple[int, ...]


@define
class Spielzustand:
    """Modelliert das ganze Spiel, ohne Darstellung."""
    verteiler: Verteiler
    _position: Weltposition
    mänx: None | mänx_mod.Mänx = None
    _variablen: dict[str, Any] = Factory(dict)

    @classmethod
    def from_verteiler(cls, verteiler: Verteiler) -> Self:
        return cls(verteiler, position=Weltposition(verteiler.module[0], (1,)),
                   mänx=mänx_mod.Mänx.default())

    def next(self) -> Zeile:
        return self._position.modul[self._position.pos]
