"""Flags de atributo (spec §5): partial_key, multivalued, derived + a variante de render.

A variante (§8) é escolhida por prioridade — o atributo é desenhado de um jeito só:
partial_key > primary_key > multivalued > derived > simple.
"""

from pychen.model.attributes import Attribute


class TestFlags:
    def test_partial_key_guarda_o_valor(self):
        attr = Attribute(partial_key=True)

        assert attr.partial_key is True
        assert attr.primary_key is False

    def test_multivalued_e_derived_guardam_os_valores(self):
        multivalorado = Attribute(multivalued=True)
        derivado = Attribute(derived=True)

        assert multivalorado.multivalued is True and multivalorado.derived is False
        assert derivado.derived is True and derivado.multivalued is False

    def test_clone_preserva_todas_as_flags(self):
        attr = Attribute(primary_key=False, multivalued=True, derived=False, partial_key=True)

        clone = attr.clone()

        assert clone.multivalued is True
        assert clone.partial_key is True
        assert clone.derived is False


class TestVarianteDeRender:
    def test_atributo_sem_flags_e_simples(self):
        assert Attribute().variant == "simple"

    def test_atributo_chave_e_key(self):
        assert Attribute(primary_key=True).variant == "key"

    def test_atributo_fraca_e_partial_key(self):
        assert Attribute(partial_key=True).variant == "partial_key"

    def test_atributo_multivalorado_e_multivalued(self):
        assert Attribute(multivalued=True).variant == "multivalued"

    def test_atributo_derivado_e_derived(self):
        assert Attribute(derived=True).variant == "derived"

    def test_prioridade_partial_key_vence_multivalued(self):
        assert Attribute(partial_key=True, multivalued=True).variant == "partial_key"

    def test_prioridade_chave_vence_multivalued_e_derived(self):
        assert Attribute(primary_key=True, multivalued=True, derived=True).variant == "key"
