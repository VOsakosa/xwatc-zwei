"""Lädt Scenarien."""

from os import PathLike
from attrs import define
import pyparsing as pp
from pyparsing import OpAssoc, pyparsing_common as pp_common

from xwatc_zwei import verteiler
from xwatc_zwei import geschichte

ident = pp_common.identifier  # type: ignore
NoSlashRest = pp.Regex(r"[^/\n]*").leave_whitespace()
Header = pp.Suppress("/") + ident + pp.Suppress("/") + NoSlashRest


@define
class HeaderLine:
    name: str
    text: str


@Header.set_parse_action
def resolve_header(results: pp.ParseResults) -> HeaderLine:
    return HeaderLine(results[0], results[1].strip())


Zeile = pp.Forward()

Text = (pp.Suppress("/") -
        NoSlashRest)("Text").set_parse_action(lambda res: geschichte.Text(res[0]))
Sprung = pp.Literal(">") - (pp.Keyword("self") | ident)
Sprung.set_name("Sprung")
Geben = (pp.Suppress("+") - ident - pp_common.integer[0,1])


IndentedBlock = pp.IndentedBlock(Zeile)

FuncBedingung = ident + pp.Literal("(") - (ident | pp_common.integer) + pp.Literal(")")
Bedingung = pp.infix_notation(FuncBedingung | ident, [
    ('!', 1, OpAssoc.RIGHT),
    (pp.Literal(","), 2, OpAssoc.LEFT),
    (pp.Literal("|"), 2, OpAssoc.LEFT),
]) | ""
Bedingung.set_name("Bedingung")

Bedingungskopf = (pp.Literal("<") - Bedingung + pp.Suppress(">")).set_name("Bedingungskopf")

Entscheidungskopf = pp.Literal(":") - ident - Bedingungskopf[0, 1] - pp.Suppress(":") - NoSlashRest

Entscheidungsblock = (Entscheidungskopf + IndentedBlock).set_name("Entscheidungsblock")
Bedingungsblock = (Bedingungskopf + IndentedBlock).set_name("Bedingungsblock")

Entscheidung = Entscheidungsblock[1,...]
Entscheidung.set_name("Entscheidung")
Bedingungsfolge = Bedingungsblock[1,...]


Zeile <<= Text | Geben | Entscheidung | Bedingungsfolge | Sprung
Zeile.set_name("Zeile")

Block = (Header + Zeile[...]).set_name("Block")
GeschichteBody = Block[1, ...]


@Block.set_parse_action
def resolve_block(results: pp.ParseResults) -> verteiler.Geschichtsmodul:
    header, *rest = results
    assert isinstance(header, HeaderLine)
    return verteiler.Geschichtsmodul(header.name, [geschichte.Text(header.text), *rest])


def load_scenario(path: PathLike) -> verteiler.Verteiler:
    """Lade ein Szenario aus einer Datei."""
    parsed = GeschichteBody.parse_file(path, parse_all=True, encoding="utf-8")
    return verteiler.Verteiler(parsed)
