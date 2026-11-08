# 📚 Biblas — versão GUI (Flet)

Versão do Biblas com interface gráfica, feita com [Flet](https://flet.dev). Para a visão geral do projeto e as funcionalidades, veja o [README principal](../README.md).

## 📦 Dependências

- Python 3.10+  
- Flet 1.x

Instalação:

```bash
pip install flet
```

Todo o resto usa apenas a biblioteca padrão do Python. As tabelas são desenhadas pelo próprio Flet.

> Dica: depois de instalar, rode `pip show flet` para ver a versão exata e, se quiser, fixá-la em um `requirements.txt` (por exemplo, `flet==<versão>`).

## 🚀 Como executar

A partir da pasta que contém o projeto:

```bash
python GUI                   # abre uma janela
python GUI/main_browser.py   # abre no navegador, em http://localhost:8000
```

Ou, de dentro da pasta `GUI`:

```bash
python .                     # janela
python main_browser.py       # navegador
```

> Não use `python -m GUI`: a pasta `modules` precisa estar no caminho de busca do Python, e isso só acontece ao executar a pasta (ou o arquivo) diretamente.

## 🖥️ Como usar

A janela tem uma barra lateral com cinco telas. Dá para navegar com o mouse ou com os atalhos `Ctrl+1` a `Ctrl+5`:

| Atalho | Tela | O que faz |
|---|---|---|
| `Ctrl+1` | Acervo | Busca com vários critérios, detalhes de cada título com histórico de empréstimos e remoção de exemplares |
| `Ctrl+2` | Adicionar livro | Formulário para cadastrar um título com várias cópias |
| `Ctrl+3` | Empréstimos | Formulários de empréstimo e de devolução |
| `Ctrl+4` | Usuários | Lista, cadastro, edição, ficha com histórico, quitação de multas e zerar faltas |
| `Ctrl+5` | Configurações | Prazo, limite, punição, multa, banimento e tema |

Os formulários validam o que é digitado enquanto você escreve: o CPF e os valores em reais ganham *input masks* automaticamente, os campos numéricos só aceitam dígitos, e os erros aparecem logo abaixo de cada campo. Cada tela é montada de novo a cada navegação, então sempre mostra os dados atuais.

Nas configurações, o tema pode ser *Claro* ou *Escuro* (e é mostrado como prévia antes de salvar), e ao mexer no banimento, o programa mostra quantos usuários seriam afetados.

## 🗂️ Estrutura do projeto

```
GUI/
├── __main__.py            # Ponto de entrada: abre a janela do aplicativo
├── main_browser.py        # Ponto de entrada alternativo: abre no navegador (porta 8000)
└── modules/
    ├── errors.py          # BiblasError, o erro que as regras levantam e a tela mostra
    ├── textutils.py       # Normalização de texto e formatação de dinheiro, datas e CPF
    ├── models.py          # Classes: Title, Copy, User e Loan (e o hash das senhas)
    ├── storage.py         # Leitura e gravação dos arquivos JSON
    ├── state.py           # Estado em memória, carregado do disco ao iniciar
    ├── rules.py           # Regras de negócio (atrasos, multas, banimento, CPF)
    ├── masks.py           # Máscaras aplicadas enquanto se digita (CPF, dinheiro, dígitos)
    ├── validators.py      # Transforma o texto digitado em valores válidos
    ├── queries.py         # Consultas: devolvem linhas e detalhes, sem imprimir nada
    ├── services/
    │   ├── loans.py       # Empréstimo e devolução
    │   ├── books.py       # Adicionar livros e remover exemplares
    │   ├── users.py       # Cadastro e edição de usuários
    │   └── settings.py    # Salvar configurações
    └── ui/
        ├── app.py         # Janela, barra lateral, atalhos e navegação entre telas
        ├── components.py  # Peças reutilizáveis: diálogos, botões, tabelas, títulos
        ├── fields.py      # Campo com validação e máscara (ValidatedField)
        ├── icons/         # Ícones do aplicativo e da aba do navegador
        └── views/
            ├── collection.py  # Tela do acervo
            ├── add_book.py    # Tela de adicionar livro
            ├── loans.py       # Tela de empréstimos e devoluções
            ├── users.py       # Telas de usuários
            └── settings.py    # Tela de configurações
```

O projeto é dividido em camadas, e a camada de entrada e saída é o pacote `ui/`:

- **Interface** (`ui/`) desenha as telas e lê o que é digitado.
- **Validação** (`masks.py`, `validators.py`) ajusta e confere o texto antes de ele chegar às regras.
- **Regras** (`rules.py`) só calculam e decidem.
- **Serviços** (`services/`) executam cada operação e **não** leem teclado nem imprimem: se algo estiver errado, levantam um `BiblasError`.
- **Estado e armazenamento** (`state.py`, `storage.py`) cuidam dos dados.

## 📖 Ordem de leitura

Essa é uma ordem baseada em definições (um arquivo define algo que o seguinte usa), com a interface no fim:

1. [textutils](modules/textutils.py)
2. [errors](modules/errors.py)
3. [models](modules/models.py)
4. [storage](modules/storage.py)
5. [state](modules/state.py)
6. [rules](modules/rules.py)
7. [masks](modules/masks.py)
8. [validators](modules/validators.py)
9. [loans (service)](modules/services/loans.py)
10. [books](modules/services/books.py)
11. [users](modules/services/users.py)
12. [settings](modules/services/settings.py)
13. [queries](modules/queries.py)
14. [components](modules/ui/components.py)
15. [fields](modules/ui/fields.py)
16. [add_book](modules/ui/views/add_book.py)
17. [collection](modules/ui/views/collection.py)
18. [loans (view)](modules/ui/views/loans.py)
19. [users](modules/ui/views/users.py)
20. [settings](modules/ui/views/settings.py)
21. [app](modules/ui/app.py)
22. [main](__main__.py) / [main_browser](main_browser.py)
