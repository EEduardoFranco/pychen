"""Validações semânticas do modelo (spec §6). Roda no fim de `Diagram.__init__`:
diagrama inválido nunca chega ao layout, muito menos ao SVG (erros altos, nunca silenciosos).

E01 (invariante ao nível do modelo): todo principiante atributo/composto tem uma
aresta `attributed_to` que ora parte dele. Na DSL declarativa o estado é
impossível por construção; a checagem protege o modelo puro (serialização fase 2).

E07 vale para nomes de entidades e relacionamentos: nomes de atributo são locais
(filhos de compostos repetem-se por natureza — nota em §6).
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from chen.exceptions import ValidationError
from chen.model.attributes import Attribute, CompositeNode
from chen.model.entities import Entity, WeakEntity
from chen.model.isa import ISATriangle

if TYPE_CHECKING:
    from chen.model.core import Diagram


def validate_diagram(diagram: Diagram) -> None:
    from chen.model.core import (  # isolated import: core importa este módulo
        ATTRIBUTED_TO,
        ISA_CHILD,
        LINK,
        OWNER,
    )

    ligacoes = [edge for edge in diagram.edges if edge.kind == LINK]
    donos = [edge for edge in diagram.edges if edge.kind == OWNER]

    element_names: list[str] = []
    for node in diagram.nodes:
        if isinstance(node, Attribute | CompositeNode):
            _validate_attachment(node, diagram.edges, ATTRIBUTED_TO)
        elif isinstance(node, WeakEntity):
            element_names.append(node.name)
            _validate_weak(node, donos)
        elif isinstance(node, ISATriangle):
            # invariante "1 super, ≥ 1 sub" garantido no build (§5/§9): sem regra E*
            # e sem nome de usuário — fora da lista do E07 (anotação em §6)
            continue
        elif isinstance(node, Entity):
            element_names.append(node.name)
            _validate_strong_key(node, diagram.edges, ISA_CHILD)
            _validate_no_owner_on_strong(node, donos)
        else:
            element_names.append(node.name)
            _validate_rel_links(node, ligacoes)

    _validate_unique_names(element_names)


def _validate_attachment(node, edges, kind: str) -> None:
    attached = any(edge.tail == node.obj_id and edge.kind == kind for edge in edges)
    if not attached:
        raise ValidationError(
            "E01",
            f'attribute "{node.name}" of node type {type(node).__name__} is declared '
            "but never attached to anything",
        )


def _validate_strong_key(entity, edges, kind_isa_child: str) -> None:
    # subclasses ISA são isentas (§6): a chave é herança da classe-pai
    if any(edge.tail == entity.obj_id and edge.kind == kind_isa_child for edge in edges):
        return
    if not any(attribute.primary_key for attribute in entity.attributes):
        warnings.warn(
            f'E02: strong entity "{entity.name}" has no primary key attribute',
            UserWarning,
            stacklevel=2,
        )


def _validate_unique_names(names: list[str]) -> None:
    seen: set[str] = set()
    for name in names:
        if name in seen:
            raise ValidationError(
                "E07", f'duplicated name "{name}" among entities and relationships'
            )
        seen.add(name)


def _validate_rel_links(node, ligacoes: list) -> None:
    # lido do grafo, não das classes da DSL: o modelo carregado por JSON não
    # tem descritores de classe (decisão de §9, fase 2)
    links = [edge for edge in ligacoes if edge.tail == node.obj_id]
    if len(links) < 2:
        raise ValidationError(
            "E05",
            f'Relationship "{node.name}" must connect at least 2 entities (got {len(links)})',
        )


def _validate_weak(weak, donos: list) -> None:
    owners = [edge for edge in donos if edge.head == weak.obj_id]
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


def _validate_no_owner_on_strong(entity, donos: list) -> None:
    if any(edge.head == entity.obj_id for edge in donos):
        raise ValidationError(
            "E04",
            f'strong entity "{entity.name}" cannot be the target of Owner '
            "(weak entities own an Owner edge, strong ones never do)",
        )
