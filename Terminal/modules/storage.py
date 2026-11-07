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
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    name = '-'.join(part for part in (path.stem, label, timestamp) if part)
    targetDir = UNREADABLE_DIR / path.stem
    targetDir.mkdir(parents=True, exist_ok=True)
    targetPath = targetDir / f"{name}.bak"
    replace(path, targetPath)
    print(f"*{path.name} não pôde ser lido. Arquivo movido para {targetPath.relative_to(DATA_DIR.parent)}")
    return targetPath


def read_json(path: Path, default):
    try:
        with open(path, encoding='utf-8') as file:
            return load(file)
    except FileNotFoundError:
        return default
    except (JSONDecodeError, UnicodeDecodeError):
        move_to_unreadable(path)
        return default


def load_file(path: Path, default, parse):
    try:
        return parse(read_json(path, default))
    except (AttributeError, TypeError, ValueError):
        move_to_unreadable(path, label='Invalid_Format')
        return parse(default)


def write_json_files(contents: dict):
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
    if not isinstance(savedUsers, dict):
        return False
    savedList = savedUsers.get('users', [])
    hasOldUsers = isinstance(savedList, list) and any(isinstance(user, dict) and 'gender' not in user for user in savedList)
    return 'suspensions' in savedUsers or hasOldUsers


def archive_old_format():
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
