"""Modelos de dados do sistema: títulos, exemplares, usuários e empréstimos.

Datas são guardadas como texto no formato ISO (AAAA-MM-DD) e valores
monetários como inteiros em centavos, para serializar direto em JSON.
"""

import hashlib
import hmac
import secrets
from dataclasses import dataclass, fields

GENDERS = {"male": "masculino", "female": "feminino", "other": "outro"}


@dataclass
class Title:
    """Obra do acervo (um livro, independente de quantas cópias existam).

    Attributes:
        id: Identificador único do título.
        name: Nome do livro.
        author: Nome do autor.
        publisher: Nome da editora.
        genre: Gênero literário.
        pages_count: Número de páginas.
        year: Ano de lançamento (negativo significa AEC).
    """
    id: int
    name: str
    author: str
    publisher: str
    genre: str
    pages_count: int
    year: int


@dataclass
class Copy:
    """Exemplar físico de um título, que é o que de fato é emprestado.

    Attributes:
        id: Identificador único do exemplar.
        title_id: ID do título ao qual o exemplar pertence.
    """
    id: int
    title_id: int


SCRYPT_PARAMS = {"n": 2 ** 14, "r": 8, "p": 1}


def hash_password(password: str) -> str:
    """Gera o hash de uma senha com sal aleatório, usando scrypt.

    Args:
        password: Senha em texto puro.

    Returns:
        Texto no formato 'sal$hash', ambos em hexadecimal. Como o sal é
        novo a cada chamada, a mesma senha gera textos diferentes.
    """
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, **SCRYPT_PARAMS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Confere uma senha digitada contra um hash gerado por hash_password.

    A comparação usa hmac.compare_digest, que leva o mesmo tempo
    independente de onde os valores diferem.

    Args:
        password: Senha em texto puro a conferir.
        stored: Hash guardado, no formato 'sal$hash'.

    Returns:
        True se a senha corresponder ao hash.
    """
    saltHex, digestHex = stored.split("$")
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(saltHex), **SCRYPT_PARAMS)
    return hmac.compare_digest(digest, bytes.fromhex(digestHex))


class User:
    """Usuário da biblioteca (quem pega livros emprestados).

    A senha nunca é guardada em texto puro: o usuário só carrega o hash dela
    (ver hash_password), que fica em um atributo privado e é gravado em
    users.json.

    Attributes:
        id: Identificador único do usuário.
        name: Nome de usuário (único, sem diferenciar acento ou maiúsculas).
        gender: Chave de GENDERS ('male', 'female' ou 'other').
        email: E-mail do usuário (único).
        cpf: CPF apenas com dígitos (único).
        suspended_until: Data ISO do fim da suspensão, ou None.
        faults: Quantidade de devoluções com atraso.
    """
    def __init__(self, id: int, name: str, gender: str, email: str, cpf: str, password_hash: str,
                 suspended_until: str | None = None, faults: int = 0):
        """Cria um usuário.

        Args:
            id: Identificador único.
            name: Nome de usuário.
            gender: Chave de GENDERS.
            email: E-mail.
            cpf: CPF apenas com dígitos.
            password_hash: Hash da senha, gerado por hash_password. Quem cria
                o usuário a partir de uma senha digitada deve chamar
                hash_password antes.
            suspended_until: Data ISO do fim da suspensão, se houver.
            faults: Número de devoluções com atraso já registradas.
        """
        self.id = id
        self.name = name
        self.gender = gender
        self.email = email
        self.cpf = cpf
        self.suspended_until = suspended_until
        self.faults = faults  # devoluções com atraso
        self.__password_hash = password_hash

    def check_password(self, password: str):
        """Indica se a senha informada é a do usuário.

        Args:
            password: Senha a conferir.

        Returns:
            True se a senha corresponder ao hash guardado, False caso contrário.
        """
        return verify_password(password, self.__password_hash)

    def change_password(self, newPassword: str):
        """Substitui a senha do usuário.

        Args:
            newPassword: Nova senha em texto puro, que é guardada como hash.
        """
        self.__password_hash = hash_password(newPassword)

    def to_dict(self):
        """Converte o usuário em dicionário pronto para JSON.

        Ao contrário dos dataclasses, precisa ser explícito porque a senha é um
        atributo privado e não aparece em asdict().

        Returns:
            Dicionário com todos os campos, incluindo o hash da senha em 'password_hash'.
        """
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
    """Registro de um empréstimo, aberto ou já encerrado.

    Guarda o nome do título (title_name) para o histórico continuar legível
    mesmo que o exemplar seja removido do acervo depois.

    Attributes:
        copy_id: ID do exemplar emprestado.
        title_id: ID do título do exemplar.
        title_name: Nome do título no momento do empréstimo.
        user_id: ID do usuário que pegou o livro.
        loan_date: Data ISO do empréstimo.
        due_date: Data ISO máxima de devolução.
        return_date: Data ISO em que o empréstimo foi encerrado, ou None se
            ainda estiver em andamento.
        was_removed: True se o empréstimo foi encerrado porque o exemplar foi
            removido do acervo, e não por devolução.
        fine_cents: Multa aplicada, em centavos (0 se não houve).
        fine_paid: True se a multa já foi quitada.
    """
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
    """Cria uma instância de dataclass a partir de um dicionário.

    Chaves que não correspondem a campos do dataclass são ignoradas, o que
    permite ler arquivos gravados por versões com campos a mais ou a menos.

    Args:
        dataClass: Classe decorada com @dataclass.
        data: Dicionário com os valores dos campos.

    Returns:
        Instância de dataClass.

    Raises:
        TypeError: Se faltar algum campo obrigatório.
    """
    fieldNames = {field.name for field in fields(dataClass)}
    return dataClass(**{key: value for key, value in data.items() if key in fieldNames})
