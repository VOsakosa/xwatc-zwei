"""Lädt Scenarien."""

from os import PathLike
from attrs import define
import pyparsing as pp
import pyparsing.common as pp_common

from xwatc_zwei import verteiler
from xwatc_zwei import geschichte

ident = pp_common.identifier  # type: ignore
NoSlashRest = pp.Regex(r"[^/]*").leave_whitespace()
Header = pp.Suppress("/") + ident + pp.Suppress("/") + NoSlashRest

@define
class HeaderLine:
    name: str
    text: str

@Header.set_parse_action
def resolve_header(results: pp.ParseResults) -> HeaderLine:
    return HeaderLine(results[0], results[1].strip())


Zeile = pp.Forward()

Sprung = pp.Literal(">") + (pp.Keyword("self") | ident)

IndentedBlock = pp.IndentedBlock(Zeile)

Bedingungskopf = pp.Literal("<") + ident + pp.Suppress(">")

Entscheidungskopf = pp.Literal(":") + ident + Bedingungskopf[0,1] + pp.Suppress(":")

Entscheidung = Entscheidungskopf + IndentedBlock
Bedingung = Bedingungskopf + IndentedBlock

Text = (pp.Suppress("/") + NoSlashRest)("Text").set_parse_action(
    lambda res: geschichte.Text(res[0]))
Zeile << Text | Entscheidung | Bedingung | Sprung

Block = (Header + Zeile[...])("Block")
GeschichteBody = Block[1,...]

@Block.set_parse_action
def resolve_block(results: pp.ParseResults) -> verteiler.Geschichtsmodul:
    header, *rest = results
    assert isinstance(header, HeaderLine)
    return verteiler.Geschichtsmodul(header.name, [geschichte.Text(header.text), *rest])


def load_scenario(path: PathLike) -> verteiler.Verteiler:
    """Lade ein Szenario aus einer Datei."""
    parsed = GeschichteBody.parse_file(path, parse_all=True, encoding="utf-8")
    return verteiler.Verteiler(parsed)
    
