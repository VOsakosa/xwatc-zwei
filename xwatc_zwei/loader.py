"""Lädt Scenarien."""

from os import PathLike
import pyparsing as pp

from xwatc_zwei import verteiler

def _rule() -> pp.ParserElement:
    pass


def load_scenario(path: PathLike) -> verteiler.Hauptgeschichte:
    return verteiler.Hauptgeschichte(verteiler.Geschichtsmodul("start", []), "Aspiring to...")