from modules.inputs import read_cpf, read_email, read_gender, read_password, read_yes_no
from modules.models import User, hash_password
from modules.rules import by_gender, pending_fines
from modules.state import (
    find_user_by_cpf, find_user_by_email, find_user_by_name, loanHistory, new_user_id, save_data, users,
)
from modules.storage import HISTORY_FILE, USERS_FILE
from modules.textutils import format_money


def read_new_username(first: str):
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
