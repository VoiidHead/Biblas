"""Estado da aplicação em memória, carregado do disco ao importar o módulo.

Ao ser importado, este módulo arquiva arquivos em formato antigo, carrega
acervo, usuários, configuração e histórico, e calcula os próximos IDs.

As listas (titles, copies, users, loanHistory) e o dicionário config são
compartilhados: os outros módulos os importam e os alteram no próprio
objeto, por isso eles nunca devem ser reatribuídos. Os contadores de ID são
reatribuídos, então para obter um novo ID use new_title_id, new_copy_id e
new_user_id. Alterações só vão para o disco com save_data. Também reúne as
funções de busca por ID, nome, CPF e e-mail.
"""

from dataclasses import asdict
from pathlib import Path

from modules.models import Copy, Loan, Title, User, build_from_dict
from modules.storage import (
    COLLECTION_FILE, CONFIG_FILE, HISTORY_FILE, USERS_FILE,
    archive_old_format, load_file, write_json_files,
)
from modules.textutils import fold


def parse_collection(content: dict):
    """Converte o conteúdo de collection.json nas estruturas em memória.

    Args:
        content: Dicionário lido do arquivo. Chaves ausentes viram 0 ou lista vazia.

    Returns:
        Tupla (próximo ID de título, próximo ID de exemplar, títulos, exemplares).

    Raises:
        TypeError, AttributeError: Se a estrutura estiver malformada.
            load_file trata esses erros.
    """
    return (
        content.get('next_title_id', 0),
        content.get('next_copy_id', 0),
        [build_from_dict(Title, titleData) for titleData in content.get('titles', [])],
        [build_from_dict(Copy, copyData) for copyData in content.get('copies', [])],
    )


def parse_users(content: dict):
    """Converte o conteúdo de users.json nas estruturas em memória.

    Args:
        content: Dicionário lido do arquivo. Chaves ausentes viram 0 ou lista vazia.

    Returns:
        Tupla (próximo ID de usuário, lista de usuários).

    Raises:
        TypeError, AttributeError: Se a estrutura estiver malformada ou algum
            usuário tiver campos desconhecidos. load_file trata esses erros.
    """
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
}


def parse_config(content: dict):
    """Valida o conteúdo de config.json, completando com os valores padrão.

    Cada chave de DEFAULT_CONFIG usa o valor do arquivo apenas se ele for
    válido: bool para as opções liga/desliga, inteiro positivo para os números
    e 'suspension' ou 'fine' para late_penalty. Valores inválidos e chaves
    desconhecidas são descartados.

    Args:
        content: Dicionário lido do arquivo.

    Returns:
        Dicionário de configuração completo e válido.
    """
    config = dict(DEFAULT_CONFIG)
    for key, default in DEFAULT_CONFIG.items():
        value = content.get(key, default)
        if isinstance(default, bool):
            valid = isinstance(value, bool)
        elif isinstance(default, int):
            valid = isinstance(value, int) and not isinstance(value, bool) and value > 0
        else:
            valid = value in ('suspension', 'fine')
        if valid:
            config[key] = value
    return config


def parse_history(content: list):
    """Converte o conteúdo de history.log na lista de empréstimos.

    Args:
        content: Lista de dicionários lida do arquivo.

    Returns:
        Lista de Loan.
    """
    return [build_from_dict(Loan, loanData) for loanData in content]


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
    """Reserva e devolve o próximo ID de título, avançando o contador."""
    global nextTitleId
    assignedId = nextTitleId
    nextTitleId += 1
    return assignedId


def new_copy_id():
    """Reserva e devolve o próximo ID de exemplar, avançando o contador."""
    global nextCopyId
    assignedId = nextCopyId
    nextCopyId += 1
    return assignedId


def new_user_id():
    """Reserva e devolve o próximo ID de usuário, avançando o contador."""
    global nextUserId
    assignedId = nextUserId
    nextUserId += 1
    return assignedId


def save_data(*files: Path):
    """Grava em disco apenas os arquivos indicados.

    Monta o conteúdo a partir do estado atual em memória e grava tudo de uma
    vez com write_json_files.

    Args:
        *files: Um ou mais de COLLECTION_FILE, USERS_FILE, CONFIG_FILE e
            HISTORY_FILE. Os demais não são tocados.
    """
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
    """Procura um exemplar pelo ID.

    Returns:
        O exemplar, ou None se não existir.
    """
    return next((copy for copy in copies if copy.id == copyId), None)


def find_title(titleId: int):
    """Procura um título pelo ID.

    Returns:
        O título, ou None se não existir.
    """
    return next((title for title in titles if title.id == titleId), None)


def find_user(userId: int):
    """Procura um usuário pelo ID.

    Returns:
        O usuário, ou None se não existir.
    """
    return next((user for user in users if user.id == userId), None)


def find_user_by_name(username: str):
    """Procura um usuário pelo nome, ignorando acentos, maiúsculas e espaços nas pontas.

    Returns:
        O usuário, ou None se não existir.
    """
    key = fold(username)
    return next((user for user in users if fold(user.name) == key), None)


def find_user_by_cpf(cpf: str):
    """Procura um usuário pelo CPF.

    Args:
        cpf: CPF apenas com dígitos, igual ao guardado no cadastro.

    Returns:
        O usuário, ou None se não existir.
    """
    return next((user for user in users if user.cpf == cpf), None)


def find_user_by_email(email: str):
    """Procura um usuário pelo e-mail, ignorando maiúsculas e espaços nas pontas.

    Returns:
        O usuário, ou None se não existir.
    """
    key = email.strip().casefold()
    return next((user for user in users if user.email.casefold() == key), None)


def username_of(loan: Loan):
    """Devolve o nome do usuário que fez um empréstimo.

    Returns:
        O nome, ou 'usuário desconhecido' se o usuário não existir mais.
    """
    user = find_user(loan.user_id)
    return user.name if user else "usuário desconhecido"


def copies_of(title: Title):
    """Lista os exemplares de um título.

    Returns:
        Exemplares cujo title_id é o ID do título.
    """
    return [copy for copy in copies if copy.title_id == title.id]


def active_loan(copy: Copy):
    """Procura o empréstimo em andamento de um exemplar.

    Returns:
        O empréstimo ainda não devolvido, ou None se o exemplar estiver disponível.
    """
    return next((loan for loan in loanHistory if loan.copy_id == copy.id and loan.return_date is None), None)
