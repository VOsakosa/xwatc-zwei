"""Die Verteiler wählen Geschichtsmodule"""
from attrs import define, field
from xwatc_zwei.geschichte import Zeile


@define
class Geschichtsmodul:
    id: str
    zeilen: list[Zeile]


@define
class Verteiler:
    """"""
    module: list[Geschichtsmodul] = field(converter=list)

@define
class Weltposition:
    """"""