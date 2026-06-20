from datetime import datetime, timedelta

from flask import current_app, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from passlib.hash import pbkdf2_sha256 as hasher

from models.game_model import (
    BONUS_LAGRIMAS_RESPOSTA_CORRETA,
    CONSTRUCOES,
    CUSTO_DECISAO,
    TAREFAS,
    calcular_amor_proprio,
    dt_to_str,
    get_estado_emocional,
    str_to_dt,
)


def obter_numero_slot(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return 0


def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


def validar_registo(form):
    dados = {}
    erro = None

    username = form.get("username", "").strip()
    if len(username) == 0:
        erro = "Username não pode ser vazio."
    else:
        dados["username"] = username

    email = form.get("email", "").strip()
    if erro is None and len(email) == 0:
        erro = "Email não pode ser vazio."
    elif erro is None and "@" not in email:
        erro = "Email deve conter @."
    else:
        dados["email"] = email

    password = form.get("password", "")
    if erro is None and len(password) == 0:
        erro = "Password não pode ser vazia."
    elif erro is None and len(password) < 6:
        erro = "Password precisa de pelo menos 6 caracteres."
    else:
        dados["password"] = password

    return erro is None, dados, erro


def register():
    if request.method == "GET":
        return render_template("register.html", values={})

    valido, dados, erro = validar_registo(request.form)
    if not valido:
        return render_template("register.html", erro=erro, values=request.form)

    db = current_app.config["db"]
    username = dados["username"]
    email = dados["email"]
    password = dados["password"]

    if db.username_or_email_exists(username, email):
        return render_template("register.html", erro="Username ou email já existe.", values=request.form)

    user_id = db.create_user(username, email, password)
    user = db.get_user_by_id(user_id)
    login_user(user)
    return redirect(url_for("dashboard"))


def validar_login(form):
    dados = {}
    erro = None

    username = form.get("username", "").strip()
    if len(username) == 0:
        erro = "Username não pode ser vazio."
    else:
        dados["username"] = username

    password = form.get("password", "")
    if erro is None and len(password) == 0:
        erro = "Password não pode ser vazia."
    else:
        dados["password"] = password

    return erro is None, dados, erro


def login():
    if request.method == "GET":
        return render_template("login.html", values={})

    valido, dados, erro = validar_login(request.form)
    if not valido:
        return render_template("login.html", erro=erro, values=request.form)

    db = current_app.config["db"]
    user = db.get_user_by_username(dados["username"])

    if user is not None and hasher.verify(dados["password"], user.password):
        login_user(user)
        return redirect(url_for("dashboard"))

    return render_template("login.html", erro="Username ou password incorretos.", values=request.form)


def logout():
    logout_user()
    return redirect(url_for("index"))


def atualizar_slots(db, user_id):
    now = datetime.now()
    for slot in db.get_slots_by_user(user_id):
        if slot["estado"] == "construindo":
            fim = str_to_dt(slot["construcao_fim"])
            if not fim or now >= fim:
                db.finish_slot_build(slot["id"])
                db.add_history(user_id, "Um espaço terminou a preparação.")
        elif slot["estado"] == "processando":
            fim = str_to_dt(slot["tarefa_fim"])
            if not fim or now >= fim:
                db.mark_slot_completed(slot["id"])
                db.add_history(user_id, "Uma tarefa ficou pronta para recolher.")


@login_required
def dashboard():
    db = current_app.config["db"]
    atualizar_slots(db, current_user.id)

    user = db.get_user_by_id(current_user.id)
    slots = db.get_slots_by_user(current_user.id)
    historico = db.get_history(current_user.id)
    top_users = []
    for top_user in db.get_top_users():
        top_users.append({
            "id": top_user["id"],
            "username": top_user["username"],
            "amor_proprio": top_user["amor_proprio"],
            "estado": get_estado_emocional(top_user["amor_proprio"]),
        })

    return render_template(
        "dashboard.html",
        user=user,
        user_estado=get_estado_emocional(user.amor_proprio),
        slots=slots,
        construcoes=CONSTRUCOES,
        tarefas=TAREFAS,
        top_users=top_users,
        custo_decisao=CUSTO_DECISAO,
        historico=historico,
    )


def construir_slot(user_id, slot_num):
    db = current_app.config["db"]
    user = db.get_user_by_id(user_id)
    slot = db.get_slot_by_user_and_number(user_id, slot_num)

    if slot is None or slot["estado"] != "vazio":
        return False, "Slot inválido."

    construcao = CONSTRUCOES[slot["tipo"]]
    custo = construcao["custo_lagrimas"]
    if user.lagrimas < custo:
        return False, "Lágrimas insuficientes."

    fim = dt_to_str(datetime.now() + timedelta(seconds=construcao["tempo_construcao"]))
    db.start_slot_build(slot["id"], user.id, user.lagrimas - custo, fim)
    db.add_history(user.id, "Preparaste " + construcao["nome"] + ".")
    return True, "Espaço em preparação."


@login_required
def construir():
    construir_slot(current_user.id, obter_numero_slot(request.form.get("slot", 0)))
    return redirect(url_for("dashboard"))


def iniciar_tarefa(user_id, slot_num, tarefa_id, opcao_id):
    db = current_app.config["db"]
    user = db.get_user_by_id(user_id)
    slot = db.get_slot_by_user_and_number(user_id, slot_num)

    if slot is None or slot["estado"] != "ativo":
        return False, "Slot inválido.", None

    tarefas_tipo = TAREFAS.get(slot["tipo"], [])
    etapa = slot["etapa"] or 1
    if etapa < 1 or etapa > len(tarefas_tipo):
        return False, "Momento inválido.", None

    tarefa = tarefas_tipo[etapa - 1]
    if tarefa["id"] != tarefa_id:
        return False, "Tarefa inválida.", None

    opcao = None
    for item in tarefa["opcoes"]:
        if item["id"] == opcao_id:
            opcao = item
            break

    if opcao is None:
        return False, "Opção inválida.", None

    if user.lagrimas < CUSTO_DECISAO:
        return False, "Lágrimas insuficientes.", None

    resposta_correta = opcao["amor_delta"] > 0
    novo_amor = calcular_amor_proprio(user.amor_proprio, opcao["amor_delta"])
    fim = dt_to_str(datetime.now() + timedelta(seconds=tarefa["tempo"]))
    db.start_slot_task(
        slot["id"],
        user.id,
        novo_amor,
        user.lagrimas - CUSTO_DECISAO,
        f"{tarefa['nome']} - {opcao['label']}",
        fim,
        resposta_correta,
    )
    db.add_history(user.id, "Escolheste: " + opcao["label"] + ".")
    dados = {
        "amor_proprio": novo_amor,
        "lagrimas": user.lagrimas - CUSTO_DECISAO,
        "estado_emocional": get_estado_emocional(novo_amor),
        "mensagem": opcao["mensagem"],
        "delta": ("+" if opcao["amor_delta"] > 0 else "") + str(opcao["amor_delta"]),
        "novo_valor": novo_amor,
    }
    return True, "Tarefa iniciada.", dados


@login_required
def dar_ordem():
    iniciar_tarefa(
        current_user.id,
        obter_numero_slot(request.form.get("slot", 0)),
        request.form.get("tarefa_id", ""),
        request.form.get("opcao_id", ""),
    )
    return redirect(url_for("dashboard"))


def recolher_slot(user_id, slot_num):
    db = current_app.config["db"]
    atualizar_slots(db, user_id)

    user = db.get_user_by_id(user_id)
    slot = db.get_slot_by_user_and_number(user_id, slot_num)
    if slot is None or slot["estado"] != "concluida":
        return False, "Ainda não há nada para recolher.", None

    tarefas_tipo = TAREFAS.get(slot["tipo"], [])
    proxima_etapa = (slot["etapa"] or 1) + 1

    if slot["tarefa_correta"] == 1:
        db.reward_tears(user.id, BONUS_LAGRIMAS_RESPOSTA_CORRETA)
        if proxima_etapa > len(tarefas_tipo):
            db.finalize_slot(slot["id"])
            db.add_history(user.id, "Concluíste um espaço.")
            if db.all_slots_finished(user.id):
                user = db.get_user_by_id(user.id)
                db.update_user_resources(user.id, 100, user.lagrimas)
                db.add_history(user.id, "Concluíste todos os espaços.")
        else:
            db.advance_slot(slot["id"], proxima_etapa)
            db.add_history(user.id, "Avançaste para o próximo momento.")
        mensagem = "Tarefa recolhida com sucesso."
    else:
        db.retry_slot(slot["id"])
        db.add_history(user.id, "A resposta não estava certa. Repete o momento.")
        mensagem = "A resposta não estava certa. Repete o momento."

    user = db.get_user_by_id(user.id)
    dados = {
        "amor_proprio": user.amor_proprio,
        "lagrimas": user.lagrimas,
        "estado_emocional": get_estado_emocional(user.amor_proprio),
        "mostrar_popup_cura": user.amor_proprio == 100,
    }
    return True, mensagem, dados


@login_required
def recolher():
    recolher_slot(current_user.id, obter_numero_slot(request.form.get("slot", 0)))
    return redirect(url_for("dashboard"))


@login_required
def reiniciar():
    db = current_app.config["db"]
    user = db.get_user_by_id(current_user.id)
    if user.amor_proprio == 0 or user.lagrimas == 0:
        db.reset_user_game(user.id)
        db.add_history(user.id, "Reiniciaste o jogo.")
    return redirect(url_for("dashboard"))


def segundos_restantes(slot):
    fim_texto = slot["construcao_fim"] if slot["estado"] == "construindo" else slot["tarefa_fim"]
    fim = str_to_dt(fim_texto)
    if fim is None:
        return 0
    return max(0, int((fim - datetime.now()).total_seconds()))


@login_required
def api_construir():
    dados = request.get_json() or {}
    ok, mensagem = construir_slot(current_user.id, obter_numero_slot(dados.get("slot", 0)))
    user = current_app.config["db"].get_user_by_id(current_user.id)
    if not ok:
        return jsonify({"erro": mensagem})
    return jsonify({
        "sucesso": ok,
        "mensagem": mensagem,
        "amor_proprio": user.amor_proprio,
        "lagrimas": user.lagrimas,
        "estado_emocional": get_estado_emocional(user.amor_proprio),
    })


@login_required
def api_dar_ordem():
    dados_pedido = request.get_json() or {}
    ok, mensagem, dados_resposta = iniciar_tarefa(
        current_user.id,
        obter_numero_slot(dados_pedido.get("slot", 0)),
        dados_pedido.get("tarefa_id", ""),
        dados_pedido.get("opcao_id", ""),
    )
    if not ok:
        return jsonify({"erro": mensagem})
    if dados_resposta is None:
        dados_resposta = {}
    dados_resposta["sucesso"] = ok
    dados_resposta["mensagem"] = dados_resposta.get("mensagem", mensagem)
    return jsonify(dados_resposta)


@login_required
def api_recolher():
    dados_json = request.get_json() or {}
    ok, mensagem, dados = recolher_slot(current_user.id, obter_numero_slot(dados_json.get("slot", 0)))
    if not ok:
        return jsonify({"sem_recolha": True, "mensagem": mensagem})
    if dados is None:
        dados = {}
    dados["sucesso"] = ok
    dados["mensagem"] = mensagem
    return jsonify(dados)


@login_required
def api_estado():
    db = current_app.config["db"]
    atualizar_slots(db, current_user.id)
    user = db.get_user_by_id(current_user.id)
    slots = []

    for slot in db.get_slots_by_user(current_user.id):
        total = 0
        if slot["estado"] == "construindo":
            total = CONSTRUCOES[slot["tipo"]]["tempo_construcao"]
        elif slot["estado"] == "processando":
            total = 300

        slots.append({
            "numero": slot["numero"],
            "estado": slot["estado"],
            "segundos_restantes": segundos_restantes(slot),
            "total_segundos": total,
        })

    return jsonify({
        "amor_proprio": user.amor_proprio,
        "lagrimas": user.lagrimas,
        "estado_emocional": get_estado_emocional(user.amor_proprio),
        "slots": slots,
    })


@login_required
def api_verificar_tarefa():
    dados = request.get_json() or {}
    slot_num = obter_numero_slot(dados.get("slot", 0))
    db = current_app.config["db"]
    atualizar_slots(db, current_user.id)
    slot = db.get_slot_by_user_and_number(current_user.id, slot_num)

    if slot is None:
        return jsonify({"erro": "Slot inválido."})

    mensagem = ""
    if slot["estado"] == "ativo":
        mensagem = "Espaço pronto para tarefas."
    elif slot["estado"] == "concluida":
        mensagem = "Tarefa pronta para recolher."

    return jsonify({
        "estado": slot["estado"],
        "segundos_restantes": segundos_restantes(slot),
        "mensagem": mensagem,
    })
