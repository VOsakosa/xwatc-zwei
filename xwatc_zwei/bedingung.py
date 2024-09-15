
from collections.abc import Sequence
from functools import partial
from itertools import chain
import math
from random import random
from typing import Any, Callable, Protocol, TypeVar, Union, get_type_hints

import cattrs.converters
from attrs import define

from xwatc_zwei import mänx as mänx_mod
from xwatc_zwei.geschichte import Item, VarTypError

C = TypeVar("C", bound=Callable)


class Bedingungsdaten(Protocol):
    def get_mänx(self) -> mänx_mod.Mänx | None: ...

    def assert_get_mänx(self) -> mänx_mod.Mänx:
        """Hole den Mänxen und beschwere dich, wenn er nicht da ist."""
        if mänx := self.get_mänx():
            return mänx
        raise VarTypError("Mänx-Eigenschaft gefragt, aber kein Mänx.")


@define
class Bedingungsfunc:
    """Eine Funktion, die Bedingungen auswertet."""
    args: Sequence[tuple[Any, bool]]
    callable: Callable

    @staticmethod
    def by_name(name: str) -> 'Bedingungsfunc | None':
        return _BEDINGUNGEN.get(name)


def strip_optional(opt: Any) -> tuple[Any, bool]:
    if cattrs.converters.is_union_type(opt):
        if type(None) in opt.__args__:
            return Union[tuple(arg for arg in opt.__args__ if arg is not type(None))], True
        else:
            return opt, False
    else:
        return opt, False


_BEDINGUNGEN = dict[str, Bedingungsfunc]()


def bedingung(name: str | Sequence[str] = "") -> Callable[[C], C]:
    """Markiere eine Funktion als Bedingungsfunktion."""
    def wrapper(fn: C) -> C:
        if not name:
            names: Sequence[str] = [fn.__name__.strip("_")]
        elif isinstance(name, str):
            names = [name]
        else:
            names = name
        items = [*get_type_hints(fn).items()][1:]
        hints = [strip_optional(typ) for name, typ in items if name not in "_return"]
        for name0 in names:
            _BEDINGUNGEN[name0] = Bedingungsfunc(hints, fn)
        return fn

    return wrapper


def wert_bedingung(daten: Bedingungsdaten, wert: int, attrib: str) -> bool:
    return daten.assert_get_mänx().get_wert(attrib) >= wert


for wert in chain(mänx_mod.Mänx.ATTRIBUTE, mänx_mod.Mänx.P_WERTE):
    _BEDINGUNGEN[wert] = Bedingungsfunc(
        [(int, False)], partial(wert_bedingung, attrib=wert))


@bedingung(name=["f", "fähig"])
def fähig(daten: Bedingungsdaten, fähigkeit: str, wert: None | int = None) -> bool:
    if wert is None:
        wert = 1
    elif not (1 <= wert <= 5):
        raise VarTypError("fähig: Wert muss zwischen 1 und 5 liegen.")
    return daten.assert_get_mänx().get_fähigkeit(fähigkeit) >= wert


@bedingung()
def hat(daten: Bedingungsdaten, item: str) -> bool:
    return False


@bedingung()
def wurf(daten: Bedingungsdaten, eigenschaft: str, ziel: int) -> bool:
    wert = daten.assert_get_mänx().get_wert(eigenschaft)
    log = math.log1p((wert-ziel) / ziel)
    wkeit = (log/math.log(2) + 1) / 2
    return random() < wkeit


@bedingung()
def glück(daten: Bedingungsdaten, ziel: int) -> bool:
    wkeit = ziel / 100
    return random() < wkeit


@bedingung()
def bestiarium(daten: Bedingungsdaten) -> bool:
    return False
