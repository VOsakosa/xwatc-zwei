"""Die Verteiler wählen Geschichtsmodule"""
from attrs import define
from xwatc_zwei.geschichte import Zeile


@define
class Geschichtsmodul:
    id: str
    zeilen: list[Zeile]


@define
class Verteiler:
    """"""
    module: list[Geschichtsmodul]


@define
class Hauptgeschichte:
    """"""
    start: Geschichtsmodul
    name: str