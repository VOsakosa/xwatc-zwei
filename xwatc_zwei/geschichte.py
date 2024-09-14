"""Die einzelnen Befehle innerhalb einer Geschichte"""
from collections.abc import Sequence
from enum import Enum
from typing import Protocol

from attrs import define, field, validators


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


Zeile = Text | Erhalten | Entscheidung | Sprung | IfElif | Treffen


def teste_block(block: Sequence[Zeile], name: str) -> None:
    """Teste Blöcke auf eindeutige, dumme Fehler, wie Sprünge vor Ende, oder falsche Typen."""
    # TODO Fehlende Tests: Variablen, die nicht gesetzt werden; Sprünge ins nichts
    for i, element in enumerate(block):
        if isinstance(element, Sprung) and i != len(block) - 1:
            raise ValueError(f"Sprung ist nicht letztes Element ({name})")
        elif isinstance(element, IfElif):
            for j, (bed, unterblock) in enumerate(element.fälle):
                teste_block(unterblock, f"{name}.{i+1}{chr(0x41+j)}")
                if not bed and j != len(element.fälle) - 1:
                    raise ValueError(f"Leere Bedingung {name}.{i+1}{chr(0x41+j)} "
                                     "ist nicht letztes Element")
            if len(element.fälle) == 1 and not element.fälle[0]:
                raise ValueError(f"Einzige Bedingung ist leer. ({name})")
        elif isinstance(element, Entscheidung):
            for j, wahl in enumerate(element.wahlen):
                teste_block(wahl.block, f"{name}.{i+1}{chr(0x41+j)}")
            if len({wahl.id for wahl in element.wahlen}) != len(element.wahlen):
                raise ValueError(f"Doppelt vergebene Wahl in {name}")
        elif not isinstance(element, Zeile):
            raise TypeError(f"{element} ist keine Zeile! ({name})")


from xwatc_zwei import verteiler  # noqa
