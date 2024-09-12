"""The main character, his inventory etc."""

from typing import ClassVar, Self
from attrs import define


@define
class Mänx:
    """Der Hauptcharakter"""
    ATTRIBUTE: ClassVar[list[str]] = ["flink", "weise", "schlau", "stark"]
    P_WERTE: ClassVar[list[str]] = ["unsicher", "stabil", "gesellig"]
    werte: dict[str, int]

    @classmethod
    def default(cls) -> Self:
        return cls({w: 10 for w in (*cls.ATTRIBUTE, *cls.P_WERTE)})
    
    def get_wert(self, name: str) -> int:
        return self.werte[name]
