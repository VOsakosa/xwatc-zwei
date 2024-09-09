"""The main character, his inventory etc."""

from typing import Self
from attrs import define


@define
class Mänx:
    """Der Hauptcharakter"""

    @classmethod
    def default(cls) -> Self:
        return cls()
