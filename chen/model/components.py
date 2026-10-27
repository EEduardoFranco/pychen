"""Modelo de domínio (migrado do protótipo, evoluindo com type hints).

Identidade: contador global de módulo, fiel ao protótipo. A seção 5 da spec
determina que isso evolua para identificadores sequenciais dentro de `Diagram`.
"""


class Identifier:
    def __init__(self, start: int = 0) -> None:
        self.last_id = start

    def get_new(self) -> int:
        self.last_id += 1
        return self.last_id


idfr = Identifier()


class Attribute:
    def __init__(self, name: str, is_primary: bool = False) -> None:
        self.obj_id = idfr.get_new()
        self.name = name
        self.is_primary = is_primary

    def __repr__(self) -> str:
        return f'<Attribute name="{self.name}", obj_id={self.obj_id}>'


class Entity:
    def __init__(self, name: str) -> None:
        self.obj_id = idfr.get_new()
        self.name = name
        self.attributes: list[Attribute] = []

    def add_attribute(self, attr: Attribute) -> None:
        self.attributes.append(attr)

    def __repr__(self) -> str:
        return f'<Entity name="{self.name}", obj_id={self.obj_id}>'
