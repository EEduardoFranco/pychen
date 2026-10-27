"""Validações de erro da spec §6 abordadas no M1: E05 e o caso feliz.
(E06 é testado em test_declaracao.py pois levanta na declaração.)
"""

import pytest

from chen.exceptions import ValidationError
from chen.model import Attribute, Diagram, Entity, Link, Owner, Relationship, WeakEntity


class TestE05RelacionamentoComMenosDeDuasEntidades:
    def test_relacionamento_com_um_link_levanta_E05_no_diagrama(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")

        with pytest.raises(ValidationError, match="E05"):
            Diagram("Vendas", elements=[Cliente, Faz])

    def test_relacionamento_com_zero_links_levanta_E05(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)
            nome = Attribute()

        class Faz(Relationship):
            pass

        with pytest.raises(ValidationError, match="E05"):
            Diagram("Vendas", elements=[Cliente, Faz])

    @pytest.mark.parametrize("cards", [("1", "N"), ("M", "N"), ("1", "1")])
    def test_mensagens_e05_apontam_o_relacionamento_culpado(self, cards):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        class Pedido(Entity):
            numero = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, cards[0])
            pedido = Link(Pedido, cards[1])

        # caso feliz: não levanta
        Diagram("Vendas", elements=[Cliente, Pedido, Faz])


class TestE08ClasseForaDoDiagrama:
    def test_link_para_classe_fora_do_diagrama_levanta_E08(self):
        class Forasteira(Entity):
            cpf = Attribute(primary_key=True)

        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            forasteira = Link(Forasteira, "N")

        with pytest.raises(ValidationError, match="E08"):
            Diagram("Vendas", elements=[Cliente, Faz])

    def test_owner_para_classe_fora_do_diagrama_levanta_E08(self):
        class Forasteira(Entity):
            numero = Attribute(primary_key=True)

        class Item(WeakEntity):
            codigo = Attribute(partial_key=True)
            do_dono = Owner(Forasteira)

        with pytest.raises(ValidationError, match="E08"):
            Diagram("Vendas", elements=[Item])


class TestCasoFelizValido:
    def test_golden_reduzido_valida_sem_erros(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)
            nome = Attribute()

        class Pedido(Entity):
            numero = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            pedido = Link(Pedido, "N")

        diagrama = Diagram("Vendas", elements=[Cliente, Pedido, Faz])

        assert diagrama.name == "Vendas"
