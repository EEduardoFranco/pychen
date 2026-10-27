"""Entidades (spec §5): nós retângulo do grafo, declaradas em estilo Django models.

`Entity` usa `__init_subclass__` para coletar os `Attribute` do corpo da classe
em `__chen_attributes__`, na ordem de declaração. Cada subclassificação cria uma
classe-folha: a coleta usa apenas o próprio corpo (a subclasse não herda os
descritores da pai) — explicit is better than implicit.

`WeakEntity` (spec §2): retângulo duplo, exatamente um dono declarado com
`Owner(target)` — aresta total de cardinalidade (1,1) por definição — e ao
menos uma chave parcial (`partial_key=True`).
"""

from __future__ import annotations

from chen.model.attributes import Attribute, Composite


class Entity:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls.__chen_attributes__ = [
            value for value in vars(cls).values() if isinstance(value, (Attribute, Composite))
        ]

    def __init__(self) -> None:
        self.name: str = display_name(type(self))
        self.obj_id: int = 0
        self.attributes: list[Attribute] = []


def display_name(cls: type) -> str:
    """Nome de exibição: `class Meta: name = ...` sobrescreve o nome da classe (spec §4)."""
    meta = vars(cls).get("Meta")
    return getattr(meta, "name", None) or cls.__name__


class WeakEntity(Entity):
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)  # coleta os atributos como Entity
        from chen.model.relationships import Owner  # isolated import: evitar ciclo

        cls.__chen_owners__ = [value for value in vars(cls).values() if isinstance(value, Owner)]
