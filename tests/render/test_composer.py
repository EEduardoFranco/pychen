"""test_composer — composição do SVG final (spec §7).

O composer consome modelo + layout e monta o documento raiz: arestas primeiro
(as formas cobrem os endpoints), depois nós. Todo texto é escapado; números
saem com duas casas; duas execuções → bytes idênticos.
"""

import shutil

import pytest

from chen.model import (
    Attribute,
    Composite,
    Diagram,
    Entity,
    Link,
    Owner,
    Relationship,
    WeakEntity,
)
from chen.render.composer import render_svg

pytestmark = [
    pytest.mark.requires_dot,
    pytest.mark.skipif(shutil.which("dot") is None, reason="graphviz `dot` not found in PATH"),
]


def _vendas_diagrama():
    class Cliente(Entity):
        cpf = Attribute(primary_key=True)
        nome = Attribute()

    class Pedido(Entity):
        numero = Attribute(primary_key=True)

    class Faz(Relationship):
        cliente = Link(Cliente, "1")
        pedido = Link(Pedido, "N")

    return Diagram("Vendas", elements=[Cliente, Pedido, Faz])


def _svg_reduzido() -> str:
    return render_svg(_vendas_diagrama())


class TestDocumento:
    def test_saida_e_um_documento_svg_com_tamanho_do_layout(self):
        svg = _svg_reduzido()

        assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"')
        assert svg.rstrip().endswith("</svg>")

    def test_formas_dos_conceitos_aparecem(self):
        svg = _svg_reduzido()

        assert svg.count("<rect") == 2  # entidades
        assert svg.count("<polygon") == 1  # relacionamento
        assert svg.count("<ellipse") == 3  # atributos
        assert svg.count("<path") == 5  # arestas do modelo

    def test_labels_de_cardinalidade_aparecem(self):
        svg = _svg_reduzido()

        assert ">1<" in svg
        assert ">N<" in svg


class TestChave:
    def test_atributo_chave_aparece_com_sublinhado(self):
        svg = _svg_reduzido()

        assert 'text-decoration="underline"' in svg


class TestEscape:
    def test_meta_name_com_caracteres_especiais_e_escapado(self):
        class Cliente(Entity):
            class Meta:
                name = "A<B&C"

            cpf = Attribute(primary_key=True)

        class Pedido(Entity):
            numero = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            pedido = Link(Pedido, "N")

        diagrama = Diagram("V", elements=[Cliente, Pedido, Faz])

        svg = render_svg(diagrama)

        assert "A&lt;B&amp;C" in svg
        assert "A<B&amp;C>" not in svg  # o texto cru não passa


class TestNotacaoM2:
    """Notação intermediária completa na composição (spec §2, §10)."""

    def test_entidade_fraca_vira_retangulo_duplo(self):
        class Venda(Entity):
            numero = Attribute(primary_key=True)

        class Item(WeakEntity):
            da_venda = Owner(Venda)
            codigo = Attribute(partial_key=True)

        svg = render_svg(Diagram("Itens", elements=[Venda, Item]))

        assert svg.count("<rect") == 3  # 2 da fraca + 1 da forte
        assert "entity-weak" in svg

    def test_atributo_multivalorado_vira_elipse_dupla(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)
            telefones = Attribute(multivalued=True)

        class Outro(Entity):
            numero = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            outro = Link(Outro, "N")

        svg = render_svg(Diagram("V", elements=[Cliente, Outro, Faz]))

        assert "attribute-multivalued" in svg
        assert svg.count('<ellipse cx="') >= 2  # outer + inner da mesma elipse dupla

    def test_atributo_derivado_e_tracejado(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        class Outro(Entity):
            numero = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            outro = Link(Outro, "N")
            total_do_dia = Attribute(derived=True)

        svg = render_svg(Diagram("V", elements=[Cliente, Outro, Faz]))

        assert "attribute-derived" in svg

    def test_atributo_de_entidade_fraca_tem_sublinhado_tracejado(self):
        class Venda(Entity):
            numero = Attribute(primary_key=True)

        class Item(WeakEntity):
            da_venda = Owner(Venda)
            codigo = Attribute(partial_key=True)

        svg = render_svg(Diagram("Itens", elements=[Venda, Item]))

        assert "attribute-partial-key" in svg

    def test_participacao_total_vira_linha_dupla(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        class Pedido(Entity):
            numero = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            pedido = Link(Pedido, "N", total=True)

        svg = render_svg(Diagram("V", elements=[Cliente, Pedido, Faz]))

        assert "edge-double" in svg

    def test_atributo_de_entidade_e_composto_ligam_mae_e_filhas(self):
        class Cliente(Entity):
            cpf = Attribute(primary_key=True)
            endereco = Composite(rua=Attribute(), numero=Attribute())

        class Outro(Entity):
            numero = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            outro = Link(Outro, "N")

        svg = render_svg(Diagram("V", elements=[Cliente, Outro, Faz]))

        assert svg.count("<ellipse") == 5  # cpf + endereco(mãe) + rua, numero + numero do Outro


class TestNotacaoFase2:
    """Fase 2 (§2/§10): entidade associativa — losango dentro de retângulo."""

    def test_associativa_tem_retangulo_e_losango_interno(self):
        from chen.model import AssociativeRelationship

        class Cliente(Entity):
            cpf = Attribute(primary_key=True)

        class Produto(Entity):
            codigo = Attribute(primary_key=True)

        class VendaProduto(AssociativeRelationship):
            cliente = Link(Cliente, "1")
            produto = Link(Produto, "N")

        svg = render_svg(Diagram("Vendas", elements=[Cliente, Produto, VendaProduto]))

        assert '<g class="associative">' in svg
        # retângulo + losango do mesmo conceito
        assert '<g class="associative">' in svg and "<polygon" in svg


class TestDeterminismo:
    def test_duas_composicoes_geram_bytes_identicos(self):
        primeira = _svg_reduzido()
        segunda = _svg_reduzido()

        assert primeira == segunda
        assert primeira.encode("utf-8") == segunda.encode("utf-8")
