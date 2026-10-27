"""Teste de idempotência do M3 (spec §10): mesmo modelo sempre → mesmo SVG.

Diagramas independentes (ids reiniciados por diagrama) e renderizações repetidas
devem produzir bytes idênticos — sempre, não só na primeira execução.
"""

import shutil

import pytest

from chen import Attribute, Composite, Diagram, Entity, Link, Owner, Relationship, WeakEntity

pytestmark = [
    pytest.mark.requires_dot,
    pytest.mark.skipif(shutil.which("dot") is None, reason="graphviz `dot` not found in PATH"),
]


class Cliente(Entity):
    cpf = Attribute(primary_key=True)
    nome = Attribute()
    telefones = Attribute(multivalued=True)
    endereco = Composite(rua=Attribute(), numero=Attribute(), cidade=Attribute())


class Pedido(Entity):
    numero = Attribute(primary_key=True)
    data_emissao = Attribute(derived=True)


class ItemPedido(WeakEntity):
    owner = Owner(Pedido)
    codigo = Attribute(partial_key=True)
    quantidade = Attribute()


class Faz(Relationship):
    cliente = Link(Cliente, "1")
    pedido = Link(Pedido, "N", total=True)
    valor_total = Attribute(derived=True)


def _diagrama() -> Diagram:
    return Diagram("Vendas", elements=[Cliente, Pedido, ItemPedido, Faz])


def test_tres_diagramas_independentes_geram_o_mesmo_svg():
    referencia = _diagrama().to_svg()

    for _ in range(3):
        assert _diagrama().to_svg() == referencia


def test_svg_de_duas_execucoes_e_byte_a_byte():
    svg_a = _diagrama().to_svg()
    svg_b = _diagrama().to_svg()

    assert svg_a.encode("utf-8") == svg_b.encode("utf-8")
