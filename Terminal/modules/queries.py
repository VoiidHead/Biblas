from datetime import date

from modules.inputs import read_natural_number
from modules.models import GENDERS
from modules.rules import by_gender, days_late, is_banned, loan_status, loan_summary, pending_fines, suspension_end
from modules.state import (
    active_loan, config, copies_of, find_user_by_name, loanHistory, titles, username_of, users,
)
from modules.textutils import fold, format_money
from modules.tabulate import tabulate

SEARCH_OPTIONS = {
    "a": ("ID do exemplar", "id"),
    "b": ("Nome", "name"),
    "c": ("Autor", "author"),
    "d": ("Editora", "publisher"),
    "e": ("Gênero", "genre"),
}
TITLES_MAX_WIDTHS = [18, 14, 12, 10, None, None, 13, 16]
DETAILS_MAX_WIDTHS = [None, 40]
COPIES_MAX_WIDTHS = [None, None, 14, None, None]
HISTORY_MAX_WIDTHS = [None, 14, None, None, 22, None]


def year_text(year: int):
    return f"{abs(year)} AEC" if year < 0 else str(year)


def late_text(loan):
    lateDays = days_late(loan)
    if not lateDays:
        return ""
    dayWord = "dias" if lateDays > 1 else "dia"
    return f"{lateDays} {dayWord}"


def copy_row(copy):
    loan = active_loan(copy)
    if not loan:
        return [copy.id, "disponível", "", "", ""]
    dueDate = date.fromisoformat(loan.due_date)
    return [copy.id, "emprestado", username_of(loan), f"{dueDate:%d/%m/%Y}", late_text(loan)]


def title_row(title):
    availableIds = []
    borrowedCopies = []
    for copy in copies_of(title):
        loan = active_loan(copy)
        if loan:
            borrowedCopies.append(f"{copy.id} ({username_of(loan)})")
        else:
            availableIds.append(str(copy.id))
    return [title.name, title.author, title.publisher, title.genre, title.pages_count,
            year_text(title.year), ", ".join(availableIds), "\n".join(borrowedCopies)]


def show_titles(titleList):
    headers = ["Nome", "Autor", "Editora", "Gênero", "Páginas", "Ano", "Disponíveis", "Emprestados"]
    rows = [title_row(title) for title in titleList]
    print(tabulate(rows, headers=headers, tablefmt="grid", disable_numparse=True, maxcolwidths=TITLES_MAX_WIDTHS))
    print()


def show_title(title):
    titleCopies = copies_of(title)
    availableCount = sum(1 for copy in titleCopies if not active_loan(copy))
    details = [
        ["Nome", title.name],
        ["Autor", title.author],
        ["Editora", title.publisher],
        ["Gênero", title.genre],
        ["Páginas", title.pages_count],
        ["Ano de lançamento", year_text(title.year)],
    ]
    print(tabulate(details, tablefmt="grid", disable_numparse=True, maxcolwidths=DETAILS_MAX_WIDTHS))
    print(f"Exemplares: {len(titleCopies)} | Disponíveis: {availableCount}")
    headers = ["ID", "Situação", "Mutuário", "Data máxima", "Atraso"]
    rows = [copy_row(copy) for copy in titleCopies]
    print(tabulate(rows, headers=headers, tablefmt="grid", disable_numparse=True, maxcolwidths=COPIES_MAX_WIDTHS))
    print()


def show_title_history(title):
    titleLoans = [loan for loan in loanHistory if loan.title_id == title.id]
    print("Histórico de empréstimos:")
    if not titleLoans:
        print("Nenhum empréstimo registrado\n")
        return
    rows = []
    for loan in reversed(titleLoans):
        loanDate = date.fromisoformat(loan.loan_date)
        dueDate = date.fromisoformat(loan.due_date)
        rows.append([loan.copy_id, username_of(loan), f"{loanDate:%d/%m/%Y}", f"{dueDate:%d/%m/%Y}",
                     loan_status(loan), late_text(loan)])
    headers = ["Exemplar", "Usuário", "Emprestado em", "Data máxima", "Situação", "Atraso"]
    print(tabulate(rows, headers=headers, tablefmt="grid", disable_numparse=True, maxcolwidths=HISTORY_MAX_WIDTHS))
    print()


def title_matches(title, filters: dict):
    for attribute, value in filters.items():
        if attribute == "id":
            if not any(copy.id == value for copy in copies_of(title)):
                return False
        elif fold(value) not in fold(getattr(title, attribute)):
            return False
    return True


def collection_query():
    print("Acervo:")
    show_titles(titles)


def book_query():
    optionsText = "\n".join(f"{letter.upper()} - {label}" for letter, (label, attribute) in SEARCH_OPTIONS.items())
    answer = input(f"Buscar por quais parâmetros? Digite as letras, por exemplo BC:\n{optionsText}\n").casefold()
    chosen = list(dict.fromkeys(char for char in answer if char not in " ,;"))

    if not chosen or any(char not in SEARCH_OPTIONS for char in chosen):
        print("Opção inválida\n")
        return

    filters = {}
    for letter in chosen:
        label, attribute = SEARCH_OPTIONS[letter]
        if attribute == "id":
            filters[attribute] = read_natural_number("ID do exemplar: ", isID=True)
        else:
            filters[attribute] = input(f"{label}: ").strip().casefold()

    foundTitles = [title for title in titles if title_matches(title, filters)]
    if not foundTitles:
        print("Nenhum livro encontrado\n")
        return

    if len(foundTitles) == 1:
        show_title(foundTitles[0])
        show_title_history(foundTitles[0])
    else:
        show_titles(foundTitles)
        print("Refine a busca (por exemplo, pelo ID de um exemplar) para ver os exemplares e o histórico de um livro\n")


def users_query():
    if users:
        for user in users:
            activeLoans = [loan for loan in loanHistory if loan.user_id == user.id and loan.return_date is None]
            borrowedBooks = [loan.copy_id for loan in activeLoans]
            lateBooks = [loan.copy_id for loan in activeLoans if days_late(loan) > 0]
            isFemale = user.gender == "female"
            borrowerWord = "mutuária" if isFemale else "mutuário"

            details = [user.name]
            if len(borrowedBooks) > 1:
                firstBooks = ", ".join(map(str, borrowedBooks[:-1]))
                details.append(f"{borrowerWord} dos livros: {firstBooks} e {borrowedBooks[-1]}")
            elif borrowedBooks:
                details.append(f"{borrowerWord} do livro {borrowedBooks[0]}")

            if lateBooks:
                lateIds = ", ".join(map(str, lateBooks))
                bookWord = "livros" if len(lateBooks) > 1 else "livro"
                details.append(f"{bookWord} em atraso: {lateIds}")

            suspensionEnd = suspension_end(user)
            if suspensionEnd:
                suspendedWord = "suspensa" if isFemale else "suspenso"
                details.append(f"{suspendedWord} até {suspensionEnd:%d/%m/%Y}")

            if is_banned(user, config):
                details.append("banida" if isFemale else "banido")

            fines = pending_fines(user.id, loanHistory)
            if fines:
                details.append(f"multas pendentes: {format_money(sum(loan.fine_cents for loan in fines))}")

            print(" - ".join(details))
    else:
        print("Não existem usuários registrados no sistema")


def user_query(username: str):
    user = find_user_by_name(username)
    if not user:
        print("Usuário não encontrado")
        return

    isFemale = user.gender == "female"
    cpf = user.cpf
    print(f"Nome: {user.name}")
    print(f"Gênero: {GENDERS[user.gender]}")
    print(f"E-mail: {user.email}")
    print(f"CPF: {cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}")

    suspensionEnd = suspension_end(user)
    if suspensionEnd:
        suspendedWord = "Suspensa" if isFemale else "Suspenso"
        print(f"{suspendedWord} até {suspensionEnd:%d/%m/%Y}")

    faultsText = f"Faltas (devoluções com atraso): {user.faults}"
    if config['ban_enabled']:
        faultsText += f" (limite para banimento: {config['ban_after_faults']})"
    print(faultsText)
    if is_banned(user, config):
        print(f"{by_gender(user, 'BANIDA', 'BANIDO')} da biblioteca: empréstimos bloqueados")

    fines = pending_fines(user.id, loanHistory)
    if fines:
        print(f"Multas pendentes: {format_money(sum(loan.fine_cents for loan in fines))} ({len(fines)})")

    userLoans = [loan for loan in loanHistory if loan.user_id == user.id]
    if not userLoans:
        userWord = "A usuária" if isFemale else "O usuário"
        print(f"{userWord} não possui empréstimos registrados")
        return

    print("Histórico de empréstimos:")
    for loan in reversed(userLoans):
        print(f"    {loan.title_name} (exemplar {loan.copy_id}) | {loan_summary(loan)}")
