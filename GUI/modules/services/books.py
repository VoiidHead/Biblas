from modules.errors import BiblasError
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
    if amount < 1:
        raise BiblasError("A quantidade de exemplares precisa ser maior que zero")

    name, author, publisher, genre = name.strip(), author.strip(), publisher.strip(), genre.strip()
    title = find_same_title(name, author, publisher, genre, pagesCount, year)
    isNewTitle = title is None

    if isNewTitle:
        title = Title(new_title_id(), name, author, publisher, genre, pagesCount, year)
        titles.append(title)

    newCopies = []
    for _ in range(amount):
        copy = Copy(new_copy_id(), title.id)
        copies.append(copy)
        newCopies.append(copy)

    save_data(COLLECTION_FILE)
    return title, isNewTitle, newCopies


def remove_book(copyId: int):
    copy = find_copy(copyId)
    if not copy:
        raise BiblasError("Livro não encontrado")

    changedFiles = [COLLECTION_FILE]
    messages = []
    loan = active_loan(copy)
    if loan:
        messages, closedFiles = close_loan(loan, wasRemoved=True)
        changedFiles += closedFiles

    copies.remove(copy)
    title = find_title(copy.title_id)
    if not copies_of(title):
        titles.remove(title)

    save_data(*changedFiles)
    return messages
