# Museum of Broken Relationships

Projeto final da unidade curricular de Desenvolvimento de Aplicações Web (DAW).

Instituto Politécnico de Setúbal - ESCE

Ano letivo 2025/2026

## Descrição

O Museum of Broken Relationships é um jogo web sobre a recuperação depois do fim de uma relação.

Cada utilizador começa com 4 pontos de Amor-Próprio e deve explorar quatro espaços de cura:

- Baú das Recordações Físicas
- Arquivo Digital
- A Mente e os Pensamentos
- Novos Começos

Em cada espaço, o utilizador toma decisões que podem aumentar ou diminuir o seu Amor-Próprio. O objetivo é concluir todos os momentos e alcançar 100 pontos.

## Funcionalidades

- Registo e login de utilizadores
- Passwords protegidas com hashing
- Sessões de utilizador
- Quatro espaços de cura com diferentes momentos
- Decisões com consequências no Amor-Próprio
- Estados emocionais baseados na pontuação
- Tarefas com temporizador
- Classificação dos dez utilizadores com mais Amor-Próprio
- Tema claro e tema escuro
- Base de dados SQLite

## Tecnologias

- Python 3
- Flask
- SQLite
- Passlib
- HTML5 e templates Jinja
- CSS3
- JavaScript

O código utiliza os conceitos apresentados nos laboratórios de DAW, incluindo HTML semântico, CSS responsivo, manipulação do DOM, JSON, Flask, formulários, SQLite, sessões e hashing de passwords.

## Como executar

### 1. Entrar na pasta do projeto

```bash
cd museum_broken_relationships
```

### 2. Criar um ambiente virtual

```bash
python -m venv venv
```

Ativar no Windows:

```bash
venv\Scripts\activate
```

Ativar no macOS ou Linux:

```bash
source venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Executar a aplicação

```bash
python app.py
```

### 5. Abrir no browser

Aceder a:

```text
http://127.0.0.1:5000
```

As páginas devem ser abertas através do servidor Flask. Não se deve abrir diretamente os ficheiros da pasta `templates`.

## Estrutura do projeto

```text
museum_broken_relationships/
|-- app.py
|-- game.db
|-- requirements.txt
|-- README.md
|-- templates/
|   |-- base.html
|   |-- index.html
|   |-- login.html
|   |-- register.html
|   `-- dashboard.html
`-- static/
    |-- css/
    |   `-- style.css
    |-- img/
    |   |-- branch_landing.gif
    |   |-- fundo.jpeg
    |   |-- fundo_escuro.jpeg
    |   `-- pixel_heart.png
    `-- js/
        |-- jogo.js
        `-- tema.js
```

## Ficheiros principais

- `app.py`: aplicação Flask, rotas, autenticação, regras do jogo e acesso à base de dados.
- `templates/base.html`: estrutura comum das páginas.
- `templates/dashboard.html`: dashboard principal do jogo.
- `static/css/style.css`: apresentação visual e responsividade.
- `static/js/jogo.js`: interações, tarefas, notificações e temporizadores.
- `static/js/tema.js`: alteração e armazenamento do tema visual.
- `game.db`: base de dados SQLite criada automaticamente.

## Base de dados

A aplicação cria automaticamente as tabelas necessárias:

- `user`: guarda os utilizadores e a respetiva pontuação.
- `slot`: guarda o estado dos quatro espaços de cura de cada utilizador.

As passwords nunca são guardadas em texto simples. Os novos registos utilizam hashing através da biblioteca Passlib.
