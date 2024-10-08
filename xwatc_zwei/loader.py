"""Lädt Scenarien."""

from collections.abc import Sequence
import json
from os import PathLike
from typing import Any

import jsonschema
import pyparsing as pp
from attrs import define
from pyparsing import OpAssoc
from pyparsing import pyparsing_common as pp_common

from xwatc_zwei import LEVELS, MODULE_PATH, geschichte, verteiler

pp.ParserElement.enable_packrat()

ident = pp_common.identifier.copy().set_whitespace_chars(" \t")  # type: ignore
NoSlashRest = pp.Regex(r"[^/\n]*").leave_whitespace()
Header = (pp.Suppress("/") + ident + pp.Suppress("/").set_whitespace_chars(" ") +
          NoSlashRest + pp.LineEnd())


@Header.set_parse_action
def resolve_header(results: pp.ParseResults) -> list:
    if results[1].strip():
        return [results[0], geschichte.Text(results[1].strip())]
    return [results[0]]


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
Geben = pp.one_of("+ -") - ident + pp_common.integer[0, 1].set_whitespace_chars(" \t")("amount")
Geben.set_name("Geben")


@Geben.set_parse_action
def _geben_parse_action(res: pp.ParseResults):
    amount: int = res.get("amount", 0)
    if res[0] == "-":
        amount = -amount
    else:
        assert res[0] == "+"
    return geschichte.Erhalten(res[1], amount)


SetzeVariable = (
    pp.Combine(pp.Optional(".") + ident)
    + pp.Literal("=").set_whitespace_chars(" \t")
    + (pp.QuotedString('"', esc_char="\\").set_whitespace_chars(" \t")
       | pp_common.signed_integer.set_whitespace_chars(" \t"))
).set_name("SetzeVariable").set_parse_action(
    lambda res: geschichte.SetzeVariable(res[0], res[2], res[1]))

Kommentar = pp.Suppress(pp.Literal("#") + pp.restOfLine)


_IndentedBlockUngrouped = pp.IndentedBlock(Zeile, grouped=False)
IndentedBlock = pp.Group(_IndentedBlockUngrouped)

FuncArgs = pp.delimited_list(ident | pp_common.signed_integer)
FuncAufruf = ident + pp.Suppress("(") - FuncArgs + pp.Suppress(")")
Treffen = pp.Suppress("%") - FuncAufruf

FuncBedingung = FuncAufruf.copy().set_parse_action(
    lambda toks: geschichte.FuncBedingung(toks[0], list(toks[1:])))
VarBedingung = pp.Combine(pp.Literal(".")[0, 1] + ident).set_parse_action(
    lambda toks: geschichte.VariablenBedingung(toks[0]))

Treffen.set_name("Treffen")
Treffen.set_parse_action(lambda res: geschichte.Treffen(res[0], res[1:]))
Bedingung = pp.infix_notation(FuncBedingung | VarBedingung, [
    (pp.Suppress('!'), 1, OpAssoc.RIGHT, lambda toks: geschichte.NichtBedingung(toks[0][0])),
    (pp.Suppress(","), 2, OpAssoc.LEFT, lambda toks: geschichte.UndBedingung(toks[0].as_list())),
    (pp.Suppress("|"), 2, OpAssoc.LEFT, lambda toks: geschichte.OderBedingung(toks[0].as_list())),
]) | pp.Empty().set_parse_action(lambda: [None])
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


def resolve_block(results: Sequence | pp.ParseResults) -> list:
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

_LineEnd = pp.Suppress(pp.LineEnd() | pp.StringEnd()).set_name("Zeilenende")
_Statement = (Text | Geben | Sprung | Treffen | Kommentar | SetzeVariable) + _LineEnd
_Statement.set_name("Statement")

Zeile <<= _Statement | Entscheidungsblock | Bedingungsblock

Zeile.set_name("Zeile")

Modul = (Header + Zeile[...]).set_name("Block")
GeschichteBody = Modul[1, ...]


@Modul.set_parse_action
def resolve_modul(results: pp.ParseResults) -> verteiler.Geschichtsblock:
    header, *rest = results
    rest = resolve_block(rest)
    assert isinstance(header, str)
    return verteiler.Geschichtsblock(header, rest)


def load_geschichte(path: PathLike) -> verteiler.Geschichte:
    """Lade ein Szenario aus einer Datei."""
    path = LEVELS / path
    name = str(path.relative_to(LEVELS, walk_up=True)).removesuffix(".cfg")
    parsed = GeschichteBody.parse_file(path, parse_all=True, encoding="utf-8")
    vert = verteiler.Geschichte(parsed.as_list(), name)
    for modul in vert.module:
        geschichte.teste_block(modul.zeilen, modul.id)
    return vert


def load_verteiler(path: PathLike) -> verteiler.Verteiler:
    """Lade einen Verteiler."""
    with open(path, "r", encoding="utf-8") as read:
        data = json.load(read)
    with open(MODULE_PATH / "verteiler.schema.json", "r", encoding="utf-8") as read:
        schema = json.load(read)
    jsonschema.validate(data, schema)
    start = data["start"]
    situationen = []
    for situation in data["situationen"]:
        situationen.append(verteiler.Situation(
            situation["id"], [load_geschichte(geschichte) for geschichte in situation["module"]]))
    for sit in situationen:
        if sit.id == start:
            start_sit = sit
            break
    else:
        raise ValueError(f"Die Startsituation {start} ist nicht in der Liste der Situationen.")
    return verteiler.Verteiler(situationen, start_sit)


def parse_bedingung(bed_str: str):
    return Bedingung.parse_string(bed_str, parse_all=True)[0]
