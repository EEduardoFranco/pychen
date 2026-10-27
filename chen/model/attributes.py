"""Atributos e atributos compostos (spec §5): nós elipse do grafo, declarados como
descritores de classe.

`Attribute` usa `__set_name__` para capturar o nome do campo onde foi declarado
(`cpf = Attribute(primary_key=True)`). `Composite` agrega sub-atributos: o nó mãe
anexa à entidade, as filhas anexam ao nó mãe — elipse mãe + elipses filhas (§8).

A variante de render (§8) é derivada das flags, por prioridade:
partial_key > primary_key > multivalued > derived > simple.
"""

from __future__ import annotations

VALID_VARIANTS = ("partial_key", "key", "multivalued", "derived", "simple")


class Attribute:
    def __init__(
        self,
        primary_key: bool = False,
        multivalued: bool = False,
        derived: bool = False,
        partial_key: bool = False,
    ) -> None:
        self.primary_key = primary_key
        self.multivalued = multivalued
        self.derived = derived
        self.partial_key = partial_key
        self.name: str = ""
        self.obj_id: int = 0

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    @property
    def variant(self) -> str:
        if self.partial_key:
            return "partial_key"
        if self.primary_key:
            return "key"
        if self.multivalued:
            return "multivalued"
        if self.derived:
            return "derived"
        return "simple"

    def clone(self) -> Attribute:
        """Cópia para o diagrama: o modelo instancia cópias por diagrama (spec §4)."""
        copia = Attribute(
            primary_key=self.primary_key,
            multivalued=self.multivalued,
            derived=self.derived,
            partial_key=self.partial_key,
        )
        copia.name = self.name
        return copia


class CompositeNode:
    """Nó do grafo para um atributo composto: renderiza como elipse simples (§8)."""

    variant = "simple"

    def __init__(self, name: str) -> None:
        self.name = name
        self.obj_id: int = 0
        self.attributes: list[Attribute] = []


class Composite:
    """Descritor de atributo composto: `endereco = Composite(rua=Attribute(), ...)`."""

    def __init__(self, **attributes: Attribute) -> None:
        # kwargs preserva a ordem de declaração; os nomes vêm das chaves, pois
        # sub-atributos de Composite não passam por __set_name__ (não são
        # atributos de corpo de classe).
        self.sub_attributes: list[Attribute] = []
        for name, attribute in attributes.items():
            attribute.name = name
            self.sub_attributes.append(attribute)
        self.name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def to_node(self) -> CompositeNode:
        return CompositeNode(self.name)
