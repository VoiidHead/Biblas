from modules.inputs import read_natural_number
from modules.models import Copy, Title
from modules.services.loans import close_loan
from modules.state import (
    active_loan, copies, copies_of, find_copy, find_title, new_copy_id, new_title_id, save_data, titles,
)
from modules.storage import COLLECTION_FILE
from modules.textutils import fold


def title_key(name: str, author: str, publisher: str, genre: str, pagesCount: int, year: int):
    return fold(name), fold(author), fold(publisher), fold(genre), pagesCount, year


def find_same_title(name: str, author: str, publisher: str, genre: str, pagesCount: int, year: int):
    newKey = title_key(name, author, publisher, genre, pagesCount, year)
    for title in titles:
        existingKey = title_key(title.name, title.author, title.publisher, title.genre, title.pages_count, title.year)
        if existingKey == newKey:
            return title
    return None


def add_book(name: str, author: str, publisher: str, genre: str, pagesCount: int, year: int, amount: int = 1):
    if amount == 0:
        selection = input("O número de exemplares não pode ser zero. Deseja alterar a quantidade? (s/n)").casefold()
        while selection not in ("s", "n"):
            print("Resposta inválida")
            selection = input("s - Alterar quantidade\nn - Cancelar operação").casefold()
        if selection == "s":
            while amount == 0:
                amount = read_natural_number("Quantidade de exemplares: ")
                if amount == 0:
                    print("A quantidade ainda é 0")
        else:
            print("Operação cancelada")
            return

    name, author, publisher, genre = name.strip(), author.strip(), publisher.strip(), genre.strip()
    title = find_same_title(name, author, publisher, genre, pagesCount, year)

    if title:
        print("Título já cadastrado. Os exemplares serão adicionados a ele")
    else:
        title = Title(new_title_id(), name, author, publisher, genre, pagesCount, year)
        titles.append(title)

    for added in range(1, amount + 1):
        copies.append(Copy(new_copy_id(), title.id))
        print(f"Adicionado: ({added}/{amount})")
        print(f"ID: {copies[-1].id}")
    print("\n")

    save_data(COLLECTION_FILE)


def remove_book(copyId: int):
    copy = find_copy(copyId)
    if not copy:
        print("Livro não encontrado\n")
        return

    changedFiles = [COLLECTION_FILE]
    loan = active_loan(copy)
    if loan:
        selection = input("Livro emprestado.\n1 - Removê-lo do acervo ainda assim\n2 - Cancelar operação\n")
        while selection not in ("1", "2"):
            print("Inválido")
            selection = input("1 - Remover\n2 - Cancelar\n")
        if selection == "2":
            print("Operação cancelada")
            return
        changedFiles += close_loan(loan, wasRemoved=True)

    copies.remove(copy)
    title = find_title(copy.title_id)
    if not copies_of(title):
        titles.remove(title)

    save_data(*changedFiles)
