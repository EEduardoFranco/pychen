"""Serialização canônica do modelo (spec §9, fase 2).

O JSON é o grafo semântico (nós/arestas) — nenhum estado visual entra. Ids no
JSON são **posições canônicas**, não os ids internos do modelo: nós numerados
1..N na ordem de emissão, arestas N+1.. depois, `tail`/`head` remapeados. Assim
`to_json(from_json(d)) == to_json(d)` é identidade por construção — o formato é
o declarativo por cima, o imperativo por baixo (§1.2).

Chaves omissas são defaults: `flags` só entra quando algum flag é true;
`label` só quando não nulo; `total` só quando true.
"""

from __future__ import annotations

from chen.model.attributes import Attribute, CompositeNode
from chen.model.core import (
    ATTRIBUTED_TO,
    LINK,
    OWNER,
    Diagram,
    Edge,
    Identifier,
)
from chen.model.entities import Entity, WeakEntity
from chen.model.relationships import Relationship
from chen.model.validate import validate_diagram

FORMAT_VERSION = 1
_FLAGS = ("primary_key", "multivalued", "derived", "partial_key")
_EDGE_KINDS = (ATTRIBUTED_TO, LINK, OWNER)


def to_json(diagram: Diagram) -> dict:
    positions = {node.obj_id: pos for pos, node in enumerate(diagram.nodes, start=1)}
    nodes = [_node_to_json(node, pos) for pos, node in enumerate(diagram.nodes, start=1)]
    last_node_id = len(diagram.nodes)
    edges = [
        _edge_to_json(edge, last_node_id + pos, positions)
        for pos, edge in enumerate(diagram.edges, start=1)
    ]
    return {"format": FORMAT_VERSION, "name": diagram.name, "nodes": nodes, "edges": edges}


def from_json(data: dict) -> Diagram:
    _check_format(data)
    nodes, positions = _nodes_from(data["name"], data["nodes"])
    edges = _edges_from(data["edges"], positions, len(nodes))
    _attach_attributes(nodes, edges)
    diagram = Diagram._load(data["name"], nodes, edges)
    validate_diagram(diagram)
    return diagram


# --- dump -------------------------------------------------------------------


def _node_to_json(node, obj_id: int) -> dict:
    entry: dict = {"obj_id": obj_id, "kind": node_kind(node), "name": node.name}
    flags = _flags_of(node)
    if any(flags.values()):
        entry["flags"] = flags
    return entry


def node_kind(node) -> str:
    if isinstance(node, WeakEntity):
        return "weak_entity"
    if isinstance(node, Entity):
        return "entity"
    if isinstance(node, Relationship):
        return "relationship"
    if isinstance(node, CompositeNode):
        return "composite"
    if isinstance(node, Attribute):
        return "attribute"
    raise ValueError(f'node "{node.name}" has no canonical kind')


def _flags_of(node) -> dict[str, bool]:
    if isinstance(node, Attribute):
        return {flag: bool(getattr(node, flag)) for flag in _FLAGS}
    return {}


def _edge_to_json(edge: Edge, obj_id: int, positions: dict[int, int]) -> dict:
    entry = {
        "obj_id": obj_id,
        "kind": edge.kind,
        "tail": positions[edge.tail],
        "head": positions[edge.head],
    }
    if edge.label is not None:
        entry["label"] = edge.label
    if edge.total:
        entry["total"] = True
    return entry


# --- load -------------------------------------------------------------------


def _check_format(data: dict) -> None:
    if data.get("format") != FORMAT_VERSION:
        raise ValueError(
            f"unsupported format: expected {FORMAT_VERSION}, got {data.get('format')!r}"
        )


def _nodes_from(name: str, raw_nodes: list[dict]) -> tuple[list, dict[int, int]]:
    ids = Identifier()
    nodes: list = []
    positions: dict[int, int] = {}
    for raw in raw_nodes:
        node = _node_from(raw)
        node.obj_id = ids.next()
        positions[raw["obj_id"]] = node.obj_id
        nodes.append(node)
    return nodes, positions


def _node_from(raw: dict):
    kind = raw["kind"]
    name = raw["name"]
    if kind == "entity":
        node = Entity()
        node.name = name
        return node
    if kind == "weak_entity":
        node = WeakEntity()
        node.name = name
        return node
    if kind == "relationship":
        node = Relationship()
        node.name = name
        return node
    if kind == "attribute":
        flags = raw.get("flags", {})
        node = Attribute(**{flag: bool(flags.get(flag, False)) for flag in _FLAGS})
        node.name = name
        return node
    if kind == "composite":
        return CompositeNode(name)
    raise ValueError(f'unknown node kind "{kind}"')


def _edges_from(raw_edges: list[dict], positions: dict[int, int], last_node_id: int) -> list[Edge]:
    ids = Identifier(start=last_node_id)
    edges: list[Edge] = []
    for raw in raw_edges:
        kind = raw["kind"]
        if kind not in _EDGE_KINDS:
            raise ValueError(f'unknown edge kind "{kind}"')
        edges.append(
            Edge(
                obj_id=ids.next(),
                kind=kind,
                label=raw.get("label"),
                total=bool(raw.get("total", False)),
                tail=_position_of(raw["tail"], positions),
                head=_position_of(raw["head"], positions),
            )
        )
    return edges


def _position_of(raw_id: int, positions: dict[int, int]) -> int:
    position = positions.get(raw_id)
    if position is None:
        raise ValueError(f"edge references unknown node obj_id {raw_id}")
    return position


def _attach_attributes(nodes: list, edges: list[Edge]) -> None:
    """Reconstrói as listas `attributes` dos donos a partir das arestas de anexo.

    A render usa `node.attributes`; a ordem segue a ordem das arestas no dump —
    é a mesma ordem de declaração dos descritores (§4).
    """
    por_id = {node.obj_id: node for node in nodes}
    for edge in edges:
        if edge.kind == ATTRIBUTED_TO:
            dono = por_id[edge.head]
            if hasattr(dono, "attributes"):
                dono.attributes.append(por_id[edge.tail])
