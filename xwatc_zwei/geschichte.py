"""Die einzelnen Befehle innerhalb einer Geschichte"""
from collections.abc import Sequence
from enum import Enum

from attrs import define

Bedingung = str
Item = str
Identifier = str


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


class Sonderziel(Enum):
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
    bedingung: Bedingung | None = None


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
    fälle: 'Sequence[tuple[Bedingung | None, Sequence[Zeile]]]'

    @property
    def blocks(self) -> 'Sequence[Sequence[Zeile]]':
        return [fall[1] for fall in self.fälle]


Zeile = Text | Erhalten | Entscheidung | Sprung | IfElif


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
