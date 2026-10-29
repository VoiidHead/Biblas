"""Leitura e validação de dados digitados pelo operador.

Cada função repete a pergunta até receber um valor válido e devolve o valor
já convertido e normalizado, então quem chama não precisa revalidar.
"""

from getpass import getpass
from re import fullmatch

from modules.models import GENDERS
from modules.rules import is_valid_cpf
from modules.textutils import fold


def read_natural_number(message: str, isID: bool = False):
    """Lê um inteiro maior ou igual a zero.

    Args:
        message: Pergunta exibida ao operador.
        isID: Se True, a mensagem de erro para texto não numérico fala em 'ID'
            em vez de 'número'.

    Returns:
        O inteiro lido.
    """
    while True:
        try:
            value = int(input(message))
            if value < 0:
                print("Número inválido")
                continue
            return value
        except ValueError:
            if not isID:
                print("Isso não é um número")
            else:
                print("Isso não é um ID")


def read_positive_int(message: str):
    """Lê um inteiro maior que zero.

    Args:
        message: Pergunta exibida ao operador.

    Returns:
        O inteiro lido.
    """
    value = read_natural_number(message)
    while value == 0:
        print("O valor precisa ser maior que zero")
        value = read_natural_number(message)
    return value


def read_text(message: str):
    """Lê um texto obrigatório.

    Args:
        message: Pergunta exibida ao operador.

    Returns:
        O texto sem espaços nas pontas, nunca vazio.
    """
    text = input(message).strip()
    while not text:
        print("Este campo não pode ficar vazio")
        text = input(message).strip()
    return text


def read_year(message: str):
    """Lê um ano, aceitando negativos para anos antes da era comum (AEC).

    O ano 0 é recusado porque não existe no calendário.

    Args:
        message: Pergunta exibida ao operador.

    Returns:
        O ano como inteiro, positivo ou negativo.
    """
    while True:
        try:
            value = int(input(message))
        except ValueError:
            print("Isso não é um número")
            continue
        if value == 0:
            print("O ano 0 não existe")
            continue
        return value


def read_password(message: str):
    """Lê uma senha sem mostrá-la na tela.

    Args:
        message: Pergunta exibida ao operador.

    Returns:
        A senha sem espaços nas pontas, nunca vazia.
    """
    password = getpass(message).strip()
    while not password:
        print("A senha não pode ficar vazia")
        password = getpass(message).strip()
    return password


def read_email(message: str):
    """Lê um e-mail e confere se tem o formato básico algo@dominio.ext.

    Só o formato é verificado, não se o endereço existe.

    Args:
        message: Pergunta exibida ao operador.

    Returns:
        O e-mail em minúsculas e sem espaços nas pontas.
    """
    while True:
        email = input(message).strip().casefold()
        if fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return email
        print("E-mail inválido")


def read_cpf(message: str):
    """Lê um CPF e confere os dígitos verificadores.

    Aceita pontuação (pontos e traço), que é descartada.

    Args:
        message: Pergunta exibida ao operador.

    Returns:
        O CPF válido com apenas os 11 dígitos.
    """
    while True:
        cpf = "".join(character for character in input(message) if character.isdigit())
        if is_valid_cpf(cpf):
            return cpf
        print("CPF inválido")


def read_gender(message: str):
    """Mostra um menu numerado de gêneros e lê a escolha.

    Args:
        message: Texto exibido acima das opções.

    Returns:
        A chave interna escolhida ('male', 'female' ou 'other').
    """
    numberedGenders = {str(number): gender for number, gender in enumerate(GENDERS, start=1)}
    optionsText = "\n".join(f"{number} - {GENDERS[gender].capitalize()}" for number, gender in numberedGenders.items())
    while True:
        selection = input(f"{message}\n{optionsText}\n").strip()
        if selection in numberedGenders:
            return numberedGenders[selection]
        print("Opção inválida")


def read_yes_no(message: str):
    """Lê uma resposta de sim ou não.

    Aceita 's', 'sim', 'n' e 'não' (com ou sem acento, em qualquer caixa).

    Args:
        message: Pergunta exibida ao operador.

    Returns:
        True para sim, False para não.
    """
    while True:
        answer = fold(input(message))
        if answer in ("s", "sim"):
            return True
        if answer in ("n", "nao"):
            return False
        print("Resposta inválida. Digite s ou n")


def read_option(message: str, options: tuple):
    """Lê uma opção dentre as permitidas.

    Args:
        message: Pergunta exibida ao operador.
        options: Opções válidas, já em minúsculas.

    Returns:
        A opção escolhida, em minúsculas e sem espaços nas pontas.
    """
    while True:
        selection = input(message).strip().casefold()
        if selection in options:
            return selection
        print("Opção inválida")


def read_positive_int_or_keep(message: str, current: int):
    """Lê um inteiro maior que zero, ou mantém o valor atual se o operador só apertar Enter.

    Args:
        message: Pergunta exibida ao operador.
        current: Valor devolvido quando a entrada vem vazia.

    Returns:
        O novo valor, ou current.
    """
    while True:
        text = input(message).strip()
        if not text:
            return current
        try:
            value = int(text)
        except ValueError:
            print("Isso não é um número")
            continue
        if value > 0:
            return value
        print("O valor precisa ser maior que zero")


MAX_MONEY_CENTS = 10_000_000  # R$ 100.000,00


def read_money(message: str, default: int | None = None):
    """Lê um valor em reais e devolve em centavos.

    Aceita formatos como '1,50', '1.50', '10' e 'R$ 1.234,56'. Recusa zero e
    valores acima de MAX_MONEY_CENTS (R$ 100.000,00).

    Args:
        message: Pergunta exibida ao operador.
        default: Valor em centavos devolvido se o operador só apertar Enter.
            Se for None, Enter vazio é considerado inválido.

    Returns:
        O valor em centavos.
    """
    while True:
        text = input(message).strip().replace("R$", "").strip()
        if not text and default is not None:
            return default
        if "," in text:
            text = text.replace(".", "").replace(",", ".")
        if not fullmatch(r"[0-9]+(\.[0-9]{1,2})?", text):
            print("Valor inválido. Exemplo: 1,50")
            continue
        integer, _, decimals = text.partition(".")
        cents = int(integer) * 100 + int(decimals.ljust(2, "0") or 0)
        if cents == 0:
            print("O valor precisa ser maior que zero")
        elif cents > MAX_MONEY_CENTS:
            print("Valor muito alto")
        else:
            return cents
