"""Atributos (spec §5): nós elipse do grafo, declarados como descritores de classe.

`Attribute` usa `__set_name__` para capturar o nome do campo onde foi declarado
(`cpf = Attribute(primary_key=True)`).
"""

from __future__ import annotations


class Attribute:
    def __init__(self, primary_key: bool = False) -> None:
        self.primary_key = primary_key
        self.name: str = ""
        self.obj_id: int = 0

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def clone(self) -> Attribute:
        """Cópia para o diagrama: o modelo instancia cópias por diagrama (spec §4)."""
        copia = Attribute(primary_key=self.primary_key)
        copia.name = self.name
        return copia
