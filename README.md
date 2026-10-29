# 📚 Biblas

Sistema de gerenciamento de biblioteca para o terminal, escrito em Python.

Este é um projeto pessoal de estudo, feito para praticar Python. Ele também é uma
competição com o meu colega [Augusto](https://github.com/GUT-R/biblioteca).

Com ele dá para cadastrar livros e usuários, registrar empréstimos e devoluções,
consultar o acervo e aplicar punições por atraso (suspensão ou multa), tudo por
um menu em linha de comando. Os dados ficam salvos em arquivos JSON, então não
há banco de dados nem dependências para instalar.

## ✨ Funcionalidades

**Acervo**
- Adicionar livros com várias cópias de uma vez. Cada cópia (exemplar) recebe um ID próprio.
- Reconhecer títulos repetidos (mesmo nome, autor, editora, gênero, páginas e ano, sem diferenciar acentos ou maiúsculas) e juntar os novos exemplares ao título já existente.
- Remover um exemplar, inclusive emprestado, com confirmação.
- Buscar livros por ID do exemplar, nome, autor, editora ou gênero, combinando quantos critérios quiser.
- Ver o acervo completo em tabela, com exemplares disponíveis e emprestados.

**Usuários**
- Cadastro com nome de usuário, gênero, e-mail, CPF (com validação dos dígitos verificadores) e senha, que é guardada como hash (scrypt com sal), nunca em texto puro.
- Nome, e-mail e CPF são únicos. As mensagens do sistema concordam com o gênero do usuário (suspensa/suspenso, banida/banido).
- Editar qualquer dado, quitar multas pendentes e zerar faltas.
- Consultar a ficha completa, com histórico de empréstimos.

**Empréstimos**
- O empréstimo exige o ID do exemplar e o nome e a senha do usuário.
- É bloqueado se o usuário estiver banido, suspenso, com livro atrasado ou no limite de empréstimos.
- Na devolução com atraso, o sistema aplica a punição configurada.
- Histórico completo, inclusive de exemplares removidos depois.

**Configurações** (ajustáveis pelo próprio programa)

| Opção | Padrão |
|---|---|
| Prazo de devolução | 14 dias |
| Máximo de empréstimos por usuário | 5 |
| Punição por atraso | Suspensão (1 dia por dia de atraso, acumulativa) |
| Valor da multa, se a punição for multa | R$ 1,00 por dia de atraso |
| Banimento | Desativado |
| Faltas para banir, se o banimento estiver ativo | 3 |

## 🚀 Como executar

**Necessário:**
- Python 3.10+

A partir da pasta que contém o projeto:

```bash
python biblas
```

Ou, de dentro da pasta do projeto:

```bash
python .
```

> Não use `python -m biblas`: a pasta `modules` precisa estar no caminho de busca do Python, e isso só acontece ao executar a pasta diretamente.

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

Digite o número da opção e siga as perguntas. Enquanto o acervo está vazio, o menu mostra só as opções que não dependem de exemplares: adicionar livro, cadastrar, editar e consultar usuários, ver a lista de usuários e configurações.

## 🗂️ Estrutura do projeto

```
biblas/
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

- **Entrada e saída** (`inputs`, `menus`, `queries`) falam com o operador.
- **Regras** (`rules`) só calculam e decidem, sem ler teclado nem gravar em disco.
- **Serviços** (`services/`) juntam tudo para executar cada operação.
- **Estado e armazenamento** (`state`, `storage`) cuidam dos dados.

**Ordem de leitura**:  
Caso queira ler o projeto, essa é uma ordem de leitura baseada em definições (um arquivo define algo do outro):
- [textutils](modules/textutils.py)
- [models](modules/models.py)
- [storage](modules/storage.py)
- [state](modules/state.py)
- [rules](modules/rules.py)
- [inputs](modules/inputs.py)
- [books](modules/services/books.py)
- [users](modules/services/users.py)
- [loans](modules/services/loans.py)
- [settings](modules/services/settings.py)
- [queries](modules/queries.py)
- [menus](modules/menus.py)
- [main](__main__.py)
  
*`obs: As docstrings foram geradas pelo Claude, não feitas por mim`

## 💾 Onde os dados ficam

Na primeira gravação, o programa cria a pasta `data/` ao lado de `modules/`:

| Arquivo | Conteúdo |
|---|---|
| `collection.json` | Títulos e exemplares |
| `users.json` | Usuários (com o hash das senhas) |
| `config.json` | Configurações |
| `history.log` | Histórico de empréstimos (o conteúdo também é JSON) |

Se algum arquivo estiver corrompido ou em formato antigo, ele não é apagado: é movido para `data/unreadable/` com a data e a hora no nome, e o programa continua com dados vazios para aquele arquivo.

Para começar do zero, basta apagar a pasta `data/`.

## ⚠️ Limitações conhecidas

Como é um projeto de estudo, algumas coisas são simplificadas de propósito:

- **Não há recuperação de senha.** Como só o hash é guardado, quem esquecer a senha precisa que alguém defina outra em *Editar usuário*.
- Os dados ficam em arquivos locais, e o programa não foi pensado para ser usado por várias pessoas ao mesmo tempo.
- Não há testes automatizados.

## 🤓 Curiosidade

**Biblas** é um apelido que eu e um amigo damos para a Biblioteca Central Sebastião Fernandes (biblioteca do IFRN-CNAT).
