"""Leitura e gravação dos arquivos de dados em JSON.

Os arquivos ficam em data/, ao lado da pasta modules. O histórico usa a
extensão .log, mas também contém JSON. Arquivos que não puderem ser lidos
ou estiverem em formato antigo são movidos para data/unreadable/ em vez de
serem apagados.
"""

from datetime import datetime
from json import dump, load, JSONDecodeError
from os import replace
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
UNREADABLE_DIR = DATA_DIR / 'unreadable'
COLLECTION_FILE = DATA_DIR / 'collection.json'
USERS_FILE = DATA_DIR / 'users.json'
CONFIG_FILE = DATA_DIR / 'config.json'
HISTORY_FILE = DATA_DIR / 'history.log'


def move_to_unreadable(path: Path, label: str = ''):
    """Move um arquivo problemático para data/unreadable/<nome do arquivo>/.

    O novo nome combina o nome original, o rótulo e a data/hora, com extensão
    .bak. Avisa o operador do que aconteceu e para onde o arquivo foi.

    Args:
        path: Arquivo a mover.
        label: Motivo da movimentação, incluído no nome (ex.: 'Old_Format').

    Returns:
        Caminho do arquivo no novo local.
    """
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    name = '-'.join(part for part in (path.stem, label, timestamp) if part)
    targetDir = UNREADABLE_DIR / path.stem
    targetDir.mkdir(parents=True, exist_ok=True)
    targetPath = targetDir / f"{name}.bak"
    replace(path, targetPath)
    print(f"*{path.name} não pôde ser lido. Arquivo movido para {targetPath.relative_to(DATA_DIR.parent)}")
    return targetPath


def read_json(path: Path, default):
    """Lê um arquivo JSON.

    Args:
        path: Arquivo a ler.
        default: Valor devolvido se o arquivo não existir ou for ilegível.

    Returns:
        O conteúdo decodificado. Se o arquivo não for JSON válido ou UTF-8
        válido, ele é movido para data/unreadable/ e o padrão é devolvido.
    """
    try:
        with open(path, encoding='utf-8') as file:
            return load(file)
    except FileNotFoundError:
        return default
    except (JSONDecodeError, UnicodeDecodeError):
        move_to_unreadable(path)
        return default


def load_file(path: Path, default, parse):
    """Lê um arquivo e converte o conteúdo na estrutura usada pelo programa.

    Se o JSON é válido mas tem estrutura incompatível com o que parse espera
    (AttributeError, TypeError ou ValueError), o arquivo é movido para
    data/unreadable/ e o programa começa com o estado vazio.

    Args:
        path: Arquivo a carregar.
        default: Conteúdo assumido se o arquivo não existir ou estiver ilegível.
        parse: Função que recebe o conteúdo JSON e devolve a estrutura final.

    Returns:
        O resultado de parse aplicado ao conteúdo (ou ao padrão, em caso de erro).
    """
    try:
        return parse(read_json(path, default))
    except (AttributeError, TypeError, ValueError):
        move_to_unreadable(path, label='Invalid_Format')
        return parse(default)


def write_json_files(contents: dict):
    """Grava vários arquivos JSON de uma vez.

    Cada conteúdo é escrito primeiro em um arquivo temporário (.tmp). Só
    depois de todos terem sido escritos com sucesso os originais são
    substituídos, o que reduz o risco de deixar os arquivos inconsistentes
    entre si se algo falhar no meio. Cria a pasta data/ se necessário.

    Args:
        contents: Dicionário de caminho do arquivo para o conteúdo a gravar.
    """
    DATA_DIR.mkdir(exist_ok=True)
    temporaryPaths = {}
    for path, content in contents.items():
        temporaryPath = path.with_suffix('.tmp')
        with open(temporaryPath, 'w', encoding='utf-8') as file:
            dump(content, file, ensure_ascii=False, indent=2)
        temporaryPaths[path] = temporaryPath
    for path, temporaryPath in temporaryPaths.items():
        replace(temporaryPath, path)


def is_old_users_format(savedUsers):
    """Indica se o conteúdo de users.json está no formato antigo.

    É considerado antigo se tiver a chave 'suspensions' ou se algum usuário
    não tiver o campo 'gender'.

    Args:
        savedUsers: Conteúdo já decodificado do arquivo de usuários.

    Returns:
        True se estiver no formato antigo.
    """
    if not isinstance(savedUsers, dict):
        return False
    savedList = savedUsers.get('users', [])
    hasOldUsers = isinstance(savedList, list) and any(isinstance(user, dict) and 'gender' not in user for user in savedList)
    return 'suspensions' in savedUsers or hasOldUsers


def archive_old_format():
    """Arquiva os arquivos de dados gravados em formato antigo.

    Move a configuração se for não vazia e não tiver 'loan_days', e move os
    usuários se estiverem no formato antigo. Quando qualquer um dos dois é
    movido, o histórico também é, para não ficar referenciando dados que
    deixaram de existir. Deve ser chamada antes de carregar os arquivos.
    """
    savedConfig = read_json(CONFIG_FILE, {})
    savedUsers = read_json(USERS_FILE, {})
    oldFiles = []
    if isinstance(savedConfig, dict) and savedConfig and 'loan_days' not in savedConfig:
        oldFiles.append(CONFIG_FILE)
    if is_old_users_format(savedUsers):
        oldFiles.append(USERS_FILE)
    if oldFiles:
        oldFiles.append(HISTORY_FILE)
    for path in oldFiles:
        if path.exists():
            move_to_unreadable(path, label='Old_Format')
