"""Golden test v1 (spec §10, M1): versão reduzida do exemplo canônico §4.

Cliente(cpf, nome) + Pedido(numero) + Faz(1, N) → SVG determinístico.
O snapshot é o registro revisado do SVG aceito; atualização só com
`--snapshot-update` e revisada no diff.

Este teste é de ponta a ponta e exige `dot` (anotação da §11.2), com skip
explícito quando o executável não está no PATH.
"""

import shutil

import pytest

from pychen import (
    ISA,
    AssociativeRelationship,
    Attribute,
    Composite,
    Diagram,
    Entity,
    Link,
    Owner,
    Relationship,
    WeakEntity,
)

pytestmark = [
    pytest.mark.requires_dot,
    pytest.mark.skipif(shutil.which("dot") is None, reason="graphviz `dot` not found in PATH"),
]


def test_golden_v1_reduzido_do_exemplo_canonico(snapshot):
    class Cliente(Entity):
        cpf = Attribute(primary_key=True)
        nome = Attribute()

    class Pedido(Entity):
        numero = Attribute(primary_key=True)

    class Faz(Relationship):
        cliente = Link(Cliente, "1")
        pedido = Link(Pedido, "N")

    diagrama = Diagram("Vendas", elements=[Cliente, Pedido, Faz])

    assert diagrama.to_svg() == snapshot


def test_golden_v2_exemplo_canonico_completo(snapshot):
    class Cliente(Entity):
        cpf = Attribute(primary_key=True)
        nome = Attribute()
        telefones = Attribute(multivalued=True)
        endereco = Composite(
            rua=Attribute(),
            numero=Attribute(),
            cidade=Attribute(),
        )

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

    diagrama = Diagram("Vendas", elements=[Cliente, Pedido, ItemPedido, Faz])

    assert diagrama.to_svg() == snapshot


def test_golden_v3_serializacao_renderiza_o_mesmo_svg_do_declarado():
    """§9, fase 2: o diagrama lido do dump canônico é o mesmo diagrama — o SVG
    dele é byte a byte o do declarado (round-trip fino, do JSON ao pixel)."""

    class Cliente(Entity):
        cpf = Attribute(primary_key=True)
        nome = Attribute()
        telefones = Attribute(multivalued=True)
        endereco = Composite(
            rua=Attribute(),
            numero=Attribute(),
            cidade=Attribute(),
        )

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

    declarado = Diagram("Vendas", elements=[Cliente, Pedido, ItemPedido, Faz])
    recarregado = Diagram.from_json(declarado.to_json())

    assert recarregado.to_svg() == declarado.to_svg()


def test_golden_v5_hierarquia_isa(snapshot):
    """Fase 2 (§10): hierarquia ISA — triângulo, disjunta/sobreposta e total."""

    class Pessoa(Entity):
        cpf = Attribute(primary_key=True)
        nome = Attribute()

    class Aluno(Entity):
        ra = Attribute()
        isa = ISA(Pessoa, total=False, disjoint=True)

    class Empregado(Entity):
        matricula = Attribute()
        isa = ISA(Pessoa, total=True, disjoint=False)

    diagrama = Diagram("Universidade", elements=[Pessoa, Aluno, Empregado])

    assert diagrama.to_svg() == snapshot


def test_golden_v4_entidade_associativa(snapshot):
    """Fase 2 (§10): entidade associativa — losango dentro de retângulo, com
    atributos próprios e participando de outro relacionamento."""

    class Cliente(Entity):
        cpf = Attribute(primary_key=True)
        nome = Attribute()

    class Produto(Entity):
        codigo = Attribute(primary_key=True)

    class VendaProduto(AssociativeRelationship):
        cliente = Link(Cliente, "1")
        produto = Link(Produto, "N")
        quantidade = Attribute()

    class Faturada(Relationship):
        venda = Link(VendaProduto, "N")
        nota = Link(Cliente, "1")

    diagrama = Diagram("Vendas", elements=[Cliente, Produto, VendaProduto, Faturada])

    assert diagrama.to_svg() == snapshot
