"""Relacionamentos e ligações (spec §5): nós losango e arestas rotuladas.

E06 (spec §6) levanta na declaração: `Link.__init__` valida a cardinalidade —
diagrama inválido nunca deve existir, muito menos gerar SVG.
"""

from __future__ import annotations

from chen.exceptions import ValidationError
from chen.model.entities import display_name

VALID_CARDINALITIES = {"1", "N", "M"}


class Link:
    def __init__(self, target: type, cardinality: str) -> None:
        if cardinality not in VALID_CARDINALITIES:
            raise ValidationError(
                "E06",
                f'invalid cardinality "{cardinality}"; expected one of 1, N, M',
            )
        self.target = target
        self.cardinality = cardinality
        self.field_name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.field_name = name


class Relationship:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls.__chen_links__ = [value for value in vars(cls).values() if isinstance(value, Link)]

    def __init__(self) -> None:
        self.name: str = display_name(type(self))
        self.obj_id: int = 0
