"""Die einzelnen Befehle innerhalb einer Geschichte"""
from attrs import define

Bedingung = str
Item = str



@define(frozen=True)
class Text:
    text: str

@define
class Erhalten:
    objekt: Item
    anzahl: int = 1

Zeile = Text | Erhalten
