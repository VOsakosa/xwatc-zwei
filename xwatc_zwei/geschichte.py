"""Die einzelnen Befehle innerhalb einer Geschichte"""
from collections.abc import Sequence
from enum import Enum
from typing import Protocol, assert_never

from attrs import define, field, validators

from xwatc_zwei.mänx import VarTyp


Item = str
Identifier = str


class VarTypError(RuntimeError):
    """Ein Fehler, wenn der Typ einer Variable nicht stimmt."""


class Bedingungsobjekt(Protocol):
    def ist_variable(self, variable: str) -> bool:
        """Teste, ob eine Variable gesetzt ist."""

    def teste_funktion(self, func_name: str, args: list[str | int]) -> bool:
        """Teste eine Bedingungsfunktion."""


@define
class VariablenBedingung:
    """Teste eine Variable"""
    variable: Identifier = field(validator=validators.instance_of(Identifier))

    def test(self, zustand: Bedingungsobjekt) -> bool:
        return zustand.ist_variable(self.variable)

    def __str__(self) -> str:
        return self.variable


@define
class NichtBedingung:
    bedingung: 'Bedingung'

    def test(self, zustand: Bedingungsobjekt) -> bool:
        return not self.bedingung.test(zustand)


@define
class OderBedingung:
    bedingungen: 'list[Bedingung]'

    def test(self, zustand: Bedingungsobjekt) -> bool:
        return any(bed.test(zustand) for bed in self.bedingungen)


@define
class UndBedingung:
    bedingungen: 'list[Bedingung]'

    def test(self, zustand: Bedingungsobjekt) -> bool:
        return all(bed.test(zustand) for bed in self.bedingungen)


@define
class FuncBedingung:
    func_name: str = field(validator=validators.instance_of(str))
    args: list[str | int]

    def test(self, zustand: Bedingungsobjekt) -> bool:
        return zustand.teste_funktion(self.func_name, self.args)

    def __str__(self) -> str:
        return f"{self.func_name}({', '.join(str(a) for a in self.args)})"


Bedingung = NichtBedingung | OderBedingung | UndBedingung | FuncBedingung | VariablenBedingung


@define(frozen=True)
class Text:
    """Eine Textausgabe in der Geschichte"""
    text: str

    @property
    def blocks(self) -> 'Sequence[Sequence[Zeile]]':
        return ()


@define
class Erhalten:
    """Der Hauptcharakter erhält etwas."""
    objekt: Item
    anzahl: int = 1

    @property
    def blocks(self) -> 'Sequence[Sequence[Zeile]]':
        return ()


@define
class Treffen:
    """Ein Treffen, z.B. ein Kampf"""
    typ: str
    args: Sequence[str | int]

    @property
    def blocks(self) -> 'Sequence[Sequence[Zeile]]':
        return ()


class Sonderziel(Enum):
    """Ein Spezial-Ziel für Sprünge, erstmal nur Self."""
    Self = 0


@define
class Sprung:
    """Die Geschichte wird woanders fortgesetzt. Sollte nur am Ende eines Blockes sein."""
    ziel: Identifier | Sonderziel

    @property
    def blocks(self) -> 'Sequence[Sequence[Zeile]]':
        return ()


@define
class Wahlmöglichkeit:
    """Eine von mehreren Wahlmöglichkeiten einer Entscheidung."""
    id: str
    text: str
    block: 'Sequence[Zeile]'
    bedingung: Bedingung | None = field(
        default=None, validator=validators.instance_of(None | Bedingung))  # type: ignore


@define
class Entscheidung:
    """Eine Entscheidung, die dem Spieler präsentiert wird"""
    wahlen: Sequence[Wahlmöglichkeit]

    @property
    def blocks(self) -> 'Sequence[Sequence[Zeile]]':
        return [wahl.block for wahl in self.wahlen]

    @staticmethod
    def neue_bestätigung() -> 'Entscheidung':
        return Entscheidung([Wahlmöglichkeit("", "Weiter", [])])


@define
class IfElif:
    """Eine Reihe von Fallunterscheidungen."""
    fälle: 'Sequence[tuple[Bedingung | None, Sequence[Zeile]]]' = field()

    @fälle.validator
    def _validate_fälle(self, _attrib, value):
        for bed, blocks in value:
            if not isinstance(bed, None | Bedingung):
                raise TypeError("Bedingungen in IfElif müssen None oder Bedingung sein.")

    @property
    def blocks(self) -> 'Sequence[Sequence[Zeile]]':
        return [fall[1] for fall in self.fälle]


@define
class SetzeVariable:
    """Zeile, die eine Variable setzt."""
    variable: str
    wert: VarTyp
    operator: str = "="

    def ausführen(self, locals: dict[str, VarTyp], globals: None | dict[str, VarTyp]) -> None:
        if self.variable.startswith("."):
            var = self.variable.removeprefix(".")
            if globals is None:
                return
            dct = globals
        else:
            var = self.variable
            dct = locals
        if var in dct and type(dct[var]) != type(self.wert):
            raise VarTypError(f"Variable hat Typ {type(var).__name__}, kann nicht auf "
                              f"{self.wert} gesetzt werden")
        if self.operator == "=":
            dct[var] = self.wert
        else:
            raise VarTypError(f"Unbekannter Operator: {self.operator!r}")

    @property
    def blocks(self) -> 'Sequence[Sequence[Zeile]]':
        return ()


OutputZeile = Text | Erhalten
InputZeile = Entscheidung | Treffen
FunktionsZeile = Sprung | IfElif | SetzeVariable
Zeile = OutputZeile | InputZeile | FunktionsZeile


def teste_block(block: Sequence[Zeile], name: str) -> None:
    """Teste Blöcke auf eindeutige, dumme Fehler, wie Sprünge vor Ende, oder falsche Typen."""
    # TODO Fehlende Tests: Variablen, die nicht gesetzt werden; Sprünge ins nichts
    for i, element in enumerate(block):
        if isinstance(element, Sprung) and i != len(block) - 1:
            raise ValueError(f"Sprung ist nicht letztes Element ({name})")
        elif isinstance(element, IfElif):
            for j, (bed, unterblock) in enumerate(element.fälle):
                teste_bedingung(bed, f"{name}.{i+1}{chr(0x41+j)}")
                teste_block(unterblock, f"{name}.{i+1}{chr(0x41+j)}")
                if not bed and j != len(element.fälle) - 1:
                    raise ValueError(f"Leere Bedingung {name}.{i+1}{chr(0x41+j)} "
                                     "ist nicht letztes Element")
            if len(element.fälle) == 1 and not element.fälle[0]:
                raise ValueError(f"Einzige Bedingung ist leer. ({name})")
        elif isinstance(element, Entscheidung):
            for j, wahl in enumerate(element.wahlen):
                teste_bedingung(wahl.bedingung, f"{name}.{i+1}{chr(0x41+j)}")
                teste_block(wahl.block, f"{name}.{i+1}{chr(0x41+j)}")
            if len({wahl.id for wahl in element.wahlen}) != len(element.wahlen):
                raise ValueError(f"Doppelt vergebene Wahl in {name}")
        elif not isinstance(element, Zeile):
            raise TypeError(f"{element} ist keine Zeile! ({name})")


def teste_bedingung(bedingung: Bedingung | None, name: str) -> None:
    """Teste Bedingungen auf Fehler, wie z.B. fehlende Funktionen."""
    match bedingung:
        case None:
            return
        case UndBedingung(bedingungen=bedingungen) | OderBedingung(bedingungen=bedingungen):
            for unterbedingung in bedingungen:
                teste_bedingung(unterbedingung, name)
        case NichtBedingung(bedingung=bedingung):
            teste_bedingung(bedingung, name)
        case VariablenBedingung():
            pass  # TODO Variablen-Check
        case FuncBedingung(func_name, args):
            bfunc = bedingung_mod.Bedingungsfunc.by_name(func_name)
            if bfunc is None:
                raise VarTypError(f"Bedingung {name}: Funktion {func_name} ist nicht bekannt.")
            # TODO Typ-Check?
        case _:
            assert_never(bedingung)


from xwatc_zwei import verteiler, bedingung as bedingung_mod  # noqa
