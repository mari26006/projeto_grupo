import sqlite3
import os
import re
from datetime import datetime
from flask_login import UserMixin
from passlib.hash import pbkdf2_sha256 as hasher
from passlib.hash import hex_sha256

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game.db')
AMOR_PROPRIO_INICIAL = 4
LAGRIMAS_INICIAIS = 60
CUSTO_DECISAO = 1
BONUS_LAGRIMAS_RESPOSTA_CORRETA = 2


class User(UserMixin):
    """Representa o utilizador autenticado para o Flask-Login."""

    def __init__(self, row):
        self.id = row['id']
        self.username = row['username']
        self.email = row['email']
        self.amor_proprio = row['amor_proprio']
        self.lagrimas = row['lagrimas']
        self.created_at = row['created_at']

# =====================
# BASE DE DADOS
# =====================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
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

    ''')
    conn.commit()

    # Ajuste de esquema para bases de dados existentes
    c.execute("PRAGMA table_info(slot)")
    columns = [row['name'] for row in c.fetchall()]
    if 'etapa' not in columns:
        c.execute('ALTER TABLE slot ADD COLUMN etapa INTEGER DEFAULT 0')
        conn.commit()

    if 'tarefa_correta' not in columns:
        c.execute('ALTER TABLE slot ADD COLUMN tarefa_correta INTEGER DEFAULT 0')
        conn.commit()

    if 'construcao_fim' not in columns:
        c.execute('ALTER TABLE slot ADD COLUMN construcao_fim TEXT')
        conn.commit()

    c.execute("PRAGMA table_info(user)")
    user_columns = [row['name'] for row in c.fetchall()]
    if 'lagrimas' not in user_columns:
        c.execute(f'ALTER TABLE user ADD COLUMN lagrimas INTEGER DEFAULT {LAGRIMAS_INICIAIS}')
        conn.commit()
    if 'publicacoes_disponivel' not in user_columns:
        c.execute('ALTER TABLE user ADD COLUMN publicacoes_disponivel INTEGER DEFAULT 0')
        conn.commit()
    if 'publicacoes_resolvido' not in user_columns:
        c.execute('ALTER TABLE user ADD COLUMN publicacoes_resolvido INTEGER DEFAULT 0')
        conn.commit()
    if 'silenciou_ex' not in user_columns:
        c.execute('ALTER TABLE user ADD COLUMN silenciou_ex INTEGER DEFAULT 0')
        conn.commit()

    conn.close()


def user_exists(conn, username, email):
    return conn.execute(
        'SELECT id FROM user WHERE username = ? OR email = ?',
        (username, email)
    ).fetchone()


def create_user(conn, username, email, password_hash):
    try:
        cursor = conn.execute(
            'INSERT INTO user (username, email, password, amor_proprio, lagrimas) VALUES (?, ?, ?, ?, ?)',
            (username, email, password_hash, AMOR_PROPRIO_INICIAL, LAGRIMAS_INICIAIS)
        )
    except sqlite3.IntegrityError:
        conn.rollback()
        return None
    user_id = cursor.lastrowid
    for numero, tipo in SLOT_TIPOS.items():
        conn.execute(
            'INSERT INTO slot (user_id, numero, tipo, etapa) VALUES (?, ?, ?, ?)',
            (user_id, numero, tipo, 0)
        )
    conn.commit()
    return user_id


def get_user_by_username(conn, username):
    return conn.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()


def get_user_by_id(conn, user_id):
    return conn.execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()


def get_login_user(user_id):
    conn = get_db()
    row = get_user_by_id(conn, user_id)
    conn.close()
    return User(row) if row else None


def update_user_password(conn, user_id, password_hash):
    conn.execute('UPDATE user SET password = ? WHERE id = ?', (password_hash, user_id))
    conn.commit()


def get_slots_by_user(conn, user_id):
    return conn.execute(
        'SELECT * FROM slot WHERE user_id = ? ORDER BY numero',
        (user_id,)
    ).fetchall()


def get_top_users(conn, limit=10):
    return conn.execute(
        'SELECT * FROM user ORDER BY amor_proprio DESC LIMIT ?',
        (limit,)
    ).fetchall()


def get_slot_by_user_and_number(conn, user_id, numero):
    return conn.execute(
        'SELECT * FROM slot WHERE user_id = ? AND numero = ?',
        (user_id, numero)
    ).fetchone()


def get_slot_by_id(conn, slot_id):
    return conn.execute('SELECT * FROM slot WHERE id = ?', (slot_id,)).fetchone()


def start_slot_build(conn, slot_id, user_id, tears_after_cost, build_end):
    conn.execute('UPDATE user SET lagrimas = ? WHERE id = ?', (tears_after_cost, user_id))
    conn.execute(
        'UPDATE slot SET estado = ?, etapa = ?, construcao_fim = ?, tarefa_correta = ? WHERE id = ?',
        ('construindo', 1, build_end, 0, slot_id)
    )
    conn.commit()


def finish_slot_build(conn, slot_id):
    conn.execute(
        'UPDATE slot SET estado = ?, construcao_fim = NULL WHERE id = ?',
        ('ativo', slot_id)
    )
    conn.commit()


def start_slot_task(conn, slot_id, user_id, novo_amor, novas_lagrimas, tarefa_nome, tarefa_fim, resposta_correta):
    conn.execute(
        'UPDATE user SET amor_proprio = ?, lagrimas = ? WHERE id = ?',
        (novo_amor, novas_lagrimas, user_id)
    )
    conn.execute(
        'UPDATE slot SET estado = ?, tarefa_nome = ?, tarefa_fim = ?, tarefa_correta = ? WHERE id = ?',
        ('processando', tarefa_nome, tarefa_fim, 1 if resposta_correta else 0, slot_id)
    )
    conn.commit()


def mark_slot_completed(conn, slot_id):
    conn.execute('UPDATE slot SET estado = ? WHERE id = ?', ('concluida', slot_id))
    conn.commit()


def finalize_slot(conn, slot_id):
    conn.execute(
        'UPDATE slot SET estado = ?, tarefa_nome = NULL, tarefa_fim = NULL, tarefa_correta = 0 WHERE id = ?',
        ('finalizado', slot_id)
    )


def advance_slot(conn, slot_id, next_stage):
    conn.execute(
        'UPDATE slot SET estado = ?, tarefa_nome = NULL, tarefa_fim = NULL, etapa = ?, tarefa_correta = 0 WHERE id = ?',
        ('ativo', next_stage, slot_id)
    )


def retry_slot(conn, slot_id):
    conn.execute(
        'UPDATE slot SET estado = ?, tarefa_nome = NULL, tarefa_fim = NULL WHERE id = ?',
        ('ativo', slot_id)
    )


def update_user_love(conn, user_id, amor_proprio):
    conn.execute('UPDATE user SET amor_proprio = ? WHERE id = ?', (amor_proprio, user_id))


def reward_tears(conn, user_id, amount):
    conn.execute('UPDATE user SET lagrimas = lagrimas + ? WHERE id = ?', (amount, user_id))


def unlock_publications(conn, user_id, silenced_ex):
    conn.execute(
        'UPDATE user SET publicacoes_disponivel = 1, silenciou_ex = ? WHERE id = ?',
        (1 if silenced_ex else 0, user_id)
    )
    conn.commit()


def resolve_publications(conn, user_id):
    conn.execute('UPDATE user SET publicacoes_resolvido = 1 WHERE id = ?', (user_id,))


def reset_user_game(conn, user_id):
    conn.execute(
        '''UPDATE user
           SET amor_proprio = ?, lagrimas = ?, publicacoes_disponivel = 0,
               publicacoes_resolvido = 0, silenciou_ex = 0
           WHERE id = ?''',
        (AMOR_PROPRIO_INICIAL, LAGRIMAS_INICIAIS, user_id)
    )
    conn.execute(
        'UPDATE slot SET estado = ?, etapa = 0, construcao_fim = NULL, tarefa_fim = NULL, tarefa_nome = NULL, tarefa_correta = 0 WHERE user_id = ?',
        ('vazio', user_id)
    )
    conn.commit()


def hash_password(password):
    return hasher.hash(password)

def check_password(password, hashed):
    if not isinstance(hashed, str):
        return False
    try:
        if len(hashed) == 64:
            return hex_sha256.verify(password, hashed)
        return hasher.verify(password, hashed)
    except (ValueError, TypeError):
        return False

def password_uses_old_hash(hashed):
    return len(hashed) == 64

def validate_register_form(form):
    data = {}
    errors = []

    username = form.get('username', '').strip()
    email = form.get('email', '').strip()
    password = form.get('password', '')

    if len(username) == 0:
        errors.append('O username não pode estar vazio.')
    elif len(username) > 80:
        errors.append('O username não pode ter mais de 80 caracteres.')
    else:
        data['username'] = username

    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        errors.append('Introduz um email válido.')
    elif len(email) > 120:
        errors.append('O email não pode ter mais de 120 caracteres.')
    else:
        data['email'] = email

    if len(password) < 6:
        errors.append('A password precisa de pelo menos 6 caracteres.')
    elif len(password) > 128:
        errors.append('A password não pode ter mais de 128 caracteres.')
    else:
        data['password'] = password

    return data, errors

def validate_login_form(form):
    data = {}
    errors = []

    username = form.get('username', '').strip()
    password = form.get('password', '')

    if len(username) == 0:
        errors.append('O username não pode estar vazio.')
    else:
        data['username'] = username

    if len(password) == 0:
        errors.append('A password não pode estar vazia.')
    else:
        data['password'] = password

    return data, errors

def str_to_dt(s):
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
    except (TypeError, ValueError):
        return None

def get_estado_emocional(amor_proprio):
    if amor_proprio == 100:
        return '❤️ Curado'
    if amor_proprio >= 81:
        return '✨ Quase Curado'
    if amor_proprio >= 61:
        return '✨ Confiante'
    if amor_proprio >= 41:
        return '🌱 A Recuperar'
    if amor_proprio >= 21:
        return '🌧 A Sofrer'
    return '💔 Desolado'

# =====================
# DADOS DOS ESPAÇOS
# =====================

CONSTRUCOES = {
    'bau': {
        'nome': 'Baú das Recordações Físicas',
        'descricao': 'Escolhas pesadas com objetos e lembranças físicas. Risco e recompensa emocional.',
        'imagem': 'img/bau.png',
        'custo_lagrimas': 3,
        'tempo_construcao': 5
    },
    'arquivo': {
        'nome': 'Arquivo Digital',
        'descricao': 'Mensagens, fotografias e redes sociais. Cada clique tem consequência.',
        'imagem': 'img/arquivodigital.png',
        'custo_lagrimas': 4,
        'tempo_construcao': 5
    },
    'mente': {
        'nome': 'A Mente e os Pensamentos',
        'descricao': 'Enfrenta emoções, saudades e padrões de pensamento repetitivos.',
        'imagem': 'img/mentepensamentos.png',
        'custo_lagrimas': 5,
        'tempo_construcao': 5
    },
    'novos': {
        'nome': 'Novos Começos',
        'descricao': 'Novas experiências, amizades e pequenos passos para o futuro.',
        'imagem': 'img/novoscomecos.png',
        'custo_lagrimas': 6,
        'tempo_construcao': 5
    }
}

SLOT_TIPOS = {
    1: 'bau',
    2: 'arquivo',
    3: 'mente',
    4: 'novos'
}

def get_tipo_por_numero(numero):
    return SLOT_TIPOS.get(numero)

def garantir_tipos_slots(conn, user_id):
    slots = conn.execute('SELECT id, numero, tipo FROM slot WHERE user_id = ?', (user_id,)).fetchall()
    for slot in slots:
        if not slot['tipo']:
            tipo = get_tipo_por_numero(slot['numero'])
            if tipo:
                conn.execute('UPDATE slot SET tipo = ? WHERE id = ?', (tipo, slot['id']))
    conn.commit()

def todos_slots_finalizados(conn, user_id):
    slots = conn.execute('SELECT estado FROM slot WHERE user_id = ?', (user_id,)).fetchall()
    return len(slots) == len(SLOT_TIPOS) and all(slot['estado'] == 'finalizado' for slot in slots)

def limitar_amor_antes_da_cura(conn, user_id, amor_proprio):
    amor_limitado = max(0, min(100, amor_proprio))
    if amor_limitado != amor_proprio:
        conn.execute('UPDATE user SET amor_proprio = ? WHERE id = ?', (amor_limitado, user_id))
        conn.commit()
    return amor_limitado

def calcular_amor_proprio(amor_atual, amor_delta):
    return max(0, min(100, amor_atual + amor_delta))

TAREFAS = {
    'bau': [
        {
            'id': 'roupas',
            'nome': 'Roupas do passado',
            'situacao': 'Encontraste roupas antigas do/a ex no armário.',
            'tempo': 3,
            'opcoes': [
                {'id': 'A', 'label': 'Guardar por agora e decidir depois', 'amor_delta': -5, 'mensagem': 'Mantiveste as roupas. O passado ficou mais presente no teu espaço.'},
                {'id': 'B', 'label': 'Separar para doar ou reciclar', 'amor_delta': 8, 'mensagem': 'Separaste as roupas. Estás a criar espaço físico e emocional.'}
            ]
        },
        {
            'id': 'cartas',
            'nome': 'Cartas antigas',
            'situacao': 'Encontraste cartas antigas do teu ex.',
            'tempo': 3,
            'opcoes': [
                {'id': 'A', 'label': 'Voltar a ler antes de decidir', 'amor_delta': -5, 'mensagem': 'Releste as cartas. Isso reacendeu sentimentos antigos.'},
                {'id': 'B', 'label': 'Guardar num envelope fechado', 'amor_delta': 8, 'mensagem': 'Guardaste as cartas e criaste uma distância segura entre passado e presente.'}
            ]
        },
        {
            'id': 'presentes',
            'nome': 'Presentes guardados',
            'situacao': 'Ainda tens presentes guardados do antigo relacionamento.',
            'tempo': 3,
            'opcoes': [
                {'id': 'A', 'label': 'Manter como lembrança íntima', 'amor_delta': -5, 'mensagem': 'Mantiveste os presentes. O peso do passado ainda vibra contigo.'},
                {'id': 'B', 'label': 'Reinventar ou doar com cuidado', 'amor_delta': 8, 'mensagem': 'Decidiste transformar os presentes. Isso abre espaço para algo novo.'}
            ]
        }
    ],
    'arquivo': [
        {
            'id': 'fotografias',
            'nome': 'Fotografias antigas',
            'situacao': 'Encontraste fotografias antigas em pastas digitais.',
            'tempo': 3,
            'opcoes': [
                {'id': 'A', 'label': 'Deixar no álbum e revisitar mais tarde', 'amor_delta': -5, 'mensagem': 'Deixaste as fotos como estão. Ainda estás a dar espaço ao passado.'},
                {'id': 'B', 'label': 'Mover para uma pasta privada', 'amor_delta': 8, 'mensagem': 'Organizaste as fotos num lugar protegido. Estás a construir um novo hábito.'}
            ]
        },
        {
            'id': 'mensagens',
            'nome': 'Mensagens antigas',
            'situacao': 'Recebeste uma mensagem antiga do/a ex.',
            'tempo': 3,
            'opcoes': [
                {'id': 'A', 'label': 'Guardar para pensar com calma', 'amor_delta': -5, 'mensagem': 'Guardaste a mensagem. Ficaste na dúvida entre passado e futuro.'},
                {'id': 'B', 'label': 'Apagar para proteger a tua paz', 'amor_delta': 8, 'mensagem': 'Apagaste a mensagem. Cuidaste do teu coração.'}
            ]
        },
        {
            'id': 'redes',
            'nome': 'Redes sociais',
            'situacao': 'Vistes o perfil do/a ex nas redes sociais.',
            'tempo': 3,
            'opcoes': [
                {'id': 'A', 'label': 'Continuar a espreitar discretamente', 'amor_delta': -5, 'mensagem': 'Observaste o/a ex. Isso mantém-te preso/a a cenas antigas.'},
                {'id': 'B', 'label': 'Bloquear e tentar seguir em frente', 'amor_delta': 8, 'mensagem': 'Bloqueaste o/a ex. Estás a cuidar da tua paz e do teu espaço mental.'}
            ]
        }
    ],
    'mente': [
        {
            'id': 'pensamentos',
            'nome': 'Pensamentos repetidos',
            'situacao': 'O mesmo pensamento sobre o relacionamento não te larga.',
            'tempo': 3,
            'opcoes': [
                {'id': 'A', 'label': 'Permitir que ele te domine mais um pouco', 'amor_delta': -5, 'mensagem': 'Ficou mais difícil sair deste ciclo mental.'},
                {'id': 'B', 'label': 'Anotar e redirecionar', 'amor_delta': 8, 'mensagem': 'Anotaste os pensamentos e mudaste o foco. Estás a cuidar da tua mente.'}
            ]
        },
        {
            'id': 'autocuidado',
            'nome': 'Autocuidado',
            'situacao': 'Tens uma janela para fazer algo por ti hoje.',
            'tempo': 3,
            'opcoes': [
                {'id': 'A', 'label': 'Ignorar o teu bem-estar', 'amor_delta': -5, 'mensagem': 'Ignoraste o autocuidado. O teu amor-próprio fica mais frágil.'},
                {'id': 'B', 'label': 'Fazer algo gentil por ti', 'amor_delta': 8, 'mensagem': 'Escolheste cuidar de ti. Isso fortalece o teu amor-próprio.'}
            ]
        },
        {
            'id': 'amigos',
            'nome': 'Apoio dos amigos',
            'situacao': 'Os teus amigos convidaram-te para sair.',
            'tempo': 3,
            'opcoes': [
                {'id': 'A', 'label': 'Ficar em casa para te proteger', 'amor_delta': -5, 'mensagem': 'Ficaste isolado/a. Isso enfraquece a tua confiança.'},
                {'id': 'B', 'label': 'Aceitar o convite e sair', 'amor_delta': 8, 'mensagem': 'Aceitaste o apoio. Estás a recuperar com companhia.'}
            ]
        }
    ],
    'novos': [
        {
            'id': 'hobbies',
            'nome': 'Hobbies novos',
            'situacao': 'Encontraste um novo hobby que te desperta curiosidade.',
            'tempo': 3,
            'opcoes': [
                {'id': 'A', 'label': 'Guardar a ideia para depois', 'amor_delta': -5, 'mensagem': 'Deixaste a oportunidade passar. Sentes-te mais parado/a.'},
                {'id': 'B', 'label': 'Experimentar algo novo hoje', 'amor_delta': 8, 'mensagem': 'Experimentaste algo novo. Estás a abrir espaço para uma nova versão tua.'}
            ]
        },
        {
            'id': 'exercicio',
            'nome': 'Exercício físico',
            'situacao': 'O teu corpo pede movimento hoje.',
            'tempo': 3,
            'opcoes': [
                {'id': 'A', 'label': 'Ficar no sofá e adiar', 'amor_delta': -5, 'mensagem': 'Adiaste o movimento. Acabaste por te sentir mais pesado/a.'},
                {'id': 'B', 'label': 'Mover-te com um pequeno treino', 'amor_delta': 8, 'mensagem': 'Fizeste exercício. A tua energia mudou para melhor.'}
            ]
        },
        {
            'id': 'experiencias',
            'nome': 'Novas experiências',
            'situacao': 'Surge uma oportunidade para algo diferente.',
            'tempo': 3,
            'opcoes': [
                {'id': 'A', 'label': 'Manter a zona de conforto', 'amor_delta': -5, 'mensagem': 'Evitar a novidade deixa-te mais estagnado/a.'},
                {'id': 'B', 'label': 'Dizer sim e aceitar', 'amor_delta': 8, 'mensagem': 'Aceitaste a experiência. Estás a recuperar com coragem.'}
            ]
        }
    ]
}

PUBLICACOES_TAREFA = {
    'id': 'publicacoes',
    'nome': 'Novas publicações',
    'situacao': 'Há uma atualização do/a ex no feed que pode chegar mais tarde.',
    'tempo': 3,
    'opcoes': [
        {'id': 'A', 'label': 'Manter distância e não ver', 'amor_delta': 8, 'correta': True, 'mensagem': 'Optaste por não ver. Protegeste a tua paz e o teu progresso.'},
        {'id': 'B', 'label': 'Ver por curiosidade', 'amor_delta': -10, 'correta': False, 'mensagem': 'Abriste o feed e sentiste as emoções do passado.'}
    ]
}

# =====================
# ROTAS DE AUTENTICAÇÃO
# =====================

