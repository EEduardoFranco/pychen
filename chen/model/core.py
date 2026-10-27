"""Diagram (spec §4–§5): grafo puro, sem SVG e sem graphviz.

`Diagram(name, elements=[...])` recebe classes explicitamente (sem registro mágico)
e instancia cópias: reutilizar a mesma classe `Entity` em dois diagramas cria nós
novos, com ids reiniciados por diagrama. A ordem dos ids é determinística: entidades
e seus atributos na ordem da lista, depois relacionamentos, seus atributos e as
arestas de link na ordem de declaração.

Arestas: `attributed_to` (atributo → entidade | relacionamento | composto),
`link` (relacionamento → entidade, com cardinalidade e participação total) e
`owner` (dono → fraco: total, (1,1) por definição).
"""

from __future__ import annotations

from dataclasses import dataclass

from chen.exceptions import ValidationError
from chen.model.attributes import Composite
from chen.model.entities import Entity, WeakEntity
from chen.model.relationships import Owner, Relationship
from chen.model.validate import validate_diagram

ATTRIBUTED_TO = "attributed_to"
LINK = "link"
OWNER = "owner"


class Identifier:
    """Contador sequencial dentro de um diagrama — nada de contador global de módulo."""

    def __init__(self, start: int = 0) -> None:
        self.last_id = start

    def next(self) -> int:
        self.last_id += 1
        return self.last_id


@dataclass
class Edge:
    obj_id: int = 0
    tail: int = 0
    head: int = 0
    kind: str = ""
    label: str | None = None
    total: bool = False


class Diagram:
    def __init__(self, name: str, elements: list[type]) -> None:
        self.name: str = name
        self.elements: list[type] = elements
        self.nodes: list[Entity | Relationship] = []
        self.edges: list[Edge] = []
        self._ids = Identifier()
        self._build()
        validate_diagram(self)

    def _new_node(self, node) -> None:
        node.obj_id = self._ids.next()
        self.nodes.append(node)

    def _new_edge(self, edge: Edge) -> None:
        edge.obj_id = self._ids.next()
        self.edges.append(edge)

    def _build(self) -> None:
        entity_classes = [e for e in self.elements if issubclass(e, Entity)]
        relationship_classes = [e for e in self.elements if issubclass(e, Relationship)]

        instances: dict[type, Entity] = {}
        for entity_class in entity_classes:
            self._check_no_owner_on_strong(entity_class)
            instance = entity_class()
            instances[entity_class] = instance
            self._new_node(instance)
            self._copy_attributes(entity_class, instance)
            if issubclass(entity_class, WeakEntity):
                self._build_owners(entity_class, instance, instances)

        for relationship_class in relationship_classes:
            instance = relationship_class()
            self._new_node(instance)
            self._copy_attributes(relationship_class, instance)
            self._build_links(relationship_class, instance, instances)

    def _check_no_owner_on_strong(self, entity_class: type) -> None:
        if issubclass(entity_class, WeakEntity):
            return
        if any(isinstance(value, Owner) for value in vars(entity_class).values()):
            raise ValidationError(
                "E04",
                f'"{entity_class.__name__}" is a strong entity and cannot declare Owner',
            )

    def _build_owners(self, entity_class: type, weak, instances: dict[type, Entity]) -> None:
        for owner_descriptor in entity_class.__chen_owners__:
            owner_instance = instances.get(owner_descriptor.target)
            if owner_instance is None:
                raise self._e08(owner_descriptor.target)
            self._new_edge(
                Edge(
                    tail=owner_instance.obj_id,
                    head=weak.obj_id,
                    kind=OWNER,
                    label="1,1",
                    total=True,
                )
            )

    def _copy_attributes(self, cls: type, node) -> None:
        for descriptor in getattr(cls, "__chen_attributes__", []):
            if isinstance(descriptor, Composite):
                self._build_composite(descriptor, node)
                continue
            attribute = descriptor.clone()
            self._new_node(attribute)
            node.attributes.append(attribute)
            self._new_edge(Edge(tail=attribute.obj_id, head=node.obj_id, kind=ATTRIBUTED_TO))

    def _build_composite(self, descriptor: Composite, node) -> None:
        composite = descriptor.to_node()
        self._new_node(composite)
        node.attributes.append(composite)
        self._new_edge(Edge(tail=composite.obj_id, head=node.obj_id, kind=ATTRIBUTED_TO))
        for sub_descriptor in descriptor.sub_attributes:
            attribute = sub_descriptor.clone()
            self._new_node(attribute)
            composite.attributes.append(attribute)
            self._new_edge(Edge(tail=attribute.obj_id, head=composite.obj_id, kind=ATTRIBUTED_TO))

    def _build_links(
        self, relationship_class: type, relationship, instances: dict[type, Entity]
    ) -> None:
        for link in relationship_class.__chen_links__:
            entity = instances.get(link.target)
            if entity is None:
                raise self._e08(link.target)
            self._new_edge(
                Edge(
                    tail=relationship.obj_id,
                    head=entity.obj_id,
                    kind=LINK,
                    label=link.cardinality,
                    total=link.total,
                )
            )

    @staticmethod
    def _e08(target: type) -> ValidationError:
        return ValidationError(
            "E08",
            f'entity "{target.__name__}" referenced in Link/Owner is not in the diagram elements',
        )

    @classmethod
    def _load(cls, name: str, nodes: list, edges: list[Edge]) -> Diagram:
        """Construção imperativa usada pela serialização (spec §9).

        Recebe o estado pronto (nós com attributes já anexados, edges com ids
        atribuídos) e pula `__init__`/`_build` — o formato declarativo por cima,
        o imperativo por baixo (§1.2).
        """
        self = cls.__new__(cls)
        self.name = name
        self.elements = []
        self.nodes = nodes
        self.edges = edges
        self._ids = Identifier()
        return self

    def to_json(self) -> dict:
        """Serialização canônica do modelo (spec §9). Módulo lazy: core é o grafo puro."""
        from chen.model.serialize import to_json as dump  # isolated import

        return dump(self)

    @classmethod
    def from_json(cls, data: dict) -> Diagram:
        """Reconstrói e revalida um diagrama do dump canônico (spec §9)."""
        from chen.model.serialize import from_json as load  # isolated import

        return load(data)

    def to_svg(self) -> str:
        """Renderiza o diagrama (spec §4). Render importa lazy: camada acima do model."""
        from chen.render.composer import render_svg  # isolated import

        return render_svg(self)

    def save(self, path: str) -> str:
        """Escreve o SVG em disco e devolve o conteúdo gravado."""
        import pathlib

        svg = self.to_svg()
        pathlib.Path(path).write_text(svg, encoding="utf-8")
        return svg
