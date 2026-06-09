from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'daw2026secretkey'

DB_PATH = os.path.join(os.path.dirname(__file__), 'game.db')

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
            amor_proprio INTEGER DEFAULT 50,
            lagrimas INTEGER DEFAULT 50,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS slot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            numero INTEGER NOT NULL,
            estado TEXT DEFAULT 'vazio',
            tipo TEXT,
            construcao_fim TEXT,
            tarefa_fim TEXT,
            tarefa_nome TEXT,
            FOREIGN KEY (user_id) REFERENCES user(id)
        );
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed):
    return hash_password(password) == hashed

def now_str():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

def str_to_dt(s):
    if not s:
        return None
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')

def get_estado_emocional(amor_proprio):
    if amor_proprio <= 20:
        return '💔 Coração Partido'
    if amor_proprio <= 40:
        return '🌱 Recuperação'
    if amor_proprio <= 60:
        return '🏗️ Reconstrução'
    if amor_proprio <= 80:
        return '✨ Confiança'
    return '👑 Amor-Próprio Máximo'

# =====================
# DADOS DAS CONSTRUÇÕES
# =====================

CONSTRUCOES = {
    'bau': {
        'nome': 'Baú das Recordações Físicas',
        'custo': 50,
        'tempo': 3,
        'emoji': '📦'
    },
    'arquivo': {
        'nome': 'Arquivo Digital',
        'custo': 150,
        'tempo': 3,
        'emoji': '💻'
    },
    'mente': {
        'nome': 'A Mente e os Pensamentos',
        'custo': 300,
        'tempo': 3,
        'emoji': '🧠'
    }
}

TAREFAS = {
    'bau': [
        {'id': 'doar_roupas', 'nome': 'Doar roupas do/a ex', 'lagrimas': 10, 'tempo': 3, 'amor_proprio_delta': 200, 'lagrimas_delta': 0, 'hidden': True, 'hint': 'Resultado incerto'},
        {'id': 'guardar_cartas', 'nome': 'Guardar cartas antigas', 'lagrimas': 5, 'tempo': 3, 'amor_proprio_delta': -50, 'lagrimas_delta': 0, 'hidden': True, 'hint': 'Resultado incerto'},
    ],
    'arquivo': [
        {'id': 'apagar_fotos', 'nome': 'Apagar fotografias antigas', 'lagrimas': 15, 'tempo': 3, 'amor_proprio_delta': 150, 'lagrimas_delta': 0, 'hidden': True, 'hint': 'Resultado incerto'},
        {'id': 'bloquear_redes', 'nome': 'Bloquear nas redes sociais', 'lagrimas': 20, 'tempo': 3, 'amor_proprio_delta': 100, 'lagrimas_delta': 0, 'hidden': True, 'hint': 'Resultado incerto'},
    ],
    'mente': [
        {'id': 'meditacao', 'nome': 'Sessão de meditação', 'lagrimas': 25, 'tempo': 3, 'amor_proprio_delta': 200, 'lagrimas_delta': 0, 'hidden': True, 'hint': 'Resultado incerto'},
        {'id': 'diario', 'nome': 'Escrever no diário', 'lagrimas': 10, 'tempo': 3, 'amor_proprio_delta': -100, 'lagrimas_delta': 20, 'hidden': True, 'hint': 'Ganhas Lágrimas extra ⚠️'},
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
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not email or not password:
            return render_template('register.html', erro='Preenche todos os campos!')

        if len(password) < 6:
            return render_template('register.html', erro='A password precisa de pelo menos 6 caracteres!')

        conn = get_db()
        try:
            existing = conn.execute('SELECT id FROM user WHERE username = ? OR email = ?', (username, email)).fetchone()
            if existing:
                return render_template('register.html', erro='Username ou email já existe!')

            hashed = hash_password(password)
            c = conn.execute(
                'INSERT INTO user (username, email, password) VALUES (?, ?, ?)',
                (username, email, hashed)
            )
            user_id = c.lastrowid

            # Criar 4 slots
            for i in range(1, 5):
                conn.execute('INSERT INTO slot (user_id, numero) VALUES (?, ?)', (user_id, i))
            conn.commit()
        finally:
            conn.close()

        session['user_id'] = user_id
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db()
        user = conn.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
        conn.close()

        if not user or not check_password(password, user['password']):
            return render_template('login.html', erro='Username ou password incorretos!')

        session['user_id'] = user['id']
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
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

    slots = conn.execute('SELECT * FROM slot WHERE user_id = ? ORDER BY numero', (user['id'],)).fetchall()
    top_users = conn.execute('SELECT * FROM user ORDER BY amor_proprio DESC LIMIT 10').fetchall()
    top_users = [
        {
            'id': u['id'],
            'username': u['username'],
            'amor_proprio': u['amor_proprio'],
            'estado': get_estado_emocional(u['amor_proprio'])
        }
        for u in top_users
    ]
    user_estado = get_estado_emocional(user['amor_proprio'])
    conn.close()

    return render_template('dashboard.html',
        user=user,
        user_estado=user_estado,
        slots=slots,
        construcoes=CONSTRUCOES,
        tarefas=TAREFAS,
        top_users=top_users,
        agora=datetime.utcnow()
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
    tipo = data.get('tipo')

    if tipo not in CONSTRUCOES:
        return jsonify({'erro': 'Tipo inválido'}), 400

    conn = get_db()
    user = conn.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
    slot = conn.execute('SELECT * FROM slot WHERE user_id = ? AND numero = ?', (user['id'], slot_num)).fetchone()

    if not slot or slot['estado'] != 'vazio':
        conn.close()
        return jsonify({'erro': 'Slot não disponível'}), 400

    custo = CONSTRUCOES[tipo]['custo']
    if user['amor_proprio'] < custo:
        conn.close()
        return jsonify({'erro': 'Moedas insuficientes!'}), 400

    fim = (datetime.utcnow() + timedelta(seconds=CONSTRUCOES[tipo]['tempo'])).strftime('%Y-%m-%d %H:%M:%S')
    conn.execute('UPDATE user SET amor_proprio = amor_proprio - ? WHERE id = ?', (custo, user['id']))
    conn.execute('UPDATE slot SET tipo = ?, estado = ?, construcao_fim = ? WHERE id = ?',
                 (tipo, 'construindo', fim, slot['id']))
    conn.commit()
    novo_amor = user['amor_proprio'] - custo
    conn.close()

    return jsonify({
        'sucesso': True,
        'amor_proprio': novo_amor,
        'estado_emocional': get_estado_emocional(novo_amor)
    })

@app.route('/api/verificar_construcao', methods=['POST'])
def verificar_construcao():
    if 'user_id' not in session:
        return jsonify({'erro': 'Não autenticado'}), 401

    data = request.get_json()
    slot_num = data.get('slot')

    conn = get_db()
    slot = conn.execute('SELECT * FROM slot WHERE user_id = ? AND numero = ?',
                        (session['user_id'], slot_num)).fetchone()

    if not slot or slot['estado'] != 'construindo':
        conn.close()
        return jsonify({'erro': 'Slot inválido'}), 400

    fim = str_to_dt(slot['construcao_fim'])
    if datetime.utcnow() >= fim:
        conn.execute('UPDATE slot SET estado = ? WHERE id = ?', ('ativo', slot['id']))
        conn.commit()
        conn.close()
        return jsonify({'sucesso': True, 'estado': 'ativo'})

    segundos = int((fim - datetime.utcnow()).total_seconds())
    conn.close()
    return jsonify({'sucesso': False, 'segundos_restantes': segundos})

@app.route('/api/dar_ordem', methods=['POST'])
def dar_ordem():
    if 'user_id' not in session:
        return jsonify({'erro': 'Não autenticado'}), 401

    data = request.get_json()
    slot_num = data.get('slot')
    tarefa_id = data.get('tarefa_id')

    conn = get_db()
    user = conn.execute('SELECT * FROM user WHERE id = ?', (session['user_id'],)).fetchone()
    slot = conn.execute('SELECT * FROM slot WHERE user_id = ? AND numero = ?',
                        (user['id'], slot_num)).fetchone()

    if not slot or slot['estado'] != 'ativo':
        conn.close()
        return jsonify({'erro': 'Construção não disponível'}), 400

    tarefa = None
    for t in TAREFAS.get(slot['tipo'], []):
        if t['id'] == tarefa_id:
            tarefa = t
            break

    if not tarefa:
        conn.close()
        return jsonify({'erro': 'Tarefa inválida'}), 400

    if user['lagrimas'] < tarefa['lagrimas']:
        conn.close()
        return jsonify({'erro': 'Lágrimas insuficientes!'}), 400

    fim = (datetime.utcnow() + timedelta(seconds=tarefa['tempo'])).strftime('%Y-%m-%d %H:%M:%S')
    conn.execute('UPDATE user SET lagrimas = lagrimas - ? WHERE id = ?', (tarefa['lagrimas'], user['id']))
    conn.execute('UPDATE slot SET estado = ?, tarefa_nome = ?, tarefa_fim = ? WHERE id = ?',
                 ('processando', tarefa['nome'], fim, slot['id']))
    conn.commit()
    nova_lag = user['lagrimas'] - tarefa['lagrimas']
    conn.close()

    return jsonify({'sucesso': True, 'lagrimas': nova_lag})

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

    if not slot or slot['estado'] != 'concluida':
        conn.close()
        return jsonify({'erro': 'Nada para recolher'}), 400

    tarefa = None
    for t in TAREFAS.get(slot['tipo'], []):
        if t['nome'] == slot['tarefa_nome']:
            tarefa = t
            break

    if not tarefa:
        conn.close()
        return jsonify({'erro': 'Tarefa inválida'}), 400

    amor_delta = tarefa.get('amor_proprio_delta', 0)
    lagrimas_delta = tarefa.get('lagrimas_delta', 0)
    novo_amor = max(0, min(100, user['amor_proprio'] + amor_delta))
    nova_lag = user['lagrimas'] + lagrimas_delta

    conn.execute('UPDATE user SET amor_proprio = ?, lagrimas = ? WHERE id = ?',
                 (novo_amor, nova_lag, user['id']))
    conn.execute('UPDATE slot SET estado = ?, tarefa_nome = NULL, tarefa_fim = NULL WHERE id = ?',
                 ('ativo', slot['id']))
    conn.commit()
    conn.close()

    if amor_delta >= 0:
        mensagem = f'❤️ +{amor_delta} Amor-Próprio — Tomaste uma decisão saudável.'
    else:
        mensagem = f'💔 {amor_delta} Amor-Próprio — Essa escolha atrasou o teu processo de cura.'

    if lagrimas_delta > 0:
        mensagem += f' +{lagrimas_delta} Lágrimas'

    return jsonify({
        'sucesso': True,
        'amor_proprio': novo_amor,
        'lagrimas': nova_lag,
        'mensagem': mensagem,
        'estado_emocional': get_estado_emocional(novo_amor)
    })

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
    slots = conn.execute('SELECT * FROM slot WHERE user_id = ? ORDER BY numero', (user['id'],)).fetchall()
    conn.close()

    slots_data = []
    for s in slots:
        seg_restantes = None
        if s['construcao_fim'] and s['estado'] == 'construindo':
            fim = str_to_dt(s['construcao_fim'])
            seg_restantes = max(0, int((fim - datetime.utcnow()).total_seconds()))
        elif s['tarefa_fim'] and s['estado'] == 'processando':
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
        'amor_proprio': user['amor_proprio'],
        'lagrimas': user['lagrimas'],
        'estado_emocional': get_estado_emocional(user['amor_proprio']),
        'slots': slots_data
    })

# =====================
# INICIALIZAÇÃO
# =====================

init_db()

if __name__ == '__main__':
    app.run(debug=True)
