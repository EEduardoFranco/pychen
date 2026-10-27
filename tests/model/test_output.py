"""API pública de saída (spec §4): `Diagram.to_svg()` e `Diagram.save(path)`."""

from pychen.model import Attribute, Diagram, Entity, Link, Relationship


def _vendas_diagrama():
    class Cliente(Entity):
        cpf = Attribute(primary_key=True)

    class Pedido(Entity):
        numero = Attribute(primary_key=True)

    class Faz(Relationship):
        cliente = Link(Cliente, "1")
        pedido = Link(Pedido, "N")

    return Diagram("Vendas", elements=[Cliente, Pedido, Faz])


class TestToSvg:
    def test_to_svg_retorna_o_documento(self):
        svg = _vendas_diagrama().to_svg()

        assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"')

    def test_to_svg_duas_chamadas_sao_byte_a_byte(self):
        diagrama = _vendas_diagrama()

        assert diagrama.to_svg() == diagrama.to_svg()


class TestSave:
    def test_save_grava_arquivo_com_o_mesmo_conteudo_de_to_svg(self, tmp_path):
        diagrama = _vendas_diagrama()

        destino = tmp_path / "vendas.svg"

        diagrama.save(destino)

        assert destino.read_text(encoding="utf-8") == diagrama.to_svg()
