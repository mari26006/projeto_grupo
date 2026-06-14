PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    amor_proprio INTEGER DEFAULT 4,
    lagrimas INTEGER DEFAULT 60,
    publicacoes_disponivel INTEGER DEFAULT 0,
    publicacoes_resolvido INTEGER DEFAULT 0,
    silenciou_ex INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS slot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    numero INTEGER NOT NULL,
    estado TEXT DEFAULT 'vazio',
    tipo TEXT,
    etapa INTEGER DEFAULT 0,
    construcao_fim TEXT,
    tarefa_fim TEXT,
    tarefa_nome TEXT,
    tarefa_correta INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
