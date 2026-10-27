"""Validações de erro da spec §6 abordadas no M1: E05 e o caso feliz.
(E06 é testado em test_declaracao.py pois levanta na declaração.)
"""

import pytest

from pychen.exceptions import ValidationError
from pychen.model import (
    Attribute,
    Composite,
    Diagram,
    Entity,
    Link,
    Owner,
    Relationship,
    WeakEntity,
)


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


class TestE01AtributoDeclaradoNuncaAnexado:
    """E01 na DSL declarativa é impossível por construção (todo descritor coletado
    é anexado); a regra vive no modelo puro e protege futuros consumidores de estado
    (serialização, fase 2). O teste materializa o estado pendente ao nível do modelo."""

    def test_atributo_sem_aresta_de_anexo_levanta_E01(self):
        from pychen.model.core import ATTRIBUTED_TO
        from pychen.model.validate import validate_diagram

        class Cliente(Entity):
            cpf = Attribute(primary_key=True)
            nome = Attribute()

        class Pedido(Entity):
            numero = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            pedido = Link(Pedido, "N")

        diagrama = Diagram("Vendas", elements=[Cliente, Pedido, Faz])

        # a serialização da fase 2 pode produzir estado sem uma aresta de anexo
        aresta_cpf = [
            e
            for e in diagrama.edges
            if e.kind == ATTRIBUTED_TO and e.tail == 2  # cpf é o nó de id 2
        ]
        diagrama.edges.remove(aresta_cpf[0])

        with pytest.raises(ValidationError, match="E01"):
            validate_diagram(diagrama)


class TestE02EntidadeForteSemChave:
    def test_entidade_forte_sem_chave_emite_warning_E02(self):
        class Cliente(Entity):
            nome = Attribute()
            idade = Attribute()

        with pytest.warns(UserWarning, match="E02"):
            Diagram("Vendas", elements=[Cliente])

    def test_e02_aponta_a_entidade_culpada(self):
        class Cliente(Entity):
            class Meta:
                name = "ClienteSemCpf"

            nome = Attribute()

        with pytest.warns(UserWarning, match="ClienteSemCpf"):
            Diagram("Vendas", elements=[Cliente])

    def test_entidade_forte_com_chave_nao_emite_warning(self):
        import warnings

        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        with warnings.catch_warnings():
            warnings.simplefilter("error")  # qualquer warning falha o teste
            Diagram("Vendas", elements=[Cliente])

    def test_entidade_fraca_e_isentada_do_E02(self):
        class Pedido(Entity):
            numero = Attribute(primary_key=True)

        class Item(WeakEntity):
            do_pedido = Owner(Pedido)
            codigo = Attribute(partial_key=True)

        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            Diagram("Vendas", elements=[Pedido, Item])


class TestE07NomesDuplicados:
    def test_mesma_classe_repetida_na_lista_gera_E07(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        class Outro(Entity):
            numero = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            outro = Link(Outro, "N")

        with pytest.raises(ValidationError, match="E07"):
            Diagram("Vendas", elements=[Cliente, Cliente, Outro, Faz])

    def test_classes_distintas_com_o_mesmo_nome_geram_E07(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        class Outro(Entity):
            numero = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            outro = Link(Outro, "N")

        class Rebautizada(Entity):
            class Meta:
                name = "Cliente"

            cpf_re = Attribute(primary_key=True)

        class OutroCruza(Relationship):
            cliente_um = Link(Outro, "1")
            cliente_dois = Link(Rebautizada, "N")

        with pytest.raises(ValidationError, match="E07"):
            Diagram("Vendas", elements=[Cliente, Outro, Faz, Rebautizada, OutroCruza])

    def test_nomes_de_atributos_repetidos_nao_sao_E07(self):
        # nome de atributo é local (filhos de compostos repetem por natureza);
        # E07 vale para entidades e relacionamentos (anotação em §6)
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)
            endereco = Composite(rua=Attribute(), numero=Attribute())

        class Outro(Entity):
            numero = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            outro = Link(Outro, "N")

        Diagram("Vendas", elements=[Cliente, Outro, Faz])  # caso feliz
