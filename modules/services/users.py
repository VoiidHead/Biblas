"""Serviços de usuário: cadastro, edição, quitação de multas e zerar faltas.

Os nomes de usuário são guardados em minúsculas e são únicos sem diferenciar
acentos. CPF e e-mail também são únicos.
"""

from modules.inputs import read_cpf, read_email, read_gender, read_password, read_yes_no
from modules.models import User, hash_password
from modules.rules import by_gender, pending_fines
from modules.state import (
    find_user_by_cpf, find_user_by_email, find_user_by_name, loanHistory, new_user_id, save_data, users,
)
from modules.storage import HISTORY_FILE, USERS_FILE
from modules.textutils import format_money


def read_new_username(first: str):
    """Lê um nome de usuário que ainda não esteja em uso.

    Se o nome estiver vazio ou já existir, pergunta se o operador quer tentar
    outro.

    Args:
        first: Primeiro nome tentado (já digitado pelo operador).

    Returns:
        O nome livre, em minúsculas, ou None se o operador cancelar.
    """
    username = first.strip().casefold()
    while True:
        if not username:
            print("O nome de usuário não pode estar vazio")
        else:
            owner = find_user_by_name(username)
            if not owner:
                return username
            print(f"Nome de usuário em uso (conflita com '{owner.name}')")
            if not read_yes_no("Tentar outro? (s/n)\n"):
                print("Operação cancelada")
                return None
        username = input("Nome de usuário: ").strip().casefold()


def read_unique(reader, finder, message: str, label: str, current: User | None = None):
    """Lê um CPF ou e-mail até ser um valor ainda não cadastrado.

    Se o valor já pertencer a outro usuário, pergunta se o operador quer tentar
    outro.

    Args:
        reader: Função de leitura e validação (ex.: read_cpf, read_email).
        finder: Função que procura o dono de um valor (ex.: find_user_by_cpf).
        message: Pergunta exibida ao operador.
        label: Nome do campo, usado na mensagem de duplicidade.
        current: Usuário em edição, cujo próprio valor é permitido.

    Returns:
        O valor livre, ou None se o operador cancelar.
    """
    while True:
        value = reader(message)
        owner = finder(value)
        if not owner or owner is current:
            return value
        print(f"{label} já cadastrado para o usuário '{owner.name}'")
        if not read_yes_no("Tentar outro? (s/n)\n"):
            print("Operação cancelada")
            return None


def add_user(username: str):
    """Cadastra um novo usuário.

    Valida o nome de usuário e pede, em sequência, gênero, e-mail, CPF e senha.
    O e-mail e o CPF precisam ser únicos. Se o operador desistir em algum
    passo, nada é cadastrado. A senha é guardada como hash. Grava os usuários
    ao final.

    Args:
        username: Nome de usuário desejado.
    """
    username = read_new_username(username)
    if username is None:
        return

    gender = read_gender("Gênero:")
    email = read_unique(read_email, find_user_by_email, "E-mail: ", "E-mail")
    if email is None:
        return
    cpf = read_unique(read_cpf, find_user_by_cpf, "CPF: ", "CPF")
    if cpf is None:
        return
    password = read_password("Senha: ")
    users.append(User(new_user_id(), username, gender, email, cpf, hash_password(password)))
    save_data(USERS_FILE)


def edit_user(username: str, newUsername: str | None = None, gender: str | None = None,
              cpf: str | None = None, password: str | None = None, email: str | None = None):
    """Altera dados de um usuário.

    Só atualiza os campos informados (os que não forem None). Antes de mudar
    qualquer coisa, confere se o usuário existe e se o novo nome, CPF ou e-mail
    não pertencem a outro usuário; se algo falhar, nada é alterado. Assume
    que gênero, CPF e e-mail já vêm validados por modules.inputs.

    Args:
        username: Nome atual do usuário.
        newUsername: Novo nome de usuário.
        gender: Nova chave de gênero.
        cpf: Novo CPF, apenas com dígitos.
        password: Nova senha (guardada como hash).
        email: Novo e-mail.
    """
    user = find_user_by_name(username.strip().casefold())
    if not user:
        print("Usuário não encontrado")
        return

    if all(value is None for value in (newUsername, gender, cpf, password, email)):
        print("Nenhuma alteração informada")
        return

    if newUsername is not None:
        newUsername = newUsername.strip().casefold()
        if not newUsername:
            print("O nome de usuário não pode estar vazio")
            return
        if newUsername == user.name:
            print("O novo nome é igual ao atual")
            return
        owner = find_user_by_name(newUsername)
        if owner and owner is not user:
            print("Nome de usuário em uso")
            return
    if cpf is not None:
        owner = find_user_by_cpf(cpf)
        if owner and owner is not user:
            print(f"CPF já cadastrado para o usuário '{owner.name}'")
            return
    if email is not None:
        owner = find_user_by_email(email)
        if owner and owner is not user:
            print(f"E-mail já cadastrado para o usuário '{owner.name}'")
            return

    if newUsername is not None:
        user.name = newUsername
    if gender is not None:
        user.gender = gender
    if cpf is not None:
        user.cpf = cpf
    if email is not None:
        user.email = email
    if password is not None:
        user.change_password(password)

    save_data(USERS_FILE)
    print(f"Dados atualizados: {user.name}")


def pay_fines(user: User):
    """Quita todas as multas pendentes de um usuário, após confirmação.

    Lista as multas e o total antes de perguntar. Grava o histórico.

    Args:
        user: Usuário que está pagando.
    """
    fines = pending_fines(user.id, loanHistory)
    if not fines:
        print("Nenhuma multa pendente")
        return

    for loan in fines:
        print(f"    {loan.title_name} (exemplar {loan.copy_id}): {format_money(loan.fine_cents)}")
    print(f"Total: {format_money(sum(loan.fine_cents for loan in fines))}")
    if not read_yes_no("Confirmar o pagamento de todas as multas? (s/n)\n"):
        print("Operação cancelada")
        return

    for loan in fines:
        loan.fine_paid = True
    save_data(HISTORY_FILE)
    print("Multas quitadas")


def reset_faults(user: User):
    """Zera as faltas de um usuário, após confirmação, o que pode reabilitá-lo se estava banido.

    Args:
        user: Usuário a reabilitar.
    """
    if user.faults == 0:
        print(f"{by_gender(user, 'A usuária', 'O usuário')} não tem faltas")
        return
    if not read_yes_no(f"Zerar as {user.faults} faltas de {user.name}? (s/n)\n"):
        print("Operação cancelada")
        return

    user.faults = 0
    save_data(USERS_FILE)
    print("Faltas zeradas")


def edit_user_menu():
    """Pergunta qual usuário e qual dado editar, e executa a edição.

    Opções: nome, gênero, CPF, senha, e-mail, quitar multas pendentes e zerar faltas.
    """
    username = input("Nome do usuário: ").strip().casefold()
    user = find_user_by_name(username)
    if not user:
        print("Usuário não encontrado")
        return

    selection = input('''
                Qual dado deseja editar?
                1 - Nome
                2 - Gênero
                3 - CPF
                4 - Senha
                5 - E-mail
                6 - Quitar multas pendentes
                7 - Zerar faltas (reabilitar)
                        \n''')
    match selection:
        case "1":
            edit_user(username, newUsername=input("Novo nome de usuário: "))
        case "2":
            edit_user(username, gender=read_gender("Novo gênero:"))
        case "3":
            cpf = read_unique(read_cpf, find_user_by_cpf, "Novo CPF: ", "CPF", current=user)
            if cpf is not None:
                edit_user(username, cpf=cpf)
        case "4":
            edit_user(username, password=read_password("Nova senha: "))
        case "5":
            email = read_unique(read_email, find_user_by_email, "Novo e-mail: ", "E-mail", current=user)
            if email is not None:
                edit_user(username, email=email)
        case "6":
            pay_fines(user)
        case "7":
            reset_faults(user)
        case _:
            print("Opção inválida")
