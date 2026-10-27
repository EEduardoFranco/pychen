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

from pychen.exceptions import ValidationError
from pychen.model.attributes import Composite
from pychen.model.entities import Entity, WeakEntity
from pychen.model.relationships import AssociativeRelationship, Owner, Relationship
from pychen.model.validate import validate_diagram

ATTRIBUTED_TO = "attributed_to"
LINK = "link"
OWNER = "owner"
ISA_CHILD = "isa_child"
ISA_SUPER = "isa_super"


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

        instances: dict[type, Entity | Relationship] = {}
        pendentes_isa: list[tuple] = []
        for entity_class in entity_classes:
            self._check_no_owner_on_strong(entity_class)
            instance = entity_class()
            instances[entity_class] = instance
            self._new_node(instance)
            self._copy_attributes(entity_class, instance)
            pendentes_isa.extend(self._build_isas(entity_class, instance, instances))
            if issubclass(entity_class, WeakEntity):
                self._build_owners(entity_class, instance, instances)

        pendentes: list[tuple] = []
        for relationship_class in relationship_classes:
            instance = relationship_class()
            instances[relationship_class] = instance  # associativa pode ser alvo de Link
            self._new_node(instance)
            self._copy_attributes(relationship_class, instance)
            pendentes.extend(self._build_links(relationship_class, instance, instances))

        # passe único de pendências (§5, fase 2): superclasse ISA e alvos de Link
        # declarados depois na lista resolvem aqui; a ordem dos ids dos diagramas
        # sem essas referências fica inalterada
        for isa_descriptor, triangulo in pendentes_isa:
            super_instance = instances.get(isa_descriptor.superclass)
            if super_instance is None:
                raise self._e08(isa_descriptor.superclass, via="ISA")
            self._new_isa_super_edge(triangulo, super_instance, isa_descriptor)

        for link, relationship in pendentes:
            target_instance = instances.get(link.target)
            if target_instance is None:
                raise self._e08(link.target)
            self._new_link_edge(relationship, target_instance, link)

    def _build_isas(self, entity_class: type, sub, instances: dict) -> list[tuple]:
        from pychen.model.isa import ISATriangle  # isolated import: evitar ciclo

        pendentes = []
        for isa_descriptor in entity_class.__chen_isas__:
            triangulo = ISATriangle(total=isa_descriptor.total, disjoint=isa_descriptor.disjoint)
            self._new_node(triangulo)
            self._new_edge(Edge(tail=sub.obj_id, head=triangulo.obj_id, kind=ISA_CHILD))
            super_instance = instances.get(isa_descriptor.superclass)
            if super_instance is None:
                pendentes.append((isa_descriptor, triangulo))
                continue
            self._new_isa_super_edge(triangulo, super_instance, isa_descriptor)
        return pendentes

    def _new_isa_super_edge(self, triangulo, super_instance, isa_descriptor) -> None:
        self._new_edge(
            Edge(
                tail=triangulo.obj_id,
                head=super_instance.obj_id,
                kind=ISA_SUPER,
                label="d" if isa_descriptor.disjoint else "o",
                total=isa_descriptor.total,
            )
        )

    def _check_no_owner_on_strong(self, entity_class: type) -> None:
        if issubclass(entity_class, WeakEntity):
            return
        if any(isinstance(value, Owner) for value in vars(entity_class).values()):
            raise ValidationError(
                "E04",
                f'"{entity_class.__name__}" is a strong entity and cannot declare Owner',
            )

    def _build_links(self, relationship_class: type, relationship, instances: dict) -> list[tuple]:
        pendentes = []
        for link in relationship_class.__chen_links__:
            target_instance = self._resolve_target(link, instances)
            if target_instance is None:
                pendentes.append((link, relationship))
                continue
            self._new_link_edge(relationship, target_instance, link)
        return pendentes

    @staticmethod
    def _resolve_target(link, instances: dict) -> Entity | Relationship | None:
        target_class = link.target
        if not issubclass(target_class, Entity | AssociativeRelationship):
            raise ValidationError(
                "E08",
                f'Link target "{target_class.__name__}" is not an Entity or '
                "AssociativeRelationship and cannot be a Link target",
            )
        return instances.get(target_class)

    def _new_link_edge(self, relationship, target_instance, link) -> None:
        self._new_edge(
            Edge(
                tail=relationship.obj_id,
                head=target_instance.obj_id,
                kind=LINK,
                label=link.cardinality,
                total=link.total,
            )
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

    @staticmethod
    def _e08(target: type, via: str = "Link/Owner") -> ValidationError:
        return ValidationError(
            "E08",
            f'entity "{target.__name__}" referenced in {via} is not in the diagram elements',
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
        from pychen.model.serialize import to_json as dump  # isolated import

        return dump(self)

    @classmethod
    def from_json(cls, data: dict) -> Diagram:
        """Reconstrói e revalida um diagrama do dump canônico (spec §9)."""
        from pychen.model.serialize import from_json as load  # isolated import

        return load(data)

    def to_svg(self) -> str:
        """Renderiza o diagrama (spec §4). Render importa lazy: camada acima do model."""
        from pychen.render.composer import render_svg  # isolated import

        return render_svg(self)

    def save(self, path: str) -> str:
        """Escreve o SVG em disco e devolve o conteúdo gravado."""
        import pathlib

        svg = self.to_svg()
        pathlib.Path(path).write_text(svg, encoding="utf-8")
        return svg
