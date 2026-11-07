from modules.models import GENDERS
from modules.rules import (
    by_gender, days_late, is_banned, late_text, loan_status, open_loans, pending_fines, suspension_end,
)
from modules.state import active_loan, config, copies_of, loanHistory, titles, username_of
from modules.textutils import fold, format_cpf, format_date, format_money, year_text

SEARCH_FIELDS = (
    ("id", "ID do exemplar"),
    ("name", "Nome"),
    ("author", "Autor"),
    ("publisher", "Editora"),
    ("genre", "Gênero"),
)
TITLE_HEADERS = ["Nome", "Autor", "Editora", "Gênero", "Páginas", "Ano", "Disponíveis", "Emprestados"]
COPY_HEADERS = ["ID", "Situação", "Mutuário", "Data máxima", "Atraso"]
TITLE_HISTORY_HEADERS = ["Exemplar", "Usuário", "Emprestado em", "Data máxima", "Situação", "Atraso"]
USER_HEADERS = ["Usuário", "Empréstimos", "Em atraso", "Situação", "Multas pendentes"]
USER_HISTORY_HEADERS = ["Livro", "Exemplar", "Emprestado em", "Data máxima", "Situação", "Atraso", "Multa"]


def copy_row(copy):
    loan = active_loan(copy)
    if not loan:
        return [copy.id, "disponível", "", "", ""]
    return [copy.id, "emprestado", username_of(loan), format_date(loan.due_date), late_text(loan)]


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
            year_text(title.year), ", ".join(availableIds), ", ".join(borrowedCopies)]


def title_details(title):
    return [
        ("Nome", title.name),
        ("Autor", title.author),
        ("Editora", title.publisher),
        ("Gênero", title.genre),
        ("Páginas", title.pages_count),
        ("Ano de lançamento", year_text(title.year)),
    ]


def title_counts(title):
    titleCopies = copies_of(title)
    return len(titleCopies), sum(1 for copy in titleCopies if not active_loan(copy))


def title_history_rows(title):
    titleLoans = [loan for loan in loanHistory if loan.title_id == title.id]
    return [[loan.copy_id, username_of(loan), format_date(loan.loan_date), format_date(loan.due_date),
             loan_status(loan), late_text(loan)] for loan in reversed(titleLoans)]


def title_matches(title, filters: dict):
    for attribute, value in filters.items():
        if attribute == "id":
            if not any(copy.id == value for copy in copies_of(title)):
                return False
        elif fold(value) not in fold(getattr(title, attribute)):
            return False
    return True


def search_titles(filters: dict):
    return [title for title in titles if title_matches(title, filters)]


def user_row(user):
    loans = open_loans(user.id, loanHistory)
    borrowed = ", ".join(str(loan.copy_id) for loan in loans)
    late = ", ".join(str(loan.copy_id) for loan in loans if days_late(loan) > 0)

    statuses = []
    suspensionEnd = suspension_end(user)
    if suspensionEnd:
        statuses.append(f"{by_gender(user, 'suspensa', 'suspenso')} até {format_date(suspensionEnd)}")
    if is_banned(user, config):
        statuses.append(by_gender(user, "banida", "banido"))

    fines = pending_fines(user.id, loanHistory)
    fineText = format_money(sum(loan.fine_cents for loan in fines)) if fines else ""
    return [user.name, borrowed, late, ", ".join(statuses) or "regular", fineText]


def user_details(user):
    details = [
        ("Nome", user.name),
        ("Gênero", GENDERS[user.gender]),
        ("E-mail", user.email),
        ("CPF", format_cpf(user.cpf)),
    ]

    suspensionEnd = suspension_end(user)
    if suspensionEnd:
        details.append((by_gender(user, "Suspensa", "Suspenso"), f"até {format_date(suspensionEnd)}"))

    faultsText = str(user.faults)
    if config['ban_enabled']:
        faultsText += f" (limite para banimento: {config['ban_after_faults']})"
    details.append(("Faltas (atrasos)", faultsText))
    if is_banned(user, config):
        details.append((by_gender(user, "BANIDA", "BANIDO"), "da biblioteca: empréstimos bloqueados"))

    fines = pending_fines(user.id, loanHistory)
    if fines:
        details.append(("Multas pendentes", f"{format_money(sum(loan.fine_cents for loan in fines))} ({len(fines)})"))
    return details


def user_history_rows(user):
    rows = []
    for loan in reversed([loan for loan in loanHistory if loan.user_id == user.id]):
        fineText = ""
        if loan.fine_cents:
            fineText = f"{format_money(loan.fine_cents)} ({'paga' if loan.fine_paid else 'pendente'})"
        rows.append([loan.title_name, loan.copy_id, format_date(loan.loan_date), format_date(loan.due_date),
                     loan_status(loan), late_text(loan), fineText])
    return rows
