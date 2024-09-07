"""Die einzelnen Befehle innerhalb einer Geschichte"""
from attrs import define

Bedingung = str
Item = str

@define
class Attribute:
    if_: Bedingung

@define
class Text:
    attribute: Attribute
    text: str

@define
class Erhalten:
    objekt: Item
    anzahl: int = 1

Zeile = Text | Erhalten
