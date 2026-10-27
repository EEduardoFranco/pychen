"""Composer (spec §7): posições + fragmentos SVG → um documento raiz .svg.

Ordem de desenho: arestas primeiro (as formas cobrem os endpoints), depois nós
na ordem existente no modelo. Números com duas casas; texto escapado no loader.
"""

from __future__ import annotations

from pychen.layout.dot import compute_layout
from pychen.model.attributes import Attribute, CompositeNode
from pychen.model.entities import WeakEntity
from pychen.model.isa import ISATriangle
from pychen.model.relationships import AssociativeRelationship, Relationship
from pychen.render.shapes import (
    associative,
    attribute,
    edge,
    entity,
    isa_triangle,
    relationship,
    weak_entity,
)
from pychen.render.template_loader import Template


def render_svg(diagram) -> str:
    """Modelo + layout → SVG final (renderização completa, spec §7)."""
    layout = compute_layout(diagram)
    templates: dict[str, Template] = {}

    def rendered(name: str, parameters: dict[str, str]) -> str:
        template = templates.setdefault(name, Template(name))
        if not template.content:
            template.load()
        return template.render(parameters)

    segments: list[str] = [_document_header(layout.width, layout.height)]

    for pair_edges in layout.edges.values():
        for edge_geom in pair_edges:
            for name, parameters in edge(edge_geom):
                segments.append(rendered(name, parameters))

    for node in diagram.nodes:
        geometry = layout.nodes[node.obj_id]
        if isinstance(node, ISATriangle):
            name, parameters = isa_triangle(geometry)
        elif isinstance(node, WeakEntity):
            name, parameters = weak_entity(geometry, node.name)
        elif isinstance(node, AssociativeRelationship):
            name, parameters = associative(geometry, node.name)
        elif isinstance(node, Relationship):
            name, parameters = relationship(geometry, node.name)
        elif isinstance(node, (Attribute, CompositeNode)):
            name, parameters = attribute(geometry, node.name, variant=node.variant)
        else:
            name, parameters = entity(geometry, node.name)
        segments.append(rendered(name, parameters))

    segments.append("</svg>")
    return "\n".join(segments) + "\n"


def _document_header(width: float, height: float) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width:.2f}" height="{height:.2f}" '
        f'viewBox="0 0 {width:.2f} {height:.2f}">'
    )
