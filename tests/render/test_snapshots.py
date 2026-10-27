"""Snapshots de SVG por variante de forma (spec §10, M2).

Um teste por conceito — uma falha de regressão aparece no diff do snapshot
revisando-se o arquivo `.ambr`. Aqui não há layout: os testes cobrem shapes +
templates puros (não exigem `dot`).
"""

from chen.layout.dot import EdgeGeom, NodeGeom
from chen.render.shapes import (
    attribute,
    edge,
    entity,
    relationship,
    weak_entity,
)
from chen.render.template_loader import Template


def _render(fragment, parameters) -> str:
    template = Template(fragment)
    template.load()
    return template.render(parameters)


def test_snapshot_fragmento_entity(snapshot):
    _, params = entity(NodeGeom(x=50.0, y=40.0, width=80.0, height=20.0), "Cliente")

    assert _render("Entity.svg", params) == snapshot


def test_snapshot_fragmento_weak_entity(snapshot):
    _, params = weak_entity(NodeGeom(x=50.0, y=40.0, width=80.0, height=20.0), "ItemPedido")

    assert _render("WeakEntity.svg", params) == snapshot


def test_snapshot_fragmento_relationship(snapshot):
    _, params = relationship(NodeGeom(x=50.0, y=40.0, width=60.0, height=30.0), "Faz")

    assert _render("Relationship.svg", params) == snapshot


def test_snapshot_fragmento_attribute_simple(snapshot):
    _, params = attribute(
        NodeGeom(x=20.0, y=10.0, width=30.0, height=12.0), "nome", variant="simple"
    )

    assert _render("Attribute.svg", params) == snapshot


def test_snapshot_fragmento_attribute_key(snapshot):
    _, params = attribute(NodeGeom(x=20.0, y=10.0, width=30.0, height=12.0), "cpf", variant="key")

    assert _render("Attribute_key.svg", params) == snapshot


def test_snapshot_fragmento_attribute_partial_key(snapshot):
    _, params = attribute(
        NodeGeom(x=20.0, y=10.0, width=30.0, height=12.0), "codigo", variant="partial_key"
    )

    assert _render("Attribute_partial_key.svg", params) == snapshot


def test_snapshot_fragmento_attribute_multivalued(snapshot):
    _, params = attribute(
        NodeGeom(x=20.0, y=10.0, width=30.0, height=12.0), "telefones", variant="multivalued"
    )

    assert _render("Attribute_multivalued.svg", params) == snapshot


def test_snapshot_fragmento_attribute_derived(snapshot):
    _, params = attribute(
        NodeGeom(x=20.0, y=10.0, width=30.0, height=12.0), "total", variant="derived"
    )

    assert _render("Attribute_derived.svg", params) == snapshot


def test_snapshot_fragmento_edge(snapshot):
    [(_, params)] = edge(EdgeGeom(points=((0.0, 0.0), (10.0, 10.5))))

    assert _render("Edge.svg", params) == snapshot


def test_snapshot_fragmento_edge_double(snapshot):
    (_, params) = edge(EdgeGeom(points=((0.0, 0.0), (10.0, 10.5)), total=True))[0]

    assert _render("EdgeDouble.svg", params) == snapshot


def test_snapshot_fragmento_edge_label(snapshot):
    [_, (_, params)] = edge(
        EdgeGeom(points=((0.0, 0.0), (10.0, 10.0)), label="N", label_x=5.0, label_y=2.5)
    )

    assert _render("EdgeLabel.svg", params) == snapshot
