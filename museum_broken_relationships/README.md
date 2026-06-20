# Museum of Broken Relationships

Projeto final de Desenvolvimento de Aplicações Web.

## Tema

O jogo é sobre recuperar de uma relação terminada. O jogador gere espaços de cura dentro do museu e tenta aumentar o Amor-Próprio.

## Funcionalidades

- Registo com username, email e password
- Login e logout
- Sessões com Flask-Login
- Base de dados SQLite
- Dois recursos principais:
  - Amor-Próprio
  - Lágrimas
- Quatro espaços/construções:
  - Baú das Recordações Físicas
  - Arquivo Digital
  - A Mente e os Pensamentos
  - Novos Começos
- Cada espaço tem custo e tempo de preparação
- Cada espaço tem tarefas/decisões
- As tarefas demoram tempo
- O jogador recolhe manualmente a tarefa concluída
- Dashboard com recursos, slots, leaderboard e histórico
- JavaScript com Fetch API para comunicar com o backend
- Tema claro/escuro guardado com localStorage

## Tecnologias

- Python
- Flask
- Flask-Login
- SQLite
- Passlib
- HTML
- CSS
- JavaScript

## Como executar

Instalar dependências:

```bash
pip install -r requirements.txt
```

Executar:

```bash
python app.py
```

Abrir no browser:

```text
http://127.0.0.1:8080
```

## Estrutura MVC

- Model: `models/game_model.py`
- View: `templates/` e `static/`
- Controller: `controllers/main_controller.py`
- Entrada da aplicação: `app.py`

## Entregáveis

- `README.md`
- `api_documentacao.md`
- `base_dados.sql`
- `relatorio_museum_broken_relationships_final.pdf`
- `projeto_museum_broken_relationships.zip`
