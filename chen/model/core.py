"""Diagram (spec §4–§5): grafo puro, sem SVG e sem graphviz.

`Diagram(name, elements=[...])` recebe classes explicitamente (sem registro mágico)
e instancia cópias: reutilizar a mesma classe `Entity` em dois diagrams cria nós
novos, com ids reiniciados por diagrama. A ordem dos ids é determinística: entidades
e seus atributos na ordem da lista, depois relacionamentos, seus atributos e as
arestas de link na ordem de declaração.
"""

from __future__ import annotations

from dataclasses import dataclass

from chen.exceptions import ValidationError
from chen.model.entities import Entity
from chen.model.relationships import Relationship
from chen.model.validate import validate_diagram

ATTRIBUTED_TO = "attributed_to"
LINK = "link"


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


class Diagram:
    def __init__(self, name: str, elements: list[type]) -> None:
        self.name: str = name
        self.elements: list[type] = elements
        self.nodes: list[Entity | Relationship] = []
        self.edges: list[Edge] = []
        self._ids = Identifier()
        self._build()
        validate_diagram(self)

    def _new_node(self, node: Entity | Relationship) -> None:
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
            instance = entity_class()
            instances[entity_class] = instance
            self._new_node(instance)
            self._copy_attributes(entity_class, instance)

        for relationship_class in relationship_classes:
            instance = relationship_class()
            self._new_node(instance)
            self._copy_attributes(relationship_class, instance)
            self._build_links(relationship_class, instances)

    def _copy_attributes(self, cls: type, node: Entity | Relationship) -> None:
        descriptors = getattr(cls, "__chen_attributes__", [])
        for descriptor in descriptors:
            attribute = descriptor.clone()
            self._new_node(attribute)
            node.attributes.append(attribute)
            self._new_edge(Edge(tail=attribute.obj_id, head=node.obj_id, kind=ATTRIBUTED_TO))

    def _build_links(self, relationship_class: type, instances: dict[type, Entity]) -> None:
        relationship = self.nodes[-1]
        for link in relationship_class.__chen_links__:
            entity = instances.get(link.target)
            if entity is None:
                raise ValidationError(
                    "E08",
                    f"{relationship_class.__name__}.{link.field_name}: entity "
                    f'"{link.target.__name__}" is not in the diagram elements',
                )
            self._new_edge(
                Edge(
                    tail=relationship.obj_id,
                    head=entity.obj_id,
                    kind=LINK,
                    label=link.cardinality,
                )
            )

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
