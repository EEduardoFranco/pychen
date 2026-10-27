"""Hierarquia ISA (spec §2/§5, fase 2): triângulo, total/parcial, disjunta/sobreposta.

`ISA(SuperClass, total=..., disjoint=...)` é descritor, no corpo da `Entity` filha.
Um descritor por subclasse → um triângulo (`ISATriangle`): aresta `isa_child`
subclasse→triângulo e `isa_super` triângulo→superclasse com rótulo `d`/`o`;
subclasse **total** marca linha dupla até a superclasse. Classe forte em
hierarquia ISA é isenta do E02 (a chave é herança da classe-pai, §6).
"""

import warnings

import pytest

from pychen.exceptions import ValidationError
from pychen.model import (
    ISA,  # noqa: F401 — exposto pela API pública no caminho feliz
    Attribute,
    Diagram,
    Entity,
    Link,
    Relationship,
)


def _universidade():
    class Pessoa(Entity):
        cpf = Attribute(primary_key=True)
        nome = Attribute()

    class Aluno(Entity):
        ra = Attribute()
        isa = ISA(Pessoa, total=False, disjoint=True)

    class Empregado(Entity):
        matricula = Attribute()
        isa = ISA(Pessoa, total=True, disjoint=False)

    return Pessoa, Aluno, Empregado


class TestDeclaracao:
    def test_descritor_cria_triângulo_com_uma_aresta_child_e_uma_super(self):
        from pychen.model import ISATriangle

        Pessoa, Aluno, Empregado = _universidade()
        diagrama = Diagram("U", elements=[Pessoa, Aluno, Empregado])

        triangulos = [n for n in diagrama.nodes if isinstance(n, ISATriangle)]
        assert len(triangulos) == 2  # um por subclasse (decisão §5/§13)

        aluno = [n for n in diagrama.nodes if n.name == "Aluno"][0]
        triangulo_aluno = [
            t
            for t in triangulos
            if any(
                e.tail == aluno.obj_id and e.kind == "isa_child"
                for e in diagrama.edges
                if e.head == t.obj_id
            )
        ]
        assert len(triangulo_aluno) == 1

    def test_aresta_super_liga_o_triangulo_a_superclasse_com_rotulo(self):
        Pessoa, Aluno, Empregado = _universidade()
        diagrama = Diagram("U", elements=[Pessoa, Aluno, Empregado])

        pessoa = [n for n in diagrama.nodes if n.name == "Pessoa"][0]
        supers = [e for e in diagrama.edges if e.kind == "isa_super" and e.head == pessoa.obj_id]
        rotulos = {e.label for e in supers}

        assert len(supers) == 2
        assert rotulos == {"d", "o"}  # disjunta e sobreposta, respectivamente

    def test_subclasse_total_marca_linha_dupla_ate_a_superclasse(self):
        Pessoa, Aluno, Empregado = _universidade()
        diagrama = Diagram("U", elements=[Pessoa, Aluno, Empregado])

        empsupers = [e for e in diagrama.edges if e.kind == "isa_super" and e.total is True]
        assert len(empsupers) == 1  # Empregado é total; Aluno não

    def test_triângulo_tem_exatamente_uma_child_e_uma_super(self):
        from pychen.model import ISATriangle

        Pessoa, Aluno, Empregado = _universidade()
        diagrama = Diagram("U", elements=[Pessoa, Aluno, Empregado])

        for triangulo in (n for n in diagrama.nodes if isinstance(n, ISATriangle)):
            children = [
                e for e in diagrama.edges if e.kind == "isa_child" and e.head == triangulo.obj_id
            ]
            supers = [
                e for e in diagrama.edges if e.kind == "isa_super" and e.tail == triangulo.obj_id
            ]
            assert len(children) == 1
            assert len(supers) == 1


class TestE02Isenta:
    def test_subclasse_isa_sem_chave_propria_nao_emite_E02(self):
        Pessoa, Aluno, Empregado = _universidade()

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            Diagram("U", elements=[Pessoa, Aluno, Empregado])

    def test_entidade_isa_se_ocupa_como_alvo_de_link(self):
        Pessoa, Aluno, Empregado = _universidade()

        class Enrola(Relationship):
            aluno = Link(Aluno, "N")
            emp = Link(Empregado, "1")

        diagrama = Diagram("U", elements=[Pessoa, Aluno, Empregado, Enrola])

        alvinho = [n for n in diagrama.nodes if n.name == "Aluno"][0]
        assert any(e.kind == "link" and e.head == alvinho.obj_id for e in diagrama.edges)


class TestE08Superclasse:
    def test_superclasse_fora_do_diagrama_e_E08(self):
        class Pessoa(Entity):
            cpf = Attribute(primary_key=True)

        class Aluno(Entity):
            ra = Attribute()
            isa = ISA(Pessoa, total=False, disjoint=False)

        with pytest.raises(ValidationError, match="E08"):
            Diagram("U", elements=[Aluno])  # Pessoa fora da lista

    def test_superclasse_declarada_depois_na_lista_resolve(self):
        class Pessoa(Entity):
            cpf = Attribute(primary_key=True)

        class Aluno(Entity):
            ra = Attribute()
            isa = ISA(Pessoa, total=False, disjoint=False)

        diagrama = Diagram("U", elements=[Aluno, Pessoa])  # sub antes da super

        supers = [e for e in diagrama.edges if e.kind == "isa_super"]
        assert len(supers) == 1
        pessoa = [n for n in diagrama.nodes if n.name == "Pessoa"][0]
        assert supers[0].head == pessoa.obj_id
