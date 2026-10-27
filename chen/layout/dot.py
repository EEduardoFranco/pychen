"""Camada layout (spec §7): modelo → DOT → `dot -Tjson` → posições.

Contrato do `-Tjson` (verificado com experimento real, Graphviz 16.1.0):
- `bb = "0,0,W,H"` — o H (4º número) é o ymax; o eixo y do graphviz cresce para
  cima, então flipamos: `y_svg = ymax - y`.
- `objects`: `name` (o id `n{obj_id}` que demos no DOT), `pos = "x,y"` (centro)
  e `width`/`height` em polegadas (×72 → px). Coordenadas já chegam em points.
- `edges`: `tail`/`head` = `_gvid` dos nós, `pos` = spline (`"x,y x,y ..."`) e
  `lp = "x,y"` — só presente quando a aresta tem `label`.

Graphviz é chamado via subprocess (spec §7): sem pygraphviz, que exige compilação.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

from chen.exceptions import DotNotFound

if TYPE_CHECKING:
    from chen.layout.dot import Layout
    from chen.model.core import Diagram, Edge


@dataclass(frozen=True)
class NodeGeom:
    """Geometria do nó em px SVG (x, y = centro)."""

    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class EdgeGeom:
    """Spline da aresta em px SVG, com posição do rótulo quando houver."""

    points: tuple[tuple[float, float], ...]
    label: str | None = None
    label_x: float = 0.0
    label_y: float = 0.0
    total: bool = False


@dataclass(frozen=True)
class Layout:
    width: float
    height: float
    nodes: dict[int, NodeGeom]
    edges: dict[tuple[int, int], list[EdgeGeom]]


def _resolve_dot() -> str | None:
    return shutil.which("dot")


def _escape(value: str) -> str:
    """Escapa o texto para dentro de uma string DOT entre aspas."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def to_dot(diagram: Diagram) -> str:
    """Modelo → texto DOT. Serve só de fonte de geometria: formas ignoradas (spec §7)."""
    lines = [f'graph "{_escape(diagram.name)}" {{']
    for node in diagram.nodes:
        lines.append(f'  n{node.obj_id} [label="{_escape(node.name)}"];')
    for edge in diagram.edges:
        if edge.label is None:
            lines.append(f"  n{edge.tail} -- n{edge.head};")
        else:
            lines.append(f'  n{edge.tail} -- n{edge.head} [label="{_escape(edge.label)}"];')
    lines.append("}")
    return "\n".join(lines) + "\n"


def compute_layout(diagram: Diagram) -> Layout:
    """Modelo → posições. Executa `dot -Tjson` e flipa o eixo Y para px SVG."""
    executable = _resolve_dot()
    if executable is None:
        raise DotNotFound(
            "graphviz executable `dot` not found in PATH; install Graphviz "
            "(https://graphviz.org/download/)"
        )

    process = subprocess.run(
        [executable, "-Tjson"],
        input=to_dot(diagram).encode("utf-8"),
        capture_output=True,
        check=True,
    )
    data = json.loads(process.stdout.decode("utf-8"))
    return _parse_json(data, _edges_by_pair(diagram.edges))


def _edges_by_pair(model_edges: list) -> dict[tuple[int, int], list[Edge]]:
    """Arestas do modelo agrupadas por par (fila de consumo na ordem do DOT)."""
    by_pair: dict[tuple[int, int], list[Edge]] = {}
    for edge in model_edges:
        by_pair.setdefault((edge.tail, edge.head), []).append(edge)
    return by_pair


def _parse_bbox(bb: str) -> tuple[float, float]:
    """`"x0,y0,x1,y1"` → (width, ymax). O ymax é o 4º número (p/ flipar o eixo y)."""
    _x0, _y0, x1, y1 = (float(value) for value in bb.split(","))
    return x1, y1


def _parse_points(value: str) -> tuple[tuple[float, float], ...]:
    points = []
    for point in value.split(" "):
        x, y = (float(coordinate) for coordinate in point.split(","))
        points.append((x, y))
    return tuple(points)


def _parse_json(data: dict, by_pair: dict[tuple[int, int], list[Edge]]) -> Layout:
    width, ymax = _parse_bbox(data["bb"])

    gvid_to_obj: dict[int, int] = {}
    nodes: dict[int, NodeGeom] = {}
    for obj in data["objects"]:
        obj_id = int(obj["name"][1:])  # name = "n{obj_id}"
        gvid_to_obj[obj["_gvid"]] = obj_id
        x, y = obj["pos"].split(",")
        nodes[obj_id] = NodeGeom(
            x=float(x),
            y=ymax - float(y),
            width=float(obj["width"]) * 72.0,
            height=float(obj["height"]) * 72.0,
        )

    edges: dict[tuple[int, int], list[EdgeGeom]] = {}
    for json_edge in data["edges"]:
        pair = (gvid_to_obj[json_edge["tail"]], gvid_to_obj[json_edge["head"]])
        model_edge = by_pair[pair].pop(0)
        points = [(x, ymax - y) for x, y in _parse_points(json_edge["pos"])]

        label_x = label_y = 0.0
        if "lp" in json_edge:
            label_x, label_y = (float(v) for v in json_edge["lp"].split(","))

        edges.setdefault(pair, []).append(
            EdgeGeom(
                points=points,
                label=model_edge.label,
                label_x=label_x,
                label_y=ymax - label_y,
                total=model_edge.total,
            )
        )

    return Layout(width=width, height=ymax, nodes=nodes, edges=edges)
