"""Menus do programa e as funções que ligam cada opção ao serviço correspondente.

As funções read_* pedem ao operador os dados necessários e chamam o serviço
que faz o trabalho. FULL_MENU e EMPTY_MENU mapeiam a tecla digitada para
uma tupla (rótulo, ação, pausar depois?).
"""

from modules.inputs import read_natural_number, read_password, read_positive_int, read_text, read_year
from modules.queries import book_query, collection_query, user_query, users_query
from modules.services.books import add_book, remove_book
from modules.services.loans import borrow, give_back
from modules.services.settings import change_config
from modules.services.users import add_user, edit_user_menu

MENU_INDENT = " " * 16


def read_borrow():
    """Pede o ID do exemplar, o nome do usuário e a senha e registra o empréstimo."""
    borrow(read_natural_number("ID do exemplar: ", isID=True), input("Nome do Usuário: ").strip().casefold(),
           read_password("Senha: "))


def read_give_back():
    """Pede o ID do exemplar e registra a devolução."""
    give_back(read_natural_number("ID do exemplar: ", isID=True))


def read_add_user():
    """Pede o nome de usuário e inicia o cadastro de um novo usuário."""
    add_user(input("Nome de usuário: "))


def read_add_book():
    """Pede os dados do livro e a quantidade de exemplares e os adiciona ao acervo."""
    add_book(read_text("Nome do livro: "),
             read_text("Nome do autor: "),
             read_text("Nome da editora: "),
             read_text("Gênero: "),
             read_positive_int("Número de Páginas: "),
             read_year("Ano de lançamento (negativo para AEC): "),
             amount=read_natural_number("Quantidade de exemplares: "))


def read_remove_book():
    """Pede o ID de um exemplar e o remove do acervo."""
    remove_book(read_natural_number("ID do exemplar: ", isID=True))


def read_user_query():
    """Pede o nome de um usuário e mostra a ficha e o histórico dele."""
    user_query(input("Nome do usuário: ").strip().casefold())


# tecla: (rótulo, ação, pedir para o operador apertar algo depois?)
FULL_MENU = {
    "1": ("Empréstimo", read_borrow, True),
    "2": ("Devolução", read_give_back, True),
    "3": ("Cadastro de usuário", read_add_user, True),
    "4": ("Editar usuário", edit_user_menu, True),
    "5": ("Adicionar livro ao acervo", read_add_book, True),
    "6": ("Remover exemplar do acervo", read_remove_book, True),
    "7": ("Buscar livro", book_query, True),
    "8": ("Consultar usuário", read_user_query, True),
    "9": ("Ver acervo", collection_query, True),
    "10": ("Ver lista de usuários", users_query, True),
    "*": ("Configurações", change_config, False),
}

# Sem acervo só aparecem as opções que não dependem de exemplares
EMPTY_MENU = {
    "1": ("Adicionar livro ao acervo", read_add_book, True),
    "2": ("Cadastrar usuário", read_add_user, True),
    "3": ("Editar usuário", edit_user_menu, True),
    "4": ("Ver lista de usuários", users_query, True),
    "5": ("Consultar usuário", read_user_query, True),
    "*": ("Configurações", change_config, False),
}


def menu_text(options: dict):
    """Monta o texto do menu principal.

    Args:
        options: Dicionário de tecla para tupla (rótulo, ação, pausar).

    Returns:
        Texto com uma linha por opção, mais a opção '/' para fechar o programa.
    """
    lines = [f"{MENU_INDENT}{key} - {label}" for key, (label, _, _) in options.items()]
    lines.append(f"{MENU_INDENT}/ - Fechar o programa")
    return "\n" + "\n".join(lines) + "\n" + MENU_INDENT + "\n"
