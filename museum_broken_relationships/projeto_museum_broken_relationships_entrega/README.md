# Museum of Broken Relationships

Projeto final de Desenvolvimento de Aplicações Web do Instituto Politécnico de Setúbal — ESCE, ano letivo 2025/2026.

## Sobre o jogo

O *Museum of Broken Relationships* é um jogo web de gestão emocional inspirado na recuperação após o fim de uma relação.

Cada utilizador começa com:

- `4` pontos de Amor-Próprio;
- `60` Lágrimas.

As Lágrimas são utilizadas para preparar espaços e tomar decisões. As decisões alteram o Amor-Próprio e respostas corretas permitem recuperar Lágrimas. O objetivo é concluir os quatro espaços de cura e alcançar 100 pontos de Amor-Próprio.

Se o Amor-Próprio ou as Lágrimas chegarem a zero, o jogador pode reiniciar a jornada.

## Funcionalidades

- Registo, login, logout e sessões com Flask-Login;
- Passwords protegidas com Passlib;
- Dois recursos: Amor-Próprio e Lágrimas;
- Quatro espaços com custos e tempos de preparação;
- Preparação dos espaços com duração de 1 minuto;
- Tarefas com duração de 5 minutos e recolha manual;
- Estados emocionais baseados no Amor-Próprio;
- Leaderboard dos dez melhores utilizadores;
- Tema claro e escuro persistente;
- Layout responsivo para desktop, tablet e mobile;
- API JSON validada no servidor;
- Testes automatizados dos fluxos principais.

## Arquitetura MVC

- **Model:** `models/game_model.py` — base de dados, validações e regras do jogo.
- **View:** `templates/` e `static/` — templates Jinja, CSS, JavaScript e imagens.
- **Controller:** `controllers/main_controller.py` — rotas, autenticação e respostas HTTP/JSON.
- **Inicialização:** `app.py` — configuração da aplicação e registo do Controller.

## Tecnologias

- Python 3;
- Flask 3.1;
- Flask-Login;
- SQLite;
- Passlib;
- HTML5, Jinja, CSS3 e JavaScript.

## Instalação

```bash
cd museum_broken_relationships
python -m venv venv
```

Ativar o ambiente virtual no Windows:

```bash
venv\Scripts\activate
```

Ativar no macOS ou Linux:

```bash
source venv/bin/activate
```

Instalar e executar:

```bash
pip install -r requirements.txt
python app.py
```

A aplicação fica disponível em:

```text
http://127.0.0.1:5000
```

A base de dados `game.db` é criada automaticamente na primeira execução.

## Testes

```bash
python -m unittest discover -s tests -v
```

## Estrutura

```text
museum_broken_relationships/
|-- app.py
|-- requirements.txt
|-- README.md
|-- api_documentacao.md
|-- base_dados.sql
|-- controllers/
|   `-- main_controller.py
|-- models/
|   `-- game_model.py
|-- templates/
|   |-- base.html
|   |-- index.html
|   |-- login.html
|   |-- register.html
|   `-- dashboard.html
|-- static/
|   |-- css/style.css
|   |-- js/jogo.js
|   |-- js/tema.js
|   `-- img/
|-- tests/
|   `-- test_app.py
|-- RELATORIO_TECNICO_REVISTO.md
|-- relatorio_museum_broken_relationships_alinhado.docx
`-- relatorio_museum_broken_relationships_final.pdf
```

## Documentação

- `api_documentacao.md`: rotas, parâmetros e respostas da API;
- `base_dados.sql`: esquema da base de dados;
- `RELATORIO_TECNICO_REVISTO.md`: versão editável do relatório;
- `relatorio_museum_broken_relationships_final.pdf`: relatório final.
