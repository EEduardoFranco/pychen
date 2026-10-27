"""Relacionamentos e ligações (spec §5): nós losango e arestas rotuladas.

E06 (spec §6) levanta na declaração: `Link.__init__` valida a cardinalidade —
diagrama inválido nunca deve existir, muito menos gerar SVG.

`Owner` declara a ligação de uma entidade fraca ao seu dono (total, (1,1) por
definição). `Link(total=True)` marca participação total (linha dupla, §2).

Relacionamentos também podem declarar atributos (§2: atributo ligado ao losango).
"""

from __future__ import annotations

from chen.exceptions import ValidationError
from chen.model.attributes import Attribute
from chen.model.entities import display_name

VALID_CARDINALITIES = {"1", "N", "M"}


class Link:
    def __init__(self, target: type, cardinality: str, total: bool = False) -> None:
        if cardinality not in VALID_CARDINALITIES:
            raise ValidationError(
                "E06",
                f'invalid cardinality "{cardinality}"; expected one of 1, N, M',
            )
        self.target = target
        self.cardinality = cardinality
        self.total = total
        self.field_name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.field_name = name


class Owner:
    def __init__(self, target: type) -> None:
        self.target = target
        self.field_name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.field_name = name


class Relationship:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        values = vars(cls)
        cls.__chen_links__ = [value for value in values.values() if isinstance(value, Link)]
        cls.__chen_attributes__ = [
            value for value in values.values() if isinstance(value, Attribute)
        ]

    def __init__(self) -> None:
        self.name: str = display_name(type(self))
        self.obj_id: int = 0
        self.attributes: list[Attribute] = []


class AssociativeRelationship(Relationship):
    """Entidade associativa (spec §2/§5, fase 2): losango dentro de retângulo.

    Relacionamento que participa de outros relacionamentos: coleciona `Link`s
    como qualquer `Relationship`, pode declarar atributos e pode ser **alvo** de
    `Link` de outros relacionamentos. Subclasse dedicada — decisão registrada
    em §13 (2026-10-27): explícita no olhar, sem mágica de Meta.
    """
