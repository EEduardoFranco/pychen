"""Hierarquia ISA (spec §2/§5, fase 2): triângulo e descritor de subclasse.

`ISA(SuperClass, total=..., disjoint=...)` é um descritor ao estilo `Owner`/`Link`,
declarado no corpo da `Entity` filha. Cada descritor vira um nó `ISATriangle`
com uma aresta `isa_child` (subclasse → triângulo) e uma `isa_super`
(triângulo → superclasse; rótulo `d`/`o`, linha dupla quando `total`) — o
compositor reusa a maquinaria de aresta existente (§8).
"""

from __future__ import annotations


class ISA:
    """Descritor de subclasse: `isa = ISA(Pessoa, total=False, disjoint=True)`.

    O nome do campo é irrelevante para a semântica; uso recomendado: `isa`.
    """

    def __init__(self, superclass: type, total: bool = False, disjoint: bool = False) -> None:
        self.superclass = superclass
        self.total = total
        self.disjoint = disjoint
        self.field_name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self.field_name = name


class ISATriangle:
    """Nó triângulo do grafo (§5): sem nome de usuário; as restrições moram nas
    arestas `isa_super` e o invariante "1 super, ≥ 1 sub" é garantido no build."""

    def __init__(self, total: bool = False, disjoint: bool = False) -> None:
        self.total = total
        self.disjoint = disjoint
        self.name: str = "ISA"
        self.obj_id: int = 0
