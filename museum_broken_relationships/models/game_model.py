import sqlite3 as dbapi2
from datetime import datetime

from flask import current_app
from flask_login import UserMixin
from passlib.hash import pbkdf2_sha256 as hasher


amor_proprio_inicial = 4
lagrimas_iniciais = 60
custo_decisao = 1
bonus_lagrimas_resposta_correta = 2
tempo_construcao_segundos = 60
tempo_tarefa_segundos = 300


class User(UserMixin):
    def __init__(self, user_id, username, email, password, amor_proprio, lagrimas):
        self.id = user_id
        self.username = username
        self.email = email
        self.password = password
        self.amor_proprio = amor_proprio
        self.lagrimas = lagrimas


def get_user(user_id):
    db = current_app.config["db"]
    return db.get_user_by_id(user_id)


def get_estado_emocional(amor_proprio):
    if amor_proprio == 100:
        return '<i class="fa-solid fa-heart" style="color: rgb(202, 46, 84);"></i> Curado'
    if amor_proprio >= 81:
        return '<wa-icon name="star" style="color: rgb(226, 196, 83);"></wa-icon> Quase Curado'
    if amor_proprio >= 61:
        return '<wa-icon name="star" style="color: rgb(226, 196, 83);"></wa-icon> Confiante'
    if amor_proprio >= 41:
        return '<i class="fa-solid fa-seedling" style="color: rgb(78, 134, 41);"></i> A Recuperar'
    if amor_proprio >= 21:
        return '<i class="fa-solid fa-cloud-showers-heavy" style="color: rgb(117, 111, 111);"></i> A Sofrer'
    return '<i class="fa-solid fa-heart-crack" style="color: rgb(202, 46, 84);"></i> Desolado'


def str_to_dt(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def dt_to_str(value):
    return value.strftime("%Y-%m-%d %H:%M:%S")


def calcular_amor_proprio(amor_atual, amor_delta):
    return max(0, min(100, amor_atual + amor_delta))


construcoes = {
    "bau": {
        "nome": "Baú das Recordações Físicas",
        "descricao": "Escolhas pesadas com objetos e lembranças físicas.",
        "imagem": "img/bau.png",
        "custo_lagrimas": 3,
        "tempo_construcao": tempo_construcao_segundos,
    },
    "arquivo": {
        "nome": "Arquivo Digital",
        "descricao": "Mensagens, fotografias e redes sociais.",
        "imagem": "img/arquivodigital.png",
        "custo_lagrimas": 4,
        "tempo_construcao": tempo_construcao_segundos,
    },
    "mente": {
        "nome": "A Mente e os Pensamentos",
        "descricao": "Emoções, saudades e padrões de pensamento.",
        "imagem": "img/mentepensamentos.png",
        "custo_lagrimas": 5,
        "tempo_construcao": tempo_construcao_segundos,
    },
    "novos": {
        "nome": "Novos Começos",
        "descricao": "Novas experiências, amizades e pequenos passos.",
        "imagem": "img/novoscomecos.png",
        "custo_lagrimas": 6,
        "tempo_construcao": tempo_construcao_segundos,
    },
}


SLOT_TIPOS = {
    1: "bau",
    2: "arquivo",
    3: "mente",
    4: "novos",
}


tarefas = {
    "bau": [
        {
            "id": "roupas",
            "nome": "Roupas do passado",
            "situacao": "Encontraste roupas antigas do/a ex no armário.",
            "tempo": tempo_tarefa_segundos,
            "opcoes": [
                {"id": "A", "label": "Guardar por agora e decidir depois", "amor_delta": -5, "mensagem": "Mantiveste as roupas. O passado ficou mais presente no teu espaço."},
                {"id": "B", "label": "Separar para doar ou reciclar", "amor_delta": 8, "mensagem": "Separaste as roupas. Estás a criar espaço físico e emocional."},
            ],
        },
        {
            "id": "cartas",
            "nome": "Cartas antigas",
            "situacao": "Encontraste cartas antigas do teu ex.",
            "tempo": tempo_tarefa_segundos,
            "opcoes": [
                {"id": "A", "label": "Voltar a ler antes de decidir", "amor_delta": -5, "mensagem": "Releste as cartas. Isso reacendeu sentimentos antigos."},
                {"id": "B", "label": "Guardar num envelope fechado", "amor_delta": 8, "mensagem": "Guardaste as cartas e criaste uma distância segura entre passado e presente."},
            ],
        },
        {
            "id": "presentes",
            "nome": "Presentes guardados",
            "situacao": "Ainda tens presentes guardados do antigo relacionamento.",
            "tempo": tempo_tarefa_segundos,
            "opcoes": [
                {"id": "A", "label": "Manter como lembrança íntima", "amor_delta": -5, "mensagem": "Mantiveste os presentes. O peso do passado ainda vibra contigo."},
                {"id": "B", "label": "Reinventar ou doar com cuidado", "amor_delta": 8, "mensagem": "Decidiste transformar os presentes. Isso abre espaço para algo novo."},
            ],
        },
    ],
    "arquivo": [
        {
            "id": "fotografias",
            "nome": "Fotografias antigas",
            "situacao": "Encontraste fotografias antigas em pastas digitais.",
            "tempo": tempo_tarefa_segundos,
            "opcoes": [
                {"id": "A", "label": "Deixar no álbum e revisitar mais tarde", "amor_delta": -5, "mensagem": "Deixaste as fotos como estão. Ainda estás a dar espaço ao passado."},
                {"id": "B", "label": "Mover para uma pasta privada", "amor_delta": 8, "mensagem": "Organizaste as fotos num lugar protegido. Estás a construir um novo hábito."},
            ],
        },
        {
            "id": "mensagens",
            "nome": "Mensagens antigas",
            "situacao": "Recebeste uma mensagem antiga do/a ex.",
            "tempo": tempo_tarefa_segundos,
            "opcoes": [
                {"id": "A", "label": "Guardar para pensar com calma", "amor_delta": -5, "mensagem": "Guardaste a mensagem. Ficaste na dúvida entre passado e futuro."},
                {"id": "B", "label": "Apagar para proteger a tua paz", "amor_delta": 8, "mensagem": "Apagaste a mensagem. Cuidaste do teu coração."},
            ],
        },
        {
            "id": "redes",
            "nome": "Redes sociais",
            "situacao": "Vistes o perfil do/a ex nas redes sociais.",
            "tempo": tempo_tarefa_segundos,
            "opcoes": [
                {"id": "A", "label": "Continuar a espreitar discretamente", "amor_delta": -5, "mensagem": "Observaste o/a ex. Isso mantém-te preso/a a cenas antigas."},
                {"id": "B", "label": "Bloquear e tentar seguir em frente", "amor_delta": 8, "mensagem": "Bloqueaste o/a ex. Estás a cuidar da tua paz e do teu espaço mental."},
            ],
        },
    ],
    "mente": [
        {
            "id": "pensamentos",
            "nome": "Pensamentos repetidos",
            "situacao": "O mesmo pensamento sobre o relacionamento não te larga.",
            "tempo": tempo_tarefa_segundos,
            "opcoes": [
                {"id": "A", "label": "Permitir que ele te domine mais um pouco", "amor_delta": -5, "mensagem": "Ficou mais difícil sair deste ciclo mental."},
                {"id": "B", "label": "Anotar e redirecionar", "amor_delta": 8, "mensagem": "Anotaste os pensamentos e mudaste o foco. Estás a cuidar da tua mente."},
            ],
        },
        {
            "id": "autocuidado",
            "nome": "Autocuidado",
            "situacao": "Tens uma janela para fazer algo por ti hoje.",
            "tempo": tempo_tarefa_segundos,
            "opcoes": [
                {"id": "A", "label": "Ignorar o teu bem-estar", "amor_delta": -5, "mensagem": "Ignoraste o autocuidado. O teu amor-próprio fica mais frágil."},
                {"id": "B", "label": "Fazer algo gentil por ti", "amor_delta": 8, "mensagem": "Escolheste cuidar de ti. Isso fortalece o teu amor-próprio."},
            ],
        },
        {
            "id": "amigos",
            "nome": "Apoio dos amigos",
            "situacao": "Os teus amigos convidaram-te para sair.",
            "tempo": tempo_tarefa_segundos,
            "opcoes": [
                {"id": "A", "label": "Ficar em casa para te proteger", "amor_delta": -5, "mensagem": "Ficaste isolado/a. Isso enfraquece a tua confiança."},
                {"id": "B", "label": "Aceitar o convite e sair", "amor_delta": 8, "mensagem": "Aceitaste o apoio. Estás a recuperar com companhia."},
            ],
        },
    ],
    "novos": [
        {
            "id": "hobbies",
            "nome": "Hobbies novos",
            "situacao": "Encontraste um novo hobby que te desperta curiosidade.",
            "tempo": tempo_tarefa_segundos,
            "opcoes": [
                {"id": "A", "label": "Guardar a ideia para depois", "amor_delta": -5, "mensagem": "Deixaste a oportunidade passar. Sentes-te mais parado/a."},
                {"id": "B", "label": "Experimentar algo novo hoje", "amor_delta": 8, "mensagem": "Experimentaste algo novo. Estás a abrir espaço para uma nova versão tua."},
            ],
        },
        {
            "id": "exercicio",
            "nome": "Exercício físico",
            "situacao": "O teu corpo pede movimento hoje.",
            "tempo": tempo_tarefa_segundos,
            "opcoes": [
                {"id": "A", "label": "Ficar no sofá e adiar", "amor_delta": -5, "mensagem": "Adiaste o movimento. Acabaste por te sentir mais pesado/a."},
                {"id": "B", "label": "Mover-te com um pequeno treino", "amor_delta": 8, "mensagem": "Fizeste exercício. A tua energia mudou para melhor."},
            ],
        },
        {
            "id": "experiencias",
            "nome": "Novas experiências",
            "situacao": "Surge uma oportunidade para algo diferente.",
            "tempo": tempo_tarefa_segundos,
            "opcoes": [
                {"id": "A", "label": "Manter a zona de conforto", "amor_delta": -5, "mensagem": "Evitar a novidade deixa-te mais estagnado/a."},
                {"id": "B", "label": "Dizer sim e aceitar", "amor_delta": 8, "mensagem": "Aceitaste a experiência. Estás a recuperar com coragem."},
            ],
        },
    ],
}


class Database:
    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.create_tables()

    def connect(self):
        return dbapi2.connect(self.dbfile)

    def create_tables(self):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS USER (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    USERNAME TEXT UNIQUE NOT NULL,
                    EMAIL TEXT UNIQUE NOT NULL,
                    PASSWORD TEXT NOT NULL,
                    AMOR_PROPRIO INTEGER DEFAULT 4,
                    LAGRIMAS INTEGER DEFAULT 60
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS SLOT (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    USER_ID INTEGER NOT NULL,
                    NUMERO INTEGER NOT NULL,
                    ESTADO TEXT DEFAULT 'vazio',
                    TIPO TEXT,
                    ETAPA INTEGER DEFAULT 0,
                    CONSTRUCAO_FIM TEXT,
                    TAREFA_FIM TEXT,
                    TAREFA_NOME TEXT,
                    TAREFA_CORRETA INTEGER DEFAULT 0,
                    FOREIGN KEY (USER_ID) REFERENCES USER(ID)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS HISTORICO (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    USER_ID INTEGER NOT NULL,
                    TEXTO TEXT NOT NULL,
                    CREATED_AT TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (USER_ID) REFERENCES USER(ID)
                )
                """
            )
            connection.commit()

    def create_user(self, username, email, password):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO USER (USERNAME, EMAIL, PASSWORD, AMOR_PROPRIO, LAGRIMAS) VALUES (?, ?, ?, ?, ?)",
                (username, email, hasher.hash(password), amor_proprio_inicial, lagrimas_iniciais),
            )
            user_id = cursor.lastrowid
            for numero, tipo in SLOT_TIPOS.items():
                cursor.execute(
                    "INSERT INTO SLOT (USER_ID, NUMERO, TIPO, ETAPA) VALUES (?, ?, ?, ?)",
                    (user_id, numero, tipo, 0),
                )
            connection.commit()
            return user_id

    def add_history(self, user_id, texto):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO HISTORICO (USER_ID, TEXTO) VALUES (?, ?)", (user_id, texto))
            connection.commit()

    def get_history(self, user_id):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT TEXTO, CREATED_AT FROM HISTORICO WHERE USER_ID = ? ORDER BY ID DESC LIMIT 4",
                (user_id,),
            )
            return [{"texto": row[0], "created_at": row[1]} for row in cursor.fetchall()]

    def username_or_email_exists(self, username, email):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT ID FROM USER WHERE USERNAME = ? OR EMAIL = ?", (username, email))
            return cursor.fetchone() is not None

    def get_user_by_id(self, user_id):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT ID, USERNAME, EMAIL, PASSWORD, AMOR_PROPRIO, LAGRIMAS FROM USER WHERE ID = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if row:
                return User(row[0], row[1], row[2], row[3], row[4], row[5])
            return None

    def get_user_by_username(self, username):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT ID, USERNAME, EMAIL, PASSWORD, AMOR_PROPRIO, LAGRIMAS FROM USER WHERE USERNAME = ?",
                (username,),
            )
            row = cursor.fetchone()
            if row:
                return User(row[0], row[1], row[2], row[3], row[4], row[5])
            return None

    def get_slots_by_user(self, user_id):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT ID, USER_ID, NUMERO, ESTADO, TIPO, ETAPA, CONSTRUCAO_FIM, TAREFA_FIM, TAREFA_NOME, TAREFA_CORRETA
                FROM SLOT
                WHERE USER_ID = ?
                ORDER BY NUMERO
                """,
                (user_id,),
            )
            return [self.slot_from_row(row) for row in cursor.fetchall()]

    def get_slot_by_user_and_number(self, user_id, numero):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT ID, USER_ID, NUMERO, ESTADO, TIPO, ETAPA, CONSTRUCAO_FIM, TAREFA_FIM, TAREFA_NOME, TAREFA_CORRETA
                FROM SLOT
                WHERE USER_ID = ? AND NUMERO = ?
                """,
                (user_id, numero),
            )
            row = cursor.fetchone()
            return self.slot_from_row(row) if row else None

    def get_top_users(self):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT ID, USERNAME, AMOR_PROPRIO FROM USER ORDER BY AMOR_PROPRIO DESC LIMIT 10")
            return [{"id": row[0], "username": row[1], "amor_proprio": row[2]} for row in cursor.fetchall()]

    def start_slot_build(self, slot_id, user_id, lagrimas, fim):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE USER SET LAGRIMAS = ? WHERE ID = ?", (lagrimas, user_id))
            cursor.execute(
                "UPDATE SLOT SET ESTADO = ?, ETAPA = ?, CONSTRUCAO_FIM = ?, TAREFA_CORRETA = ? WHERE ID = ?",
                ("construindo", 1, fim, 0, slot_id),
            )
            connection.commit()

    def finish_slot_build(self, slot_id):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE SLOT SET ESTADO = ?, CONSTRUCAO_FIM = NULL WHERE ID = ?", ("ativo", slot_id))
            connection.commit()

    def start_slot_task(self, slot_id, user_id, amor, lagrimas, tarefa_nome, tarefa_fim, correta):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE USER SET AMOR_PROPRIO = ?, LAGRIMAS = ? WHERE ID = ?", (amor, lagrimas, user_id))
            cursor.execute(
                "UPDATE SLOT SET ESTADO = ?, TAREFA_NOME = ?, TAREFA_FIM = ?, TAREFA_CORRETA = ? WHERE ID = ?",
                ("processando", tarefa_nome, tarefa_fim, 1 if correta else 0, slot_id),
            )
            connection.commit()

    def mark_slot_completed(self, slot_id):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE SLOT SET ESTADO = ? WHERE ID = ?", ("concluida", slot_id))
            connection.commit()

    def advance_slot(self, slot_id, etapa):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE SLOT SET ESTADO = ?, TAREFA_NOME = NULL, TAREFA_FIM = NULL, ETAPA = ?, TAREFA_CORRETA = 0 WHERE ID = ?",
                ("ativo", etapa, slot_id),
            )
            connection.commit()

    def retry_slot(self, slot_id):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE SLOT SET ESTADO = ?, TAREFA_NOME = NULL, TAREFA_FIM = NULL, TAREFA_CORRETA = 0 WHERE ID = ?",
                ("ativo", slot_id),
            )
            connection.commit()

    def finalize_slot(self, slot_id):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE SLOT SET ESTADO = ?, TAREFA_NOME = NULL, TAREFA_FIM = NULL, TAREFA_CORRETA = 0 WHERE ID = ?",
                ("finalizado", slot_id),
            )
            connection.commit()

    def update_user_resources(self, user_id, amor, lagrimas):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE USER SET AMOR_PROPRIO = ?, LAGRIMAS = ? WHERE ID = ?", (amor, lagrimas, user_id))
            connection.commit()

    def reward_tears(self, user_id, amount):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE USER SET LAGRIMAS = LAGRIMAS + ? WHERE ID = ?", (amount, user_id))
            connection.commit()

    def reset_user_game(self, user_id):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE USER SET AMOR_PROPRIO = ?, LAGRIMAS = ? WHERE ID = ?",
                (amor_proprio_inicial, lagrimas_iniciais, user_id),
            )
            cursor.execute(
                "UPDATE SLOT SET ESTADO = ?, ETAPA = 0, CONSTRUCAO_FIM = NULL, TAREFA_FIM = NULL, TAREFA_NOME = NULL, TAREFA_CORRETA = 0 WHERE USER_ID = ?",
                ("vazio", user_id),
            )
            connection.commit()

    def all_slots_finished(self, user_id):
        slots = self.get_slots_by_user(user_id)
        return len(slots) == len(SLOT_TIPOS) and all(slot["estado"] == "finalizado" for slot in slots)

    def slot_from_row(self, row):
        return {
            "id": row[0],
            "user_id": row[1],
            "numero": row[2],
            "estado": row[3],
            "tipo": row[4],
            "etapa": row[5],
            "construcao_fim": row[6],
            "tarefa_fim": row[7],
            "tarefa_nome": row[8],
            "tarefa_correta": row[9],
        }
