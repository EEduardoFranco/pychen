"""test_composer — composição do SVG final (spec §7).

O composer consome modelo + layout e monta o documento raiz: arestas primeiro
(as formas cobrem os endpoints), depois nós. Todo texto é escapado; números
saem com duas casas; duas execuções → bytes idênticos.
"""

import shutil

import pytest

from chen.model import Attribute, Diagram, Entity, Link, Relationship
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

        class Pedido(Entity):
            numero = Attribute(primary_key=True)

        class Faz(Relationship):
            cliente = Link(Cliente, "1")
            pedido = Link(Pedido, "N")

        diagrama = Diagram("V", elements=[Cliente, Pedido, Faz])

        svg = render_svg(diagrama)

        assert "A&lt;B&amp;C" in svg
        assert "A<B&amp;C>" not in svg  # o texto cru não passa


class TestDeterminismo:
    def test_duas_composicoes_geram_bytes_identicos(self):
        primeira = _svg_reduzido()
        segunda = _svg_reduzido()

        assert primeira == segunda
        assert primeira.encode("utf-8") == segunda.encode("utf-8")
