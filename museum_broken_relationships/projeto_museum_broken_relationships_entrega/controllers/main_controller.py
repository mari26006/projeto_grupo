import copy
from datetime import UTC, datetime, timedelta

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from models.game_model import (
    BONUS_LAGRIMAS_RESPOSTA_CORRETA,
    CONSTRUCOES,
    CUSTO_DECISAO,
    PUBLICACOES_TAREFA,
    TAREFAS,
    User,
    advance_slot,
    calcular_amor_proprio,
    check_password,
    create_user,
    finalize_slot,
    finish_slot_build,
    garantir_tipos_slots,
    get_db,
    get_estado_emocional,
    get_slot_by_id,
    get_slot_by_user_and_number,
    get_slots_by_user,
    get_top_users,
    get_tipo_por_numero,
    get_user_by_id,
    get_user_by_username,
    hash_password,
    limitar_amor_antes_da_cura,
    mark_slot_completed,
    password_uses_old_hash,
    reset_user_game,
    resolve_publications,
    reward_tears,
    retry_slot,
    start_slot_task,
    start_slot_build,
    str_to_dt,
    todos_slots_finalizados,
    unlock_publications,
    update_user_love,
    update_user_password,
    user_exists,
    validate_login_form,
    validate_register_form,
)

main_controller = Blueprint('main', __name__)


def utc_now():
    return datetime.now(UTC).replace(tzinfo=None)


def get_json_data(required_fields):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, ('Pedido JSON inválido.', 400)
    for field in required_fields:
        if field not in data:
            return None, (f'Campo obrigatório em falta: {field}.', 400)
    return data, None


def is_valid_slot_number(value):
    return type(value) is int and value in range(1, 5)


@main_controller.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_controller.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data, errors = validate_register_form(request.form)
        if len(errors) > 0:
            return render_template('register.html', erro=errors[0], values=request.form)

        conn = get_db()
        try:
            existing = user_exists(conn, data['username'], data['email'])
            if existing:
                return render_template(
                    'register.html',
                    erro='Username ou email já existe!',
                    values=request.form
                )

            hashed = hash_password(data['password'])
            user_id = create_user(conn, data['username'], data['email'], hashed)
            if user_id is None:
                return render_template(
                    'register.html',
                    erro='Username ou email já existe!',
                    values=request.form
                )
        finally:
            conn.close()

        conn = get_db()
        user = get_user_by_id(conn, user_id)
        conn.close()
        login_user(User(user))
        return redirect(url_for('main.dashboard'))

    return render_template('register.html')

@main_controller.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data, errors = validate_login_form(request.form)
        if len(errors) > 0:
            return render_template('login.html', erro=errors[0], values=request.form)

        conn = get_db()
        user = get_user_by_username(conn, data['username'])
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
            update_user_password(conn, user['id'], hash_password(data['password']))
            conn.close()

        login_user(User(user))
        return redirect(url_for('main.dashboard'))

    return render_template('login.html')

@main_controller.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('main.index'))

# =====================
# DASHBOARD
# =====================

@main_controller.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    user = get_user_by_id(conn, current_user.id)
    if not user:
        conn.close()
        logout_user()
        return redirect(url_for('main.login'))

    garantir_tipos_slots(conn, user['id'])
    for slot in get_slots_by_user(conn, user['id']):
        if slot['estado'] == 'construindo':
            fim_construcao = str_to_dt(slot['construcao_fim'])
            if not fim_construcao or utc_now() >= fim_construcao:
                finish_slot_build(conn, slot['id'])
    limitar_amor_antes_da_cura(conn, user['id'], user['amor_proprio'])
    user = get_user_by_id(conn, current_user.id)
    slots = get_slots_by_user(conn, user['id'])
    top_users_data = get_top_users(conn)
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
    if user['publicacoes_disponivel'] and not user['publicacoes_resolvido']:
        publicacoes = copy.deepcopy(PUBLICACOES_TAREFA)
        if user['silenciou_ex']:
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
        top_users=top_users,
        custo_decisao=CUSTO_DECISAO
    )

# =====================
# ROTAS DO JOGO (API)
# =====================

@main_controller.route('/api/construir', methods=['POST'])
@login_required
def construir():
    data, error = get_json_data(('slot',))
    if error:
        return jsonify({'erro': error[0]}), error[1]
    slot_num = data.get('slot')
    if not is_valid_slot_number(slot_num):
        return jsonify({'erro': 'O slot deve ser um número inteiro entre 1 e 4.'}), 400

    conn = get_db()
    user = get_user_by_id(conn, current_user.id)
    slot = get_slot_by_user_and_number(conn, user['id'], slot_num)

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

    construcao = CONSTRUCOES[slot_tipo]
    custo = construcao['custo_lagrimas']
    if user['lagrimas'] < custo:
        conn.close()
        return jsonify({'erro': f'Precisas de {custo} Lágrimas para preparar este espaço.'}), 400

    fim = (utc_now() + timedelta(seconds=construcao['tempo_construcao'])).strftime('%Y-%m-%d %H:%M:%S')
    start_slot_build(conn, slot['id'], user['id'], user['lagrimas'] - custo, fim)
    conn.close()

    return jsonify({
        'sucesso': True,
        'estado_emocional': get_estado_emocional(amor_atual),
        'lagrimas': user['lagrimas'] - custo
    })

@main_controller.route('/api/dar_ordem', methods=['POST'])
@login_required
def dar_ordem():
    data, error = get_json_data(('slot', 'tarefa_id', 'opcao_id'))
    if error:
        return jsonify({'erro': error[0]}), error[1]
    slot_num = data.get('slot')
    tarefa_id = data.get('tarefa_id')
    opcao_id = data.get('opcao_id')
    if not is_valid_slot_number(slot_num) or not isinstance(tarefa_id, str) or not isinstance(opcao_id, str):
        return jsonify({'erro': 'Tipos de dados inválidos.'}), 400

    conn = get_db()
    user = get_user_by_id(conn, current_user.id)
    slot = get_slot_by_user_and_number(conn, user['id'], slot_num)

    if not slot or slot['estado'] != 'ativo':
        conn.close()
        return jsonify({
            'erro': 'Este espaço ainda não está pronto para uma nova decisão. Aguarda a preparação ou recolhe a tarefa atual.'
        }), 400

    etapa = slot['etapa'] or 1

    tarefas_tipo = copy.deepcopy(TAREFAS.get(slot['tipo'], []))
    if slot['tipo'] == 'arquivo' and user['publicacoes_disponivel'] and not user['publicacoes_resolvido']:
        publicacoes = copy.deepcopy(PUBLICACOES_TAREFA)
        if user['silenciou_ex']:
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
    if user['lagrimas'] < CUSTO_DECISAO:
        conn.close()
        return jsonify({'erro': 'Não tens Lágrimas suficientes para tomar uma decisão. Reinicia o jogo para continuar.'}), 400

    resposta_correta = opcao.get('correta', opcao['amor_delta'] > 0)
    amor_delta = opcao['amor_delta']
    if resposta_correta and amor_delta <= 0:
        amor_delta = 8

    novo_amor = calcular_amor_proprio(amor_atual, amor_delta)
    fim = (utc_now() + timedelta(seconds=tarefa['tempo'])).strftime('%Y-%m-%d %H:%M:%S')

    if tarefa_id == 'redes':
        unlock_publications(conn, user['id'], opcao_id == 'B')

    start_slot_task(
        conn,
        slot['id'],
        user['id'],
        novo_amor,
        user['lagrimas'] - CUSTO_DECISAO,
        f"{tarefa['nome']} - {opcao['label']}",
        fim,
        resposta_correta
    )
    conn.close()

    delta_text = f"{amor_delta:+d}"
    return jsonify({
        'sucesso': True,
        'amor_proprio': novo_amor,
        'estado_emocional': get_estado_emocional(novo_amor),
        'mensagem': opcao['mensagem'],
        'delta': delta_text,
        'novo_valor': novo_amor,
        'lagrimas': user['lagrimas'] - CUSTO_DECISAO,
        'resposta_correta': resposta_correta
    })

@main_controller.route('/api/recolher', methods=['POST'])
@login_required
def recolher():
    data, error = get_json_data(('slot',))
    if error:
        return jsonify({'erro': error[0]}), error[1]
    slot_num = data.get('slot')
    if not is_valid_slot_number(slot_num):
        return jsonify({'erro': 'O slot deve ser um número inteiro entre 1 e 4.'}), 400

    conn = get_db()
    user = get_user_by_id(conn, current_user.id)
    slot = get_slot_by_user_and_number(conn, user['id'], slot_num)

    # Permite recolher logo após o contador terminar.
    if slot and slot['estado'] == 'processando' and slot['tarefa_fim']:
        fim = str_to_dt(slot['tarefa_fim'])
        if fim and utc_now() >= fim:
            mark_slot_completed(conn, slot['id'])
            slot = get_slot_by_id(conn, slot['id'])

    if not slot or slot['estado'] != 'concluida':
        conn.close()
        return jsonify({'sem_recolha': True})

    amor_resposta = limitar_amor_antes_da_cura(conn, user['id'], user['amor_proprio'])
    tipo = slot['tipo'] or get_tipo_por_numero(slot['numero'])
    
    tarefas_tipo = copy.deepcopy(TAREFAS.get(tipo, []))
    if tipo == 'arquivo' and user['publicacoes_disponivel'] and not user['publicacoes_resolvido']:
        tarefas_tipo.append(PUBLICACOES_TAREFA)
        
    total_momentos = len(tarefas_tipo)
    proxima_etapa = (slot['etapa'] or 1) + 1
    resposta_correta = slot['tarefa_correta'] == 1
    mostrar_popup_cura = False

    if resposta_correta:
        reward_tears(conn, user['id'], BONUS_LAGRIMAS_RESPOSTA_CORRETA)
        if slot['tarefa_nome'] and slot['tarefa_nome'].startswith('Novas publicações'):
            resolve_publications(conn, user['id'])
            
        if proxima_etapa > total_momentos:
            finalize_slot(conn, slot['id'])
            if todos_slots_finalizados(conn, user['id']):
                amor_resposta = 100
                mostrar_popup_cura = True
                update_user_love(conn, user['id'], amor_resposta)
                mensagem = 'Parabéns! Respondeste corretamente a todos os momentos de todos os espaços.'
            else:
                mensagem = 'Parabéns! Respondeste corretamente a todos os momentos. Espaço concluído.'
        else:
            advance_slot(conn, slot['id'], proxima_etapa)
            mensagem = 'Resposta correta! O próximo momento já está pronto.'
    else:
        retry_slot(conn, slot['id'])
        mensagem = 'A resposta não estava certa. Repete o momento para avançar.'

    conn.commit()
    user = get_user_by_id(conn, user['id'])
    conn.close()

    return jsonify({
        'sucesso': True,
        'amor_proprio': amor_resposta,
        'lagrimas': user['lagrimas'],
        'mensagem': mensagem,
        'estado_emocional': get_estado_emocional(amor_resposta),
        'mostrar_popup_cura': mostrar_popup_cura
    })

@main_controller.route('/reiniciar', methods=['POST'])
@login_required
def reiniciar():
    conn = get_db()
    user = get_user_by_id(conn, current_user.id)
    if not user or (user['amor_proprio'] != 0 and user['lagrimas'] != 0):
        conn.close()
        return redirect(url_for('main.dashboard'))

    reset_user_game(conn, user['id'])
    conn.close()
    
    return redirect(url_for('main.dashboard'))

@main_controller.route('/api/verificar_tarefa', methods=['POST'])
@login_required
def verificar_tarefa():
    data, error = get_json_data(('slot',))
    if error:
        return jsonify({'erro': error[0]}), error[1]
    slot_num = data.get('slot')
    if not is_valid_slot_number(slot_num):
        return jsonify({'erro': 'O slot deve ser um número inteiro entre 1 e 4.'}), 400

    conn = get_db()
    slot = get_slot_by_user_and_number(conn, current_user.id, slot_num)

    if not slot or slot['estado'] not in ('construindo', 'processando'):
        conn.close()
        return jsonify({'erro': 'Slot inválido'}), 400

    campo_fim = 'construcao_fim' if slot['estado'] == 'construindo' else 'tarefa_fim'
    fim = str_to_dt(slot[campo_fim])
    if not fim:
        if slot['estado'] == 'construindo':
            finish_slot_build(conn, slot['id'])
            estado_final = 'ativo'
        else:
            retry_slot(conn, slot['id'])
            conn.commit()
            estado_final = 'ativo'
        conn.close()
        return jsonify({
            'sucesso': True,
            'estado': estado_final,
            'mensagem': 'O temporizador foi recuperado e o espaço está novamente disponível.'
        })
    if utc_now() >= fim:
        if slot['estado'] == 'construindo':
            finish_slot_build(conn, slot['id'])
            estado_final = 'ativo'
            mensagem = f"✨ {CONSTRUCOES[slot['tipo']]['nome']} está pronto!"
        else:
            mark_slot_completed(conn, slot['id'])
            estado_final = 'concluida'
            mensagem = '🎉 A tarefa terminou e pode ser recolhida.'
        conn.close()
        return jsonify({'sucesso': True, 'estado': estado_final, 'mensagem': mensagem})

    segundos = int((fim - utc_now()).total_seconds())
    conn.close()
    return jsonify({'sucesso': False, 'segundos_restantes': segundos})

@main_controller.route('/api/estado')
@login_required
def estado():
    conn = get_db()
    user = get_user_by_id(conn, current_user.id)
    amor_atual = limitar_amor_antes_da_cura(conn, user['id'], user['amor_proprio'])
    slots = get_slots_by_user(conn, user['id'])
    conn.close()

    slots_data = []
    for s in slots:
        seg_restantes = None
        fim_texto = s['construcao_fim'] if s['estado'] == 'construindo' else s['tarefa_fim']
        if fim_texto and s['estado'] in ('construindo', 'processando'):
            fim = str_to_dt(fim_texto)
            if fim:
                seg_restantes = max(0, int((fim - utc_now()).total_seconds()))

        slots_data.append({
            'numero': s['numero'],
            'estado': s['estado'],
            'tipo': s['tipo'],
            'tarefa_nome': s['tarefa_nome'],
            'segundos_restantes': seg_restantes
        })

    return jsonify({
        'amor_proprio': amor_atual,
        'lagrimas': user['lagrimas'],
        'estado_emocional': get_estado_emocional(amor_atual),
        'slots': slots_data
    })
