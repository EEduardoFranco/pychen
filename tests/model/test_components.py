"""Testes do modelo de domínio migrado do protótipo (components.py → chen/model)."""

from chen.model import Attribute, Entity, Identifier


class TestIdentifier:
    def test_ids_sao_sequenciais(self):
        idfr = Identifier()

        primeiro = idfr.get_new()
        segundo = idfr.get_new()

        assert segundo == primeiro + 1


class TestAttribute:
    def test_atributo_guarda_nome(self):
        attr = Attribute(name="nome")

        assert attr.name == "nome"

    def test_atributo_tem_id(self):
        attr = Attribute(name="cpf")

        assert isinstance(attr.obj_id, int)

    def test_is_primary_padrao_e_false(self):
        attr = Attribute(name="nome")

        assert attr.is_primary is False

    def test_is_primary_pode_ser_true(self):
        attr = Attribute(name="cpf", is_primary=True)

        assert attr.is_primary is True


class TestEntity:
    def test_entidade_guarda_nome(self):
        ent = Entity(name="Cliente")

        assert ent.name == "Cliente"

    def test_entidade_nasce_sem_atributos(self):
        ent = Entity(name="Cliente")

        assert ent.attributes == []

    def test_add_attribute_agrega_atributo(self):
        ent = Entity(name="Cliente")
        attr = Attribute(name="cpf")

        ent.add_attribute(attr)

        assert ent.attributes == [attr]
