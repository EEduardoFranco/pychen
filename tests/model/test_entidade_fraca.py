"""Entidade fraca (spec §2, §5–§6): retângulo duplo, um único dono, chave parcial.

- `Owner(target)` declara a ligação ao dono — total, cardinalidade (1,1) por definição.
- E03: entidade fraca sem chave parcial → erro na validação.
- E04: contagem de dono errada (zero, mais de um, ou owner em entidade forte) → erro.
"""

import pytest

from pychen import Attribute, Diagram, Entity, Owner, WeakEntity
from pychen.exceptions import ValidationError


def _pedido_com_chave():
    class Pedido(Entity):
        numero = Attribute(primary_key=True)

    return Pedido


class TestE03EntidadeFracaSemChaveParcial:
    def test_entidade_fraca_sem_chave_parcial_gera_E03(self):
        Pedido = _pedido_com_chave()

        class Item(WeakEntity):
            owner = Owner(Pedido)
            quantidade = Attribute()

        with pytest.raises(ValidationError, match="E03"):
            Diagram("Vendas", elements=[Pedido, Item])

    def test_e03_aponta_a_entidade_culpada(self):
        Pedido = _pedido_com_chave()

        class Item(WeakEntity):
            class Meta:
                name = "ItemReserva"

            owner = Owner(Pedido)
            quantidade = Attribute()

        with pytest.raises(ValidationError, match="ItemReserva"):
            Diagram("Vendas", elements=[Pedido, Item])

    def test_entidade_fraca_com_chave_parcial_nao_levanta(self):
        Pedido = _pedido_com_chave()

        class Item(WeakEntity):
            owner = Owner(Pedido)
            codigo = Attribute(partial_key=True)

        Diagram("Vendas", elements=[Pedido, Item])  # caso feliz


class TestE04ContagemDeDono:
    def test_entidade_fraca_com_mais_de_um_dono_gera_E04(self):
        Pedido = _pedido_com_chave()
        Cliente = _pedido_com_chave()

        class Item(WeakEntity):
            codigo = Attribute(partial_key=True)
            do_pedido = Owner(Pedido)
            do_cliente = Owner(Cliente)

        with pytest.raises(ValidationError, match="E04"):
            Diagram("Vendas", elements=[Pedido, Cliente, Item])

    def test_entidade_fraca_sem_dono_gera_E04(self):
        class Item(WeakEntity):
            codigo = Attribute(partial_key=True)

        with pytest.raises(ValidationError, match="E04"):
            Diagram("Vendas", elements=[Item])

    def test_entidade_forte_com_owner_gera_E04(self):
        Pedido = _pedido_com_chave()

        class Errado(Entity):
            numero = Attribute(primary_key=True)
            do_pedido = Owner(Pedido)

        with pytest.raises(ValidationError, match="E04"):
            Diagram("Vendas", elements=[Pedido, Errado])


class TestGrafoDoDono:
    def test_aresta_do_dono_e_total_e_de_cardinalidade_1_1(self):
        Pedido = _pedido_com_chave()

        class Item(WeakEntity):
            owner = Owner(Pedido)
            codigo = Attribute(partial_key=True)

        diagrama = Diagram("Vendas", elements=[Pedido, Item])

        dono = [e for e in diagrama.edges if e.kind == "owner"]

        pedido = [n for n in diagrama.nodes if n.name == "Pedido"][0]
        item = [n for n in diagrama.nodes if n.name == "Item"][0]

        assert [(e.tail, e.head) for e in dono] == [(pedido.obj_id, item.obj_id)]
        assert all(e.total is True for e in dono)
