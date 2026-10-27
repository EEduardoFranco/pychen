"""Conceitos do modelo → fragmento + parâmetros (spec §7–§8).

Toda geometria chega do layout em px SVG (centro) e sai daqui como string
formatada com duas casas — determinismo byte a byte da seção 7 da spec.
"""

from __future__ import annotations

from chen.layout.dot import EdgeGeom, NodeGeom


def _num(value: float) -> str:
    return f"{value:.2f}"


def entity(node: NodeGeom, text: str) -> tuple[str, dict[str, str]]:
    return "Entity.svg", {
        "x": _num(node.x - node.width / 2),
        "y": _num(node.y - node.height / 2),
        "w": _num(node.width),
        "h": _num(node.height),
        "cx": _num(node.x),
        "cy": _num(node.y),
        "text": text,
    }


def relationship(node: NodeGeom, text: str) -> tuple[str, dict[str, str]]:
    left_x = _num(node.x - node.width / 2)
    right_x = _num(node.x + node.width / 2)
    top_y = _num(node.y - node.height / 2)
    bottom_y = _num(node.y + node.height / 2)
    return "Relationship.svg", {
        "points": (
            f"{left_x},{_num(node.y)} {_num(node.x)},{top_y} "
            f"{right_x},{_num(node.y)} {_num(node.x)},{bottom_y}"
        ),
        "cx": _num(node.x),
        "cy": _num(node.y),
        "text": text,
    }


def attribute(node: NodeGeom, text: str, variant: str = "simple") -> tuple[str, dict[str, str]]:
    filename = "Attribute.svg" if variant == "simple" else "Attribute_key.svg"
    return filename, {
        "x": _num(node.x),
        "y": _num(node.y),
        "rx": _num(node.width / 2),
        "ry": _num(node.height / 2),
        "text": text,
    }


def edge(edge_geom: EdgeGeom) -> list[tuple[str, dict[str, str]]]:
    d = _path_data(edge_geom.points)
    fragments = [("Edge.svg", {"d": d})]
    if edge_geom.label is not None:
        fragments.append(
            (
                "EdgeLabel.svg",
                {
                    "x": _num(edge_geom.label_x),
                    "y": _num(edge_geom.label_y),
                    "text": edge_geom.label,
                },
            )
        )
    return fragments


def _path_data(points: tuple[tuple[float, float], ...]) -> str:
    commands = [f"M {_num(points[0][0])},{_num(points[0][1])}"]
    commands += [f"L {_num(x)},{_num(y)}" for x, y in points[1:]]
    return " ".join(commands)
