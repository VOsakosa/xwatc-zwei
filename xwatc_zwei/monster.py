from typing import ClassVar, Self, TypeVar
from attrs import define, Factory

@define
class Attacke:
    name: str
    schaden: int

@define
class Einheit:
    schnelle: int
    stärke: int
    max_lp: int
    attacken: list[Attacke]
    lp: int
    aktive_attacken: list[Attacke]

@define
class Monster:
    name: str
    schnelle: int
    stärke: int
    max_lp: int
    attacken: list[Attacke]
    def mache_einheit(self) -> Einheit:
        """ Mache eine neue Kampfeinheit mit vollen LP aus diesem Monster.

        >>> Tadd = Monster("David",5,6,50, [Attacke("Schwert", 12), Attacke("Keule", 5)])
        >>> Tadd.mache_einheit()  # doctest: +NORMALIZE_WHITESPACE
        Einheit(schnelle=5, stärke=6, max_lp=50, attacken=[Attacke(name='Schwert', schaden=12),
        Attacke(name='Keule', schaden=5)], lp=50, aktive_attacken=[Attacke(name='Schwert', schaden=12),
        Attacke(name='Keule', schaden=5)])
        """
        return Einheit(self.schnelle, self.stärke, self.max_lp, self.attacken, self.max_lp, self.attacken)





