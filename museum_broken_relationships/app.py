from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os
import copy
from datetime import datetime, timedelta
from passlib.hash import pbkdf2_sha256 as hasher
from passlib.hash import hex_sha256

app = Flask(__name__)
app.secret_key = 'daw2026secretkey'

DB_PATH = os.path.join(os.path.dirname(__file__), 'game.db')
AMOR_PROPRIO_INICIAL = 4

# =====================
# BASE DE DADOS
# =====================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS slot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            numero INTEGER NOT NULL,
            estado TEXT DEFAULT 'vazio',
            tipo TEXT,
            etapa INTEGER DEFAULT 0,
            tarefa_fim TEXT,
            tarefa_nome TEXT,
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

    conn.close()

def hash_password(password):
    return hasher.hash(password)

def check_password(password, hashed):
    if len(hashed) == 64:
        return hex_sha256.verify(password, hashed)
    return hasher.verify(password, hashed)

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
    else:
        data['username'] = username

    if len(email) == 0:
        errors.append('O email não pode estar vazio.')
    else:
        data['email'] = email

    if len(password) < 6:
        errors.append('A password precisa de pelo menos 6 caracteres.')
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
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')

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
        'imagem': 'img/bau.png'
    },
    'arquivo': {
        'nome': 'Arquivo Digital',
        'descricao': 'Mensagens, fotografias e redes sociais. Cada clique tem consequência.',
        'imagem': 'img/arquivodigital.png'
    },
    'mente': {
        'nome': 'A Mente e os Pensamentos',
        'descricao': 'Enfrenta emoções, saudades e padrões de pensamento repetitivos.',
        'imagem': 'img/mentepensamentos.png'
    },
    'novos': {
        'nome': 'Novos Começos',
        'descricao': 'Novas experiências, amizades e pequenos passos para o futuro.',
        'imagem': 'img/novoscomecos.png'
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

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data, errors = validate_register_form(request.form)
        if len(errors) > 0:
            return render_template('register.html', erro=errors[0], values=request.form)

        conn = get_db()
        try:
            existing = conn.execute(
                'SELECT id FROM user WHERE username = ? OR email = ?',
                (data['username'], data['email'])
            ).fetchone()
            if existing:
                return render_template(
                    'register.html',
                    erro='Username ou email já existe!',
                    values=request.form
                )

            hashed = hash_password(data['password'])
            c = conn.execute(
                'INSERT INTO user (username, email, password, amor_proprio) VALUES (?, ?, ?, ?)',
                (data['username'], data['email'], hashed, AMOR_PROPRIO_INICIAL)
            )
            user_id = c.lastrowid

            # Criar 4 slots com tipos fixos definidos no backend
            for i in range(1, 5):
                conn.execute('INSERT INTO slot (user_id, numero, tipo, etapa) VALUES (?, ?, ?, ?)',
                             (user_id, i, get_tipo_por_numero(i), 0))
            conn.commit()
        finally:
            conn.close()

        session['user_id'] = user_id
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data, errors = validate_login_form(request.form)
        if len(errors) > 0:
            return render_template('login.html', erro=errors[0], values=request.form)

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM user WHERE username = ?',
            (data['username'],)
        ).fetchone()
        conn.close()

        if not user or not check_password(data['password'], user['password']):
            return render_template(
                'login.html',
                erro='Username ou password incorretos!',
                values=request.form
            )

        # Atualiza hashes antigos depois de um login válido.
        if password_uses_old_hash(user['password']):
            conn = get_db()
            conn.execute(
                'UPDATE user SET password = ? WHERE id = ?',
                (hash_password(data['password']), user['id'])
            )
            conn.commit()
            conn.close()

        session['user_id'] = user['id']
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# =====================
# DASHBOARD
# =====================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    user = conn.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
    if not user:
        conn.close()
        session.pop('user_id', None)
        return redirect(url_for('login'))

    garantir_tipos_slots(conn, user['id'])
    limitar_amor_antes_da_cura(conn, user['id'], user['amor_proprio'])
    user = conn.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
    slots = conn.execute('SELECT * FROM slot WHERE user_id = ? ORDER BY numero', (user['id'],)).fetchall()
    top_users_data = conn.execute('SELECT * FROM user ORDER BY amor_proprio DESC LIMIT 10').fetchall()
    top_users = []
    for top_user in top_users_data:
        top_users.append({
            'id': top_user['id'],
            'username': top_user['username'],
            'amor_proprio': top_user['amor_proprio'],
            'estado': get_estado_emocional(top_user['amor_proprio'])
        })
    user_estado = get_estado_emocional(user['amor_proprio'])

    tarefas_para_template = copy.deepcopy(TAREFAS)
    if session.get('publicacoes_disponivel') and not session.get('publicacoes_resolvido'):
        publicacoes = copy.deepcopy(PUBLICACOES_TAREFA)
        if session.get('silenciou_ex'):
            publicacoes['situacao'] = 'Não viste as novas publicações do/a ex. Mantens a tua paz.'
            publicacoes['opcoes'] = [
                {'id': 'A', 'label': 'Continuar a afastar-te', 'amor_delta': 8, 'correta': True, 'mensagem': 'Decidiste não ver. Isso fortalece a tua recuperação.'},
                {'id': 'B', 'label': 'Ceder e ver por curiosidade', 'amor_delta': -5, 'correta': False, 'mensagem': 'Ceder à curiosidade trouxe alguma dor, mas já aprendeste algo.'}
            ]
        else:
            publicacoes['situacao'] = 'Vistes uma atualização do/a ex no feed hoje.'
            publicacoes['opcoes'] = [
                {'id': 'A', 'label': 'Ignorar e manter a distância', 'amor_delta': 8, 'correta': True, 'mensagem': 'Ignoraste-o/a. Estás a proteger a tua paz.'},
                {'id': 'B', 'label': 'Ver e enfrentar o desconforto', 'amor_delta': -10, 'correta': False, 'mensagem': 'Viste as publicações e sentiste o peso do passado.'}
            ]
        tarefas_para_template['arquivo'].append(publicacoes)

    conn.close()

    return render_template('dashboard.html',
        user=user,
        user_estado=user_estado,
        slots=slots,
        construcoes=CONSTRUCOES,
        tarefas=tarefas_para_template,
        top_users=top_users
    )

# =====================
# ROTAS DO JOGO (API)
# =====================

@app.route('/api/construir', methods=['POST'])
def construir():
    if 'user_id' not in session:
        return jsonify({'erro': 'Não autenticado'}), 401

    data = request.get_json()
    slot_num = data.get('slot')

    conn = get_db()
    user = conn.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
    slot = conn.execute('SELECT * FROM slot WHERE user_id = ? AND numero = ?', (user['id'], slot_num)).fetchone()

    slot_tipo = slot['tipo'] if slot else None
    if slot_tipo not in CONSTRUCOES:
        conn.close()
        return jsonify({'erro': 'Tipo de slot inválido'}), 400

    if not slot or slot['estado'] != 'vazio':
        conn.close()
        return jsonify({'erro': 'Slot não disponível'}), 400

    amor_atual = limitar_amor_antes_da_cura(conn, user['id'], user['amor_proprio'])
    if amor_atual >= 100 and todos_slots_finalizados(conn, user['id']):
        conn.close()
        return jsonify({'erro': 'Já estás curado/a. Não precisas de novas ações.'}), 400

    if amor_atual <= 0:
        conn.close()
        return jsonify({'erro': 'Ficaste desolado/a. Reinicia o progresso para voltar a tentar.'}), 400

    conn.execute('UPDATE slot SET estado = ?, etapa = ?, tarefa_correta = ? WHERE id = ?',
                 ('ativo', 1, 0, slot['id']))
    conn.commit()
    conn.close()

    return jsonify({
        'sucesso': True,
        'estado_emocional': get_estado_emocional(amor_atual)
    })

@app.route('/api/dar_ordem', methods=['POST'])
def dar_ordem():
    if 'user_id' not in session:
        return jsonify({'erro': 'Não autenticado'}), 401

    data = request.get_json()
    slot_num = data.get('slot')
    tarefa_id = data.get('tarefa_id')
    opcao_id = data.get('opcao_id')

    conn = get_db()
    user = conn.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
    slot = conn.execute('SELECT * FROM slot WHERE user_id = ? AND numero = ?',
                        (user['id'], slot_num)).fetchone()

    if not slot or slot['estado'] != 'ativo':
        conn.close()
        return jsonify({'erro': 'Espaço não disponível'}), 400

    etapa = slot['etapa'] or 1

    tarefas_tipo = copy.deepcopy(TAREFAS.get(slot['tipo'], []))
    if slot['tipo'] == 'arquivo' and session.get('publicacoes_disponivel') and not session.get('publicacoes_resolvido'):
        publicacoes = copy.deepcopy(PUBLICACOES_TAREFA)
        if session.get('silenciou_ex'):
            publicacoes['opcoes'] = [
                {'id': 'A', 'label': 'Continuar a afastar-te', 'amor_delta': 8, 'correta': True, 'mensagem': 'Decidiste não ver. Isso fortalece a tua recuperação.'},
                {'id': 'B', 'label': 'Ceder e ver por curiosidade', 'amor_delta': -5, 'correta': False, 'mensagem': 'Ceder à curiosidade trouxe alguma dor, mas já aprendeste algo.'}
            ]
        else:
            publicacoes['opcoes'] = [
                {'id': 'A', 'label': 'Ignorar e manter a distância', 'amor_delta': 8, 'correta': True, 'mensagem': 'Ignoraste-o/a. Estás a proteger a tua paz.'},
                {'id': 'B', 'label': 'Ver e enfrentar o desconforto', 'amor_delta': -10, 'correta': False, 'mensagem': 'Viste as publicações e sentiste o peso do passado.'}
            ]
        tarefas_tipo.append(publicacoes)

    if etapa < 1 or etapa > len(tarefas_tipo):
        conn.close()
        return jsonify({'erro': 'Momento inválido'}), 400

    tarefa = tarefas_tipo[etapa - 1]
    if tarefa['id'] != tarefa_id:
        conn.close()
        return jsonify({'erro': 'A questão não corresponde ao momento atual'}), 400

    opcao = None
    for o in tarefa['opcoes']:
        if o['id'] == opcao_id:
            opcao = o
            break

    if not opcao:
        conn.close()
        return jsonify({'erro': 'Opção inválida'}), 400

    amor_atual = limitar_amor_antes_da_cura(conn, user['id'], user['amor_proprio'])
    if amor_atual >= 100 and todos_slots_finalizados(conn, user['id']):
        conn.close()
        return jsonify({'erro': 'Já estás curado/a. Não precisas de novas ações.'}), 400

    if amor_atual <= 0:
        conn.close()
        return jsonify({'erro': 'Ficaste desolado/a. Reinicia o progresso para voltar a tentar.'}), 400

    resposta_correta = opcao.get('correta', opcao['amor_delta'] > 0)
    amor_delta = opcao['amor_delta']
    if resposta_correta and amor_delta <= 0:
        amor_delta = 8

    novo_amor = calcular_amor_proprio(amor_atual, amor_delta)
    fim = (datetime.utcnow() + timedelta(seconds=tarefa['tempo'])).strftime('%Y-%m-%d %H:%M:%S')

    if tarefa_id == 'redes':
        session['publicacoes_disponivel'] = True
        session['silenciou_ex'] = (opcao_id == 'B')

    conn.execute('UPDATE user SET amor_proprio = ? WHERE id = ?',
                 (novo_amor, user['id']))
    conn.execute('UPDATE slot SET estado = ?, tarefa_nome = ?, tarefa_fim = ?, tarefa_correta = ? WHERE id = ?',
                 ('processando', f"{tarefa['nome']} - {opcao['label']}", fim, 1 if resposta_correta else 0, slot['id']))
    conn.commit()
    conn.close()

    delta_text = f"{amor_delta:+d}"
    return jsonify({
        'sucesso': True,
        'amor_proprio': novo_amor,
        'estado_emocional': get_estado_emocional(novo_amor),
        'mensagem': opcao['mensagem'],
        'delta': delta_text,
        'novo_valor': novo_amor,
        'resposta_correta': resposta_correta
    })

@app.route('/api/recolher', methods=['POST'])
def recolher():
    if 'user_id' not in session:
        return jsonify({'erro': 'Não autenticado'}), 401

    data = request.get_json()
    slot_num = data.get('slot')

    conn = get_db()
    user = conn.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
    slot = conn.execute('SELECT * FROM slot WHERE user_id = ? AND numero = ?',
                        (user['id'], slot_num)).fetchone()

    # Permite recolher logo após o contador terminar.
    if slot and slot['estado'] == 'processando' and slot['tarefa_fim']:
        fim = str_to_dt(slot['tarefa_fim'])
        if datetime.utcnow() >= fim:
            conn.execute('UPDATE slot SET estado = ? WHERE id = ?', ('concluida', slot['id']))
            conn.commit()
            slot = conn.execute('SELECT * FROM slot WHERE id = ?', (slot['id'],)).fetchone()

    if not slot or slot['estado'] != 'concluida':
        conn.close()
        return jsonify({'sem_recolha': True})

    amor_resposta = limitar_amor_antes_da_cura(conn, user['id'], user['amor_proprio'])
    tipo = slot['tipo'] or get_tipo_por_numero(slot['numero'])
    
    tarefas_tipo = copy.deepcopy(TAREFAS.get(tipo, []))
    if tipo == 'arquivo' and session.get('publicacoes_disponivel') and not session.get('publicacoes_resolvido'):
        tarefas_tipo.append(PUBLICACOES_TAREFA)
        
    total_momentos = len(tarefas_tipo)
    proxima_etapa = (slot['etapa'] or 1) + 1
    resposta_correta = slot['tarefa_correta'] == 1
    mostrar_popup_cura = False

    if resposta_correta:
        if slot['tarefa_nome'] and slot['tarefa_nome'].startswith('Novas publicações'):
            session['publicacoes_resolvido'] = True
            
        if proxima_etapa > total_momentos:
            conn.execute('UPDATE slot SET estado = ?, tarefa_nome = NULL, tarefa_fim = NULL, tarefa_correta = 0 WHERE id = ?',
                         ('finalizado', slot['id']))
            if todos_slots_finalizados(conn, user['id']):
                amor_resposta = 100
                mostrar_popup_cura = True
                conn.execute('UPDATE user SET amor_proprio = ? WHERE id = ?', (amor_resposta, user['id']))
                mensagem = 'Parabéns! Respondeste corretamente a todos os momentos de todos os espaços.'
            else:
                mensagem = 'Parabéns! Respondeste corretamente a todos os momentos. Espaço concluído.'
        else:
            conn.execute('UPDATE slot SET estado = ?, tarefa_nome = NULL, tarefa_fim = NULL, etapa = ?, tarefa_correta = 0 WHERE id = ?',
                         ('ativo', proxima_etapa, slot['id']))
            mensagem = 'Resposta correta! O próximo momento já está pronto.'
    else:
        conn.execute('UPDATE slot SET estado = ?, tarefa_nome = NULL, tarefa_fim = NULL WHERE id = ?',
                     ('ativo', slot['id']))
        mensagem = 'A resposta não estava certa. Repete o momento para avançar.'

    conn.commit()
    conn.close()

    return jsonify({
        'sucesso': True,
        'amor_proprio': amor_resposta,
        'mensagem': mensagem,
        'estado_emocional': get_estado_emocional(amor_resposta),
        'mostrar_popup_cura': mostrar_popup_cura
    })

@app.route('/reiniciar')
def reiniciar():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    user = conn.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
    if not user or user['amor_proprio'] != 0:
        conn.close()
        return redirect(url_for('dashboard'))

    conn.execute('UPDATE user SET amor_proprio = ? WHERE id = ?', (AMOR_PROPRIO_INICIAL, user['id']))
    conn.execute(
        'UPDATE slot SET estado = ?, etapa = 0, tarefa_fim = NULL, tarefa_nome = NULL, tarefa_correta = 0 WHERE user_id = ?',
        ('vazio', user['id'])
    )
    conn.commit()
    conn.close()
    
    session.pop('publicacoes_disponivel', None)
    session.pop('publicacoes_resolvido', None)
    session.pop('silenciou_ex', None)

    return redirect(url_for('dashboard'))

@app.route('/api/verificar_tarefa', methods=['POST'])
def verificar_tarefa():
    if 'user_id' not in session:
        return jsonify({'erro': 'Não autenticado'}), 401

    data = request.get_json()
    slot_num = data.get('slot')

    conn = get_db()
    slot = conn.execute('SELECT * FROM slot WHERE user_id = ? AND numero = ?',
                        (session['user_id'], slot_num)).fetchone()

    if not slot or slot['estado'] != 'processando':
        conn.close()
        return jsonify({'erro': 'Slot inválido'}), 400

    fim = str_to_dt(slot['tarefa_fim'])
    if datetime.utcnow() >= fim:
        conn.execute('UPDATE slot SET estado = ? WHERE id = ?', ('concluida', slot['id']))
        conn.commit()
        conn.close()
        return jsonify({'sucesso': True, 'estado': 'concluida'})

    segundos = int((fim - datetime.utcnow()).total_seconds())
    conn.close()
    return jsonify({'sucesso': False, 'segundos_restantes': segundos})

@app.route('/api/estado')
def estado():
    if 'user_id' not in session:
        return jsonify({'erro': 'Não autenticado'}), 401

    conn = get_db()
    user = conn.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
    amor_atual = limitar_amor_antes_da_cura(conn, user['id'], user['amor_proprio'])
    slots = conn.execute('SELECT * FROM slot WHERE user_id = ? ORDER BY numero', (user['id'],)).fetchall()
    conn.close()

    slots_data = []
    for s in slots:
        seg_restantes = None
        if s['tarefa_fim'] and s['estado'] == 'processando':
            fim = str_to_dt(s['tarefa_fim'])
            seg_restantes = max(0, int((fim - datetime.utcnow()).total_seconds()))

        slots_data.append({
            'numero': s['numero'],
            'estado': s['estado'],
            'tipo': s['tipo'],
            'tarefa_nome': s['tarefa_nome'],
            'segundos_restantes': seg_restantes
        })

    return jsonify({
        'amor_proprio': amor_atual,
        'estado_emocional': get_estado_emocional(amor_atual),
        'slots': slots_data
    })

# =====================
# INICIALIZAÇÃO
# =====================

init_db()

if __name__ == '__main__':
    app.run(debug=True)
