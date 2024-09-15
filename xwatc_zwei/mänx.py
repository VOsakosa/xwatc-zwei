"""The main character, his inventory etc."""

from typing import ClassVar, Self, TypeVar
from attrs import define, Factory

T = TypeVar("T")
VarTyp = bool | int | str


@define
class Mänx:
    """Der Hauptcharakter"""
    ATTRIBUTE: ClassVar[list[str]] = ["flink", "weise", "schlau", "stark", "wach"]
    P_WERTE: ClassVar[list[str]] = ["selbstsicher", "stabil", "gesellig", "naturliebend"]
    _werte: dict[str, int]
    _fähigkeiten: dict[str, int] = Factory(dict)

    @classmethod
    def default(cls) -> Self:
        return cls({w: 10 for w in (*cls.ATTRIBUTE, *cls.P_WERTE)})

    def get_wert(self, name: str) -> int:
        """Attribut oder P-Wert des Mänxen holen."""
        return self._werte[name]

    def set_fähigkeit(self, fähigkeit: str, stufe: int) -> None:
        """Setze eine Fähigkeit auf eine feste Stufe."""
        if not 0 <= stufe <= 5:
            raise ValueError("Fähigkeiten müssen zwischen 0 und 5 sein.")
        self._fähigkeiten[fähigkeit] = stufe

    def get_fähigkeit(self, fähigkeit: str) -> int:
        """Fähigkeitsstufe."""
        return self._fähigkeiten.get(fähigkeit, 0)


@define
class Welt:
    """Die Weltvariablen."""
    _variablen: dict[str, VarTyp] = Factory(dict)

    def setze_variable(self, variable: str, wert: VarTyp) -> VarTyp | None:
        ans = self._variablen.get(variable)
        self._variablen[variable] = wert
        return ans

    def get_variable(self, variable: str, default: T) -> VarTyp | T:
        return self._variablen.get(variable, default)
