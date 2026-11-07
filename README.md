# 📚 Biblas

Sistema de gerenciamento de biblioteca escrito em Python, em **duas versões**: uma para o terminal e outra com interface gráfica feita com [Flet](https://flet.dev).

Este é um projeto pessoal de estudo, feito para praticar Python. Ele também é uma
competição com o meu colega [Augusto](https://github.com/GUT-R/biblioteca).

Com ele dá para cadastrar livros e usuários, registrar empréstimos e devoluções,
consultar o acervo e aplicar punições por atraso (suspensão ou multa). Os dados ficam
salvos em arquivos JSON, então não há banco de dados.

## 🧭 As duas versões

Ao terminar nossos códigos que rodavam no terminal, Augusto e eu decidimos criar interfaces gráficas.  
Esse repostório possui duas versões diferentes do projeto, a versão inicial feita para rodar no terminal e a versão com interface gráfica (GUI)

| | [Terminal](Terminal/) | [GUI](GUI/) |
|---|---|---|
| Interface | Menu em linha de comando | Janela com barra lateral ou no navegador |
| Dependências | Python 3.10+ | Python 3.10+<br>Flet 1.x|
| Extras | — | Tema claro/escuro, validação e *input masks* enquanto se digita, atalhos de navegação |

## ✨ Funcionalidades

As duas versões fazem a mesma coisa:

**Acervo**
- Adicionar livros com várias cópias de uma vez. Cada cópia (exemplar) recebe um ID próprio.
- Reconhecer títulos repetidos (mesmo nome, autor, editora, gênero, páginas e ano, sem diferenciar acentos ou maiúsculas) e juntar os novos exemplares ao título já existente.
- Remover um exemplar, inclusive emprestado, com confirmação.
- Buscar livros por ID do exemplar, nome, autor, editora ou gênero, combinando quantos critérios quiser.
- Ver o acervo completo em tabela, com exemplares disponíveis e emprestados.

**Usuários**
- Cadastro com nome de usuário, gênero, e-mail, CPF (com validação dos dígitos verificadores) e senha, que é guardada como *hash* (*scrypt* com sal), nunca em texto puro.
- Nome, e-mail e CPF são únicos. As mensagens do sistema concordam com o gênero do usuário (suspenso(a), banido(a)).
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
| Punição por atraso | Suspensão (1 dia por dia de atraso, cumulativa) |
| Valor da multa, se a punição for multa | R$ 1,00 por dia de atraso |
| Banimento | Desativado |
| Faltas para banir, se o banimento estiver ativo | 3 |
| Tema *(só na versão GUI)* | Sistema |

## 💾 Onde os dados ficam

Na primeira gravação, cada versão cria a pasta `data/` ao lado de `modules/`:

| Arquivo | Conteúdo |
|---|---|
| `collection.json` | Títulos e exemplares |
| `users.json` | Usuários (com o *hash* das senhas) |
| `config.json` | Configurações |
| `history.log` | Histórico de empréstimos (o conteúdo também é JSON) |

Se algum arquivo estiver corrompido ou em formato antigo, ele não é apagado: é movido para `data/unreadable/` com a data e a hora no nome, e o programa continua com dados vazios para aquele arquivo.

Para começar do zero, basta apagar a pasta `data/` da versão desejada.

## ⚠️ Limitações conhecidas

Como é um projeto de estudo, algumas coisas são simplificadas:

- Os dados ficam em arquivos locais, e o programa não foi pensado para ser usado por várias pessoas ao mesmo tempo.
- Não há testes automatizados.

## 🤓 Curiosidade

**Biblas** é um apelido que eu e um amigo damos para a Biblioteca Central Sebastião Fernandes (biblioteca do IFRN-CNAT).
