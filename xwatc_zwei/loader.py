"""Lädt Scenarien."""

from os import PathLike
from attrs import define
import pyparsing as pp
import pyparsing.common as pp_common

from xwatc_zwei import verteiler

ident = pp_common.identifier  # type: ignore
Header = pp.Suppress("/") + ident + pp.Suppress("/") + pp.rest_of_line

@Header.set_parse_action
def resolve_header(results: pp.ParseResults):
    return HeaderLine(results[0], results[1].strip())

@define
class HeaderLine:
    name: str
    text: str

Zeile = pp.Forward()

IndentedBlock = pp.IndentedBlock(Zeile)

Condition = pp.Literal("<") + ident + pp.Suppress(">")

Entscheidungskopf = pp.Literal(":") + ident + Condition[0,1] + pp.Suppress(":")

Entscheidung = Entscheidungskopf + IndentedBlock

Text = (pp.Suppress("/") + pp.Regex(r"[^/]*").leave_whitespace())("Text")
Zeile << Text | Entscheidung

Block = Header + Zeile[...]

def load_scenario(path: PathLike) -> verteiler.Hauptgeschichte:
    return verteiler.Hauptgeschichte(verteiler.Geschichtsmodul("start", []), "Aspiring to...")

Header.parse_string("/ja/Start")
print(Block.parse_string("""
/start/Hallo         
/Meine Kinder
""", parse_all=True))