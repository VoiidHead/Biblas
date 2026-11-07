import hashlib
import hmac
import secrets
from dataclasses import dataclass, fields

GENDERS = {"male": "masculino", "female": "feminino", "other": "outro"}


@dataclass
class Title:
    id: int
    name: str
    author: str
    publisher: str
    genre: str
    pages_count: int
    year: int


@dataclass
class Copy:
    id: int
    title_id: int


SCRYPT_PARAMS = {"n": 2 ** 14, "r": 8, "p": 1}


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, **SCRYPT_PARAMS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    saltHex, digestHex = stored.split("$")
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(saltHex), **SCRYPT_PARAMS)
    return hmac.compare_digest(digest, bytes.fromhex(digestHex))


class User:
    def __init__(self, id: int, name: str, gender: str, email: str, cpf: str, password_hash: str,
                 suspended_until: str | None = None, faults: int = 0):
        self.id = id
        self.name = name
        self.gender = gender
        self.email = email
        self.cpf = cpf
        self.suspended_until = suspended_until
        self.faults = faults  # devoluções com atraso
        self.__password_hash = password_hash

    def check_password(self, password: str):
        return verify_password(password, self.__password_hash)

    def change_password(self, newPassword: str):
        self.__password_hash = hash_password(newPassword)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'email': self.email,
            'cpf': self.cpf,
            'password_hash': self.__password_hash,
            'suspended_until': self.suspended_until,
            'faults': self.faults,
        }


@dataclass
class Loan:
    copy_id: int
    title_id: int
    title_name: str
    user_id: int
    loan_date: str
    due_date: str
    return_date: str | None = None
    was_removed: bool = False
    fine_cents: int = 0
    fine_paid: bool = False


def build_from_dict(dataClass, data: dict):
    fieldNames = {field.name for field in fields(dataClass)}
    return dataClass(**{key: value for key, value in data.items() if key in fieldNames})
