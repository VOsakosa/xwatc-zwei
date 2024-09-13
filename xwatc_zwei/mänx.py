"""The main character, his inventory etc."""

from typing import ClassVar, Self, TypeVar
from attrs import define, Factory

T = TypeVar("T")
VarTyp = bool | int | str

@define
class Mänx:
    """Der Hauptcharakter"""
    ATTRIBUTE: ClassVar[list[str]] = ["flink", "weise", "schlau", "stark", "wach"]
    P_WERTE: ClassVar[list[str]] = ["selbstsicher", "stabil", "gesellig"]
    _werte: dict[str, int]

    @classmethod
    def default(cls) -> Self:
        return cls({w: 10 for w in (*cls.ATTRIBUTE, *cls.P_WERTE)})
    
    def get_wert(self, name: str) -> int:
        """Attribut oder P-Wert des Mänxen holen."""
        return self._werte[name]


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
