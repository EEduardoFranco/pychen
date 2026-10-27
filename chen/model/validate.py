"""Validações semânticas do modelo (spec §6). Roda no fim de `Diagram.__init__`:
diagrama inválido nunca chega ao layout, muito menos ao SVG (erros altos, nunca silenciosos).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from chen.exceptions import ValidationError
from chen.model.entities import WeakEntity
from chen.model.relationships import Relationship

if TYPE_CHECKING:
    from chen.model.core import Diagram


def validate_diagram(diagram: Diagram) -> None:
    for node in diagram.nodes:
        if isinstance(node, Relationship):
            links = type(node).__chen_links__
            if len(links) < 2:
                raise ValidationError(
                    "E05",
                    f'Relationship "{node.name}" must connect at least 2 entities '
                    f"(got {len(links)})",
                )
        if isinstance(node, WeakEntity):
            _validate_weak(node)


def _validate_weak(weak) -> None:
    owners = type(weak).__chen_owners__
    if len(owners) != 1:
        raise ValidationError(
            "E04",
            f'weak entity "{weak.name}" must have exactly one owner (got {len(owners)})',
        )
    if not any(attribute.partial_key for attribute in weak.attributes):
        raise ValidationError(
            "E03",
            f'weak entity "{weak.name}" requires at least one partial key',
        )
