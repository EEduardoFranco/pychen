"""Canonical example from the spec (SPECS.md §4) — writes vendas.svg next to itself."""

from pathlib import Path

from pychen import Attribute, Composite, Diagram, Entity, Link, Owner, Relationship, WeakEntity


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
    data_emissao = Attribute(derived=True)  # dashed ellipse


class ItemPedido(WeakEntity):
    owner = Owner(Pedido)  # (1,1), total participation by definition
    codigo = Attribute(partial_key=True)
    quantidade = Attribute()


class Faz(Relationship):
    cliente = Link(Cliente, "1")
    pedido = Link(Pedido, "N", total=True)
    valor_total = Attribute(derived=True)  # relationship attribute


if __name__ == "__main__":
    saida = Path(__file__).resolve().parent / "vendas.svg"
    Diagram("Vendas", elements=[Cliente, Pedido, ItemPedido, Faz]).save(saida)
    print(f"written: {saida}")
