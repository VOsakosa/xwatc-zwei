"""Lädt Scenarien."""

from collections.abc import Sequence
from os import PathLike
from typing import Any

import pyparsing as pp
from attrs import define
from pyparsing import OpAssoc
from pyparsing import pyparsing_common as pp_common

from xwatc_zwei import geschichte, verteiler

ident = pp_common.identifier  # type: ignore
NoSlashRest = pp.Regex(r"[^/\n]*").leave_whitespace()
Header = pp.Suppress("/") + ident + pp.Suppress("/") + NoSlashRest


@Header.set_parse_action
def resolve_header(results: pp.ParseResults) -> list:
    return [results[0], geschichte.Text(results[1].strip())]


@define
class _BBlock:
    bed: Any
    block: pp.ParseResults

    def as_tuple(self) -> tuple[geschichte.Bedingung, list[geschichte.Zeile]]:
        return (self.bed, self.block.as_list())


Zeile = pp.Forward()

Text = (pp.Suppress("/") -
        NoSlashRest)("Text").set_parse_action(lambda res: geschichte.Text(res[0].strip()))
_Self = pp.CaselessKeyword("self").set_parse_action(lambda: geschichte.Sonderziel.Self)
Sprung = pp.Suppress(">") - (_Self | ident).set_parse_action(lambda res:
                                                             geschichte.Sprung(res[0]))
Sprung.set_name("Sprung")
Geben = (pp.Suppress("+") - ident - pp_common.integer[0, 1]).set_parse_action(
    lambda res: geschichte.Erhalten(*res))


_IndentedBlockUngrouped = pp.IndentedBlock(Zeile, grouped=False)
IndentedBlock = pp.Group(_IndentedBlockUngrouped)

FuncBedingung = ident + pp.Literal("(") - (ident | pp_common.integer) + pp.Literal(")")
Bedingung = pp.Group(pp.infix_notation(FuncBedingung | ident, [
    ('!', 1, OpAssoc.RIGHT),
    (pp.Literal(","), 2, OpAssoc.LEFT),
    (pp.Literal("|"), 2, OpAssoc.LEFT),
]) | "")
Bedingung.set_name("Bedingung")

Bedingungskopf = (pp.Suppress("<") - Bedingung + pp.Suppress(">")).set_name("Bedingungskopf")
Entscheidungskopf = pp.Suppress(":") - ident - Bedingungskopf[0, 1] - pp.Suppress(":") - NoSlashRest
Entscheidungsblock = (Entscheidungskopf + IndentedBlock).set_name("Entscheidungsblock")
Bedingungsblock = (Bedingungskopf + IndentedBlock).set_name("Bedingungsblock")
Bedingungsblock.set_parse_action(lambda toks: _BBlock(*toks))


@Entscheidungsblock.set_parse_action
def _resolve_wahlmöglichkeit(wahl: pp.ParseResults) -> geschichte.Wahlmöglichkeit:
    assert 3 <= len(wahl) <= 4
    block = wahl[-1].as_list()
    text = wahl[-2].strip()
    if len(wahl) == 4:
        bed = wahl[1]
    else:
        bed = None
    id = wahl[0]
    return geschichte.Wahlmöglichkeit(id, text, block, bed)


def resolve_block(results: pp.ParseResults) -> list:
    ans: list[geschichte.Zeile] = []
    group: list[geschichte.Zeile | _BBlock | geschichte.Wahlmöglichkeit] = []
    for line in results:
        if group and type(group[0]) == type(line):
            group.append(line)
        else:
            ans.extend(_glue_lines(group))
            group = [line]
    ans.extend(_glue_lines(group))
    return ans


def _glue_lines(lines: list) -> Sequence[geschichte.Zeile]:
    if not lines:
        return ()
    if isinstance(lines[0], _BBlock):
        return [geschichte.IfElif(fälle=[line.as_tuple() for line in lines])]
    elif isinstance(lines[0], geschichte.Wahlmöglichkeit):
        return [geschichte.Entscheidung(wahlen=lines)]
    if isinstance(lines[0], geschichte.Text):
        return [geschichte.Text(" ".join(text.text for text in lines))]
    assert isinstance(lines[0], geschichte.Zeile), lines[0]
    return lines


_IndentedBlockUngrouped.set_parse_action(resolve_block)


Zeile <<= Text | Geben | Entscheidungsblock | Bedingungsblock | Sprung
Zeile.set_name("Zeile")

Modul = (Header + Zeile[...]).set_name("Block")
GeschichteBody = Modul[1, ...]


@Modul.set_parse_action
def resolve_modul(results: pp.ParseResults) -> verteiler.Geschichtsmodul:
    header, *rest = results
    rest = resolve_block(rest)
    assert isinstance(header, str)
    return verteiler.Geschichtsmodul(header, rest)


def load_scenario(path: PathLike) -> verteiler.Verteiler:
    """Lade ein Szenario aus einer Datei."""
    parsed = GeschichteBody.parse_file(path, parse_all=True, encoding="utf-8")
    vert = verteiler.Verteiler(parsed)
    for modul in vert.module:
        geschichte.teste_block(modul.zeilen, modul.id)
    return vert
