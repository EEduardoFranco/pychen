"""Declaração declarativa (spec §4): coleta de descritores por `__init_subclass__`.

Regras testadas aqui:
- `Entity` coleta os `Attribute` declarados no corpo da classe, em ordem de declaração.
- `Relationship` coleta os `Link`.
- Nome de exibição vem do nome da classe; `class Meta: name = ...` sobrescreve.
- E06: cardinalidade fora de {1, N, M} levanta na declaração.
"""

import pytest

from pychen.exceptions import ValidationError
from pychen.model import Attribute, Entity, Link, Relationship


class TestColetaDeAtributos:
    def test_entidade_coleta_atributos_em_ordem_de_declaracao(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)
            nome = Attribute()

        assert [a.name for a in Cliente.__chen_attributes__] == ["cpf", "nome"]

    def test_atributo_sabe_se_e_chave(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)
            nome = Attribute()

        por_nome = {a.name: a for a in Cliente.__chen_attributes__}

        assert por_nome["cpf"].primary_key is True
        assert por_nome["nome"].primary_key is False

    def test_subclasse_nao_reaproveita_atributos_da_pai(self):
        class Base(Entity):
            id_ = Attribute(primary_key=True)

        class Pessoa(Base):
            nome = Attribute()

        assert [a.name for a in Pessoa.__chen_attributes__] == ["nome"]


class TestNomeDeExibicao:
    def test_nome_padrao_e_o_da_classe(self):
        class Cliente(Entity):
            pass

        assert Cliente().name == "Cliente"

    def test_meta_sobrescreve_o_nome(self):
        class Cliente(Entity):
            class Meta:
                name = "ClientePJ"

        assert Cliente().name == "ClientePJ"


class TestColetaDeLinks:
    def test_relacionamento_coleta_links_em_ordem_de_declaracao(self):
        class Cliente(Entity):
            pass

        class Pedido(Entity):
            pass

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            pedido = Link(Pedido, "N")

        assert [lk.field_name for lk in Faz.__chen_links__] == ["cliente", "pedido"]

    def test_link_guarda_cardinalidade_e_alvo(self):
        class Cliente(Entity):
            pass

        link = Link(Cliente, "N")

        assert link.cardinality == "N"
        assert link.target is Cliente


class TestE06CardinalidadeInvalidaNaDeclaracao:
    def test_cardinalidade_invalida_raise_na_declaracao_com_E06(self):
        with pytest.raises(ValidationError, match="E06"):
            Link(object, "2")

    def test_mensagem_e06_aponta_a_cardinalidade_culpada(self):
        with pytest.raises(ValidationError, match='"2"'):
            Link(object, "2")

    @pytest.mark.parametrize("valida", ["1", "N", "M"])
    def test_cardinalidades_validas_nao_levanta(self, valida):
        Link(object, valida)  # não deve levantar
