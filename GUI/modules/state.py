from dataclasses import asdict
from pathlib import Path

from modules.models import Copy, Loan, Title, User, build_from_dict
from modules.storage import (
    COLLECTION_FILE, CONFIG_FILE, HISTORY_FILE, USERS_FILE,
    archive_old_format, load_file, write_json_files,
)
from modules.textutils import fold


def parse_collection(content: dict):
    return (
        content.get('next_title_id', 0),
        content.get('next_copy_id', 0),
        [build_from_dict(Title, titleData) for titleData in content.get('titles', [])],
        [build_from_dict(Copy, copyData) for copyData in content.get('copies', [])],
    )


def parse_users(content: dict):
    return (
        content.get('next_user_id', 0),
        [User(**userData) for userData in content.get('users', [])],
    )


DEFAULT_CONFIG = {
    'loan_days': 14,
    'max_loans': 5,
    'late_penalty': 'suspension',  # 'suspension' ou 'fine'
    'fine_per_day_cents': 100,
    'ban_enabled': False,
    'ban_after_faults': 3,
    'theme': 'system',  # 'system', 'light' ou 'dark'
}

CHOICES = {
    'late_penalty': ('suspension', 'fine'),
    'theme': ('system', 'light', 'dark'),
}


def parse_config(content: dict):
    config = dict(DEFAULT_CONFIG)
    for key, default in DEFAULT_CONFIG.items():
        value = content.get(key, default)
        if isinstance(default, bool):
            valid = isinstance(value, bool)
        elif isinstance(default, int):
            valid = isinstance(value, int) and not isinstance(value, bool) and value > 0
        else:
            valid = value in CHOICES[key]
        if valid:
            config[key] = value
    return config


def parse_history(content: list):
    return [build_from_dict(Loan, loanData) for loanData in content]


# As listas e o dicionário abaixo são compartilhados entre os módulos: nunca devem ser reatribuídos.
# Os contadores de ID são reatribuídos, então use new_title_id, new_copy_id e new_user_id.
archive_old_format()

nextTitleId, nextCopyId, titles, copies = load_file(COLLECTION_FILE, {}, parse_collection)
nextUserId, users = load_file(USERS_FILE, {}, parse_users)
config = load_file(CONFIG_FILE, {}, parse_config)
loanHistory = load_file(HISTORY_FILE, [], parse_history)

nextTitleId = max(nextTitleId, max((title.id for title in titles), default=-1) + 1)
nextCopyId = max(nextCopyId, max((copy.id for copy in copies), default=-1) + 1)
nextUserId = max(
    nextUserId,
    max((user.id for user in users), default=-1) + 1,
    max((loan.user_id for loan in loanHistory), default=-1) + 1,
)


def new_title_id():
    global nextTitleId
    assignedId = nextTitleId
    nextTitleId += 1
    return assignedId


def new_copy_id():
    global nextCopyId
    assignedId = nextCopyId
    nextCopyId += 1
    return assignedId


def new_user_id():
    global nextUserId
    assignedId = nextUserId
    nextUserId += 1
    return assignedId


def save_data(*files: Path):
    contents = {}
    if COLLECTION_FILE in files:
        contents[COLLECTION_FILE] = {
            'next_title_id': nextTitleId,
            'next_copy_id': nextCopyId,
            'titles': [asdict(title) for title in titles],
            'copies': [asdict(copy) for copy in copies],
        }
    if USERS_FILE in files:
        contents[USERS_FILE] = {
            'next_user_id': nextUserId,
            'users': [user.to_dict() for user in users],
        }
    if CONFIG_FILE in files:
        contents[CONFIG_FILE] = config
    if HISTORY_FILE in files:
        contents[HISTORY_FILE] = [asdict(loan) for loan in loanHistory]
    write_json_files(contents)


def find_copy(copyId: int):
    return next((copy for copy in copies if copy.id == copyId), None)


def find_title(titleId: int):
    return next((title for title in titles if title.id == titleId), None)


def find_user(userId: int):
    return next((user for user in users if user.id == userId), None)


def find_user_by_name(username: str):
    key = fold(username)
    return next((user for user in users if fold(user.name) == key), None)


def find_user_by_cpf(cpf: str):
    return next((user for user in users if user.cpf == cpf), None)


def find_user_by_email(email: str):
    key = email.strip().casefold()
    return next((user for user in users if user.email.casefold() == key), None)


def username_of(loan: Loan):
    user = find_user(loan.user_id)
    return user.name if user else "usuário desconhecido"


def copies_of(title: Title):
    return [copy for copy in copies if copy.title_id == title.id]


def active_loan(copy: Copy):
    return next((loan for loan in loanHistory if loan.copy_id == copy.id and loan.return_date is None), None)
