"""Validações semânticas do modelo (spec §6). Roda no fim de `Diagram.__init__`:
diagrama inválido nunca chega ao layout, muito menos ao SVG (erros altos, nunca silenciosos).
"""

from __future__ import annotations

from chen.exceptions import ValidationError
from chen.model.relationships import Relationship


def validate_diagram(diagram) -> None:
    from chen.model.core import Diagram  # isolated import: typing support only

    if not isinstance(diagram, Diagram):
        raise TypeError("validate_diagram expects a Diagram instance")

    for node in diagram.nodes:
        if not isinstance(node, Relationship):
            continue
        links = type(node).__chen_links__
        if len(links) < 2:
            raise ValidationError(
                "E05",
                f'Relationship "{node.name}" must connect at least 2 entities (got {len(links)})',
            )
