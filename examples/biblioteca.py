"""A second domain (library loans) exercising the same phase-1 notation."""

from pathlib import Path

from chen import Attribute, Diagram, Entity, Link, Owner, Relationship, WeakEntity


class Aluno(Entity):
    ra = Attribute(primary_key=True)
    nome = Attribute()


class Livro(Entity):
    isbn = Attribute(primary_key=True)
    titulo = Attribute()


class Emprestimo(Relationship):
    aluno = Link(Aluno, "1")
    livro = Link(Livro, "N", total=True)
    data_devolucao = Attribute(derived=True)


class Estoque(WeakEntity):
    owner = Owner(Livro)
    copia = Attribute(partial_key=True)
    prateleira = Attribute()


if __name__ == "__main__":
    saida = Path(__file__).resolve().parent / "biblioteca.svg"
    Diagram("Biblioteca", elements=[Aluno, Livro, Estoque, Emprestimo]).save(saida)
    print(f"written: {saida}")
