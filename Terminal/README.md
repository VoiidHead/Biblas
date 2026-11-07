# 📚 Biblas — versão do terminal

Sistema de gerenciamento de biblioteca para o terminal, escrito em Python. Para a visão geral do projeto e as funcionalidades, veja o [README principal](../README.md).

Tudo funciona por um menu em linha de comando, e os dados ficam salvos em arquivos JSON, então não há banco de dados nem dependências para instalar.

## 📦 Dependências

Python 3.10+

A única biblioteca de terceiros, o [Tabulate](https://github.com/astanin/python-tabulate) (usado para desenhar as tabelas), já vem embutida em [`modules/tabulate/`](modules/tabulate/), então não precisa de instalação com pip. O resto usa apenas a biblioteca padrão do Python (`json`, `hashlib`, `getpass`, `dataclasses`, `datetime`, entre outros).

## 🚀 Como executar

A partir da pasta que contém o projeto:

```bash
python Terminal
```

Ou, de dentro da pasta `Terminal`:

```bash
python .
```

> Não use `python -m Terminal`: a pasta `modules` precisa estar no caminho de busca do Python, e isso só acontece ao executar a pasta diretamente.

## 🖥️ Como usar

O menu principal aparece em loop:

```
1 - Empréstimo
2 - Devolução
3 - Cadastro de usuário
4 - Editar usuário
5 - Adicionar livro ao acervo
6 - Remover exemplar do acervo
7 - Buscar livro
8 - Consultar usuário
9 - Ver acervo
10 - Ver lista de usuários
* - Configurações
/ - Fechar o programa
```

Digite o número da opção e siga as perguntas. As senhas são lidas sem aparecer na tela. Enquanto o acervo está vazio, o menu mostra só as opções que não dependem de exemplares: adicionar livro, cadastrar, editar e consultar usuários, ver a lista de usuários e configurações.

## 🗂️ Estrutura do projeto

```
Terminal/
├── __main__.py            # Ponto de entrada: loop do menu principal
└── modules/
    ├── menus.py           # Menus e ligação de cada opção ao serviço
    ├── inputs.py          # Leitura e validação do que o operador digita
    ├── queries.py         # Consultas e tabelas exibidas na tela
    ├── rules.py           # Regras de negócio (atrasos, multas, banimento, CPF)
    ├── models.py          # Classes: Title, Copy, User e Loan
    ├── state.py           # Estado em memória, carregado do disco ao iniciar
    ├── storage.py         # Leitura e gravação dos arquivos JSON
    ├── textutils.py       # Normalização de texto e formatação de dinheiro
    ├── services/
    │   ├── books.py       # Adicionar livros e remover exemplares
    │   ├── loans.py       # Empréstimo e devolução
    │   ├── users.py       # Cadastro e edição de usuários
    │   └── settings.py    # Menu de configurações
    └── tabulate/          # Biblioteca Tabulate embutida no projeto para desenhar tabelas
```

A ideia foi separar as responsabilidades em camadas:

- **Entrada e saída** (`inputs.py`, `menus.py`, `queries.py`) falam com o operador.
- **Regras** (`rules.py`) só calculam e decidem, sem ler teclado nem gravar em disco.
- **Serviços** (`services/`) juntam tudo para executar cada operação. Eles também fazem as perguntas ao operador e imprimem as mensagens.
- **Estado e armazenamento** (`state.py`, `storage.py`) cuidam dos dados.

## 📖 Ordem de leitura

Caso queira ler o projeto, essa é uma ordem baseada em definições (um arquivo define algo que os seguintes usam):

1. [textutils](modules/textutils.py)
2. [models](modules/models.py)
3. [storage](modules/storage.py)
4. [state](modules/state.py)
5. [rules](modules/rules.py)
6. [inputs](modules/inputs.py)
7. [loans](modules/services/loans.py)
8. [books](modules/services/books.py)
9. [users](modules/services/users.py)
10. [settings](modules/services/settings.py)
11. [queries](modules/queries.py)
12. [menus](modules/menus.py)
13. [main](__main__.py)
