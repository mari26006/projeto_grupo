// =============================================
// MUSEUM OF BROKEN RELATIONSHIPS - Jogo JS
// =============================================

let currentSlot = null;
// placeholder for tarefas data; will be populated from template JSON
var TAREFAS_DATA = {};
const TEMPO_NOTIFICACAO_MS = 15000;
const TEMPO_RECARREGAR_APOS_MENSAGEM_MS = 7000;

// Tempos de ativação em segundos (têm de coincidir com o backend)
const TEMPOS_ESPACO = {
    'bau': 3,
    'arquivo': 3,
    'mente': 3,
    'novos': 3
};

// ---- MODAL ----

function abrirMenuTarefas(numSlot, tipo) {
    currentSlot = numSlot;
    var slotEl = document.getElementById('slot-' + numSlot);
    var etapa = 1;
    if (slotEl && slotEl.dataset.etapa) {
        etapa = parseInt(slotEl.dataset.etapa, 10);
    }

    var tarefas = TAREFAS_DATA[tipo] || [];
    var tarefa = tarefas[etapa - 1] || tarefas[0];
    var container = document.getElementById('opcoes-tarefas-lista');
    container.innerHTML = '';

    if (!tarefa) {
        container.innerHTML = '<div class="opcao-tarefa"><p>Não há momento disponível neste espaço.</p></div>';
        document.getElementById('modal-tarefas').style.display = 'flex';
        return;
    }

    var card = document.createElement('div');
    card.className = 'opcao-tarefa';
    card.innerHTML = `
        <div class="situacao-tarefa">
            <strong>${tarefa.nome}</strong>
            <p class="modal-momento">Momento ${etapa}</p>
            <p>${tarefa.situacao}</p>
            <p class="modal-pergunta">O que pretendes fazer?</p>
            <p class="texto-custo">⏱ ${tarefa.tempo}s</p>
        </div>
    `;

    for (var i = 0; i < tarefa.opcoes.length; i++) {
        var opcao = tarefa.opcoes[i];
        var botao = document.createElement('button');
        botao.type = 'button';
        botao.className = 'btn btn-opcao';
        botao.textContent = `${opcao.id}. ${opcao.label}`;
        botao.setAttribute('data-action', 'darOrdem');
        botao.setAttribute('data-slot', numSlot);
        botao.setAttribute('data-tarefa-id', tarefa.id);
        botao.setAttribute('data-opcao-id', opcao.id);
        card.appendChild(botao);
    }

    container.appendChild(card);
    document.getElementById('modal-tarefas').style.display = 'flex';
}

// Event delegation: trata elementos com data-action
document.addEventListener('click', function(e) {
    var el = e.target;
    while (el && el !== document && (!el.dataset || !el.dataset.action)) {
        el = el.parentNode;
    }

    if (!el) return;

    var action = el.dataset.action;
    var slot = el.dataset.slot ? parseInt(el.dataset.slot) : null;
    var tipo = el.dataset.tipo || null;
    var tarefaId = el.getAttribute('data-tarefa-id');

    if (action === 'abrirMenuTarefas' && slot && tipo) {
        abrirMenuTarefas(slot, tipo);
    } else if (action === 'construir' && tipo) {
        if (slot) {
            construir(slot, tipo);
        }
    } else if (action === 'recolher' && slot) {
        recolher(slot);
    } else if (action === 'fecharModal') {
        fecharModal();
    } else if (action === 'darOrdem' && slot && tarefaId) {
        var opcaoId = el.dataset.opcaoId || el.getAttribute('data-opcao-id');
        darOrdem(slot, tarefaId, opcaoId);
    }
});

function fecharModal() {
    var tarefasModal = document.getElementById('modal-tarefas');
    if (tarefasModal) tarefasModal.style.display = 'none';
    currentSlot = null;
}

// Fechar modal ao clicar fora
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        fecharModal();
    }
});

// ---- NOTIFICAÇÃO ----

function mostrarNotificacao(msg) {
    var el = document.getElementById('notificacao');
    el.innerHTML = msg.replace(/\n/g, '<br>');
    el.style.display = 'block';
    setTimeout(function() {
        el.style.display = 'none';
    }, TEMPO_NOTIFICACAO_MS);
}

// ---- ATUALIZAR RECURSOS NA NAVBAR ----

function atualizarRecursos(amor, estado) {
    var elAmor = document.getElementById('amor-valor');
    var elBar = document.getElementById('amor-progresso');
    var elEstado = document.getElementById('estado-emocional');
    if (elAmor && amor !== null && amor !== undefined) elAmor.textContent = amor;
    if (elBar && amor !== null && amor !== undefined) elBar.style.width = Math.max(0, Math.min(100, amor)) + '%';
    if (elEstado && estado) elEstado.textContent = estado;
}

// ---- INICIAR ESPAÇO ----

function construir(numSlot, tipo) {
    fecharModal();
    if (!numSlot) {
        mostrarNotificacao('❌ Slot inválido para construir.');
        return;
    }
    fetch('/api/construir', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot: numSlot, tipo: tipo })
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        if (data.erro) {
            mostrarNotificacao('❌ ' + data.erro);
        } else {
            atualizarRecursos(null, data.estado_emocional);
            mostrarNotificacao('✨ A preparar o espaço...');
            setTimeout(function() { location.reload(); }, 500);
        }
    })
    .catch(function(err) {
        mostrarNotificacao('❌ Erro de ligação ao servidor.');
    });
}

// ---- DAR ORDEM ----

function darOrdem(numSlot, tarefaId, opcaoId) {
    fecharModal();
    var estadoEl = document.getElementById('estado-emocional');
    var oldEstado = estadoEl ? estadoEl.textContent : '';
    fetch('/api/dar_ordem', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot: numSlot, tarefa_id: tarefaId, opcao_id: opcaoId })
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        if (data.erro) {
            mostrarNotificacao('❌ ' + data.erro);
        } else {
            atualizarRecursos(data.amor_proprio, data.estado_emocional);
            var deltaMessage = data.delta && data.delta.startsWith('+')
                ? '❤️ Amor-Próprio ' + data.delta
                : '💔 Amor-Próprio ' + data.delta;
            mostrarNotificacao(deltaMessage + '<br>' + data.mensagem + '<br> Novo valor: ' + data.novo_valor + '/100');
            if (data.estado_emocional && oldEstado && data.estado_emocional !== oldEstado) {
                setTimeout(function() {
                    mostrarNotificacao('🎉 Estado emocional mudou: ' + oldEstado + ' → ' + data.estado_emocional);
                }, 1200);
            }
            setTimeout(function() { location.reload(); }, TEMPO_RECARREGAR_APOS_MENSAGEM_MS);
        }
    })
    .catch(function(err) {
        mostrarNotificacao('❌ Erro de ligação ao servidor.');
    });
}

// ---- RECOLHER ----

function recolher(numSlot) {
    fetch('/api/recolher', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot: numSlot })
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        if (data.sem_recolha) return;
        if (data.erro) {
            mostrarNotificacao('❌ ' + data.erro);
        } else {
            var estadoEl = document.getElementById('estado-emocional');
            var oldEstado = estadoEl ? estadoEl.textContent : '';
            atualizarRecursos(data.amor_proprio, data.estado_emocional);
            mostrarNotificacao(data.mensagem || '🎉 Tarefa concluída!');
            if (data.estado_emocional && oldEstado && data.estado_emocional !== oldEstado) {
                setTimeout(function() {
                    mostrarNotificacao('🎉 Novo Estado Desbloqueado! ' + oldEstado + ' → ' + data.estado_emocional);
                }, 1200);
            }
            setTimeout(function() { location.reload(); }, TEMPO_RECARREGAR_APOS_MENSAGEM_MS);
        }
    })
    .catch(function(err) {
        mostrarNotificacao('❌ Erro de ligação ao servidor.');
    });
}

// ---- CONTADORES / BARRAS DE PROGRESSO ----
// Esta função gere as contagens decrescentes nos slots que estão a iniciar ou processando

function iniciarContadores() {
    var slots = document.querySelectorAll('.slot');
    for (var i = 0; i < slots.length; i++) {
        let slotEl = slots[i];
        let estado = slotEl.dataset.estado;
        let numSlot = parseInt(slotEl.dataset.numero);

        if (estado === 'construindo' || estado === 'processando') {
            // Pede ao servidor quantos segundos restam
            let rota = estado === 'construindo' ? '/api/verificar_construcao' : '/api/verificar_tarefa';
            fetch(rota, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ slot: numSlot })
            })
            .then(function(res) { return res.json(); })
            .then(function(data) {
                if (data.estado === 'ativo' || data.estado === 'concluida') {
                    // Terminou enquanto a página carregou, recarrega
                    location.reload();
                    return;
                }

                var segundos = data.segundos_restantes || 0;

                // Calcula tempo total para a barra
                var tipoSlot = slotEl.dataset.tipo;
                var tempoTotal = 60;
                if (estado === 'construindo' && TEMPOS_ESPACO[tipoSlot]) {
                    tempoTotal = TEMPOS_ESPACO[tipoSlot];
                } else {
                    // Para tarefas, estimamos o tempo total a partir dos dados JS
                    // (simplificado: usamos os segundos restantes como referência)
                    tempoTotal = segundos > 0 ? segundos * 1.1 : 60;
                }

                var contadorEl = document.getElementById('contador-' + numSlot);
                var barraEl = document.getElementById('barra-' + numSlot);

                // Atualiza a cada segundo
                var intervalo = setInterval(function() {
                    if (segundos <= 0) {
                        clearInterval(intervalo);
                        if (contadorEl) contadorEl.textContent = 'Pronto! A recarregar...';
                        if (barraEl) barraEl.style.width = '100%';
                        setTimeout(function() { location.reload(); }, 800);
                        return;
                    }

                    segundos--;
                    var progresso = Math.min(100, ((tempoTotal - segundos) / tempoTotal) * 100);
                    if (barraEl) barraEl.style.width = progresso + '%';
                    if (contadorEl) contadorEl.textContent = formatarTempo(segundos);
                }, 1000);
            })
            .catch(function() {
                // Se falhar, só não mostra o contador
            });
        }
    }
}

function formatarTempo(segundos) {
    if (segundos < 60) {
        return segundos + 's';
    }
    var min = Math.floor(segundos / 60);
    var seg = segundos % 60;
    return min + 'm ' + seg + 's';
}

// ---- POLLING: verifica o estado a cada 15 segundos ----
// Isto garante que a página atualiza mesmo que o utilizador não recarregue

function pollingEstado() {
    setInterval(function() {
        fetch('/api/estado')
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.erro) return;

            // Atualiza recursos
            atualizarRecursos(data.amor_proprio, data.estado_emocional);

            // Verifica se algum slot mudou para 'concluida' e deve ser recarregado
            data.slots.forEach(function(s) {
                const slotEl = document.getElementById('slot-' + s.numero);
                if (!slotEl) return;
                const estadoAtual = slotEl.dataset.estado;

                if (estadoAtual !== s.estado) {
                    // O estado mudou, recarregar a página
                    location.reload();
                }
            });
        })
        .catch(function() { /* ignora erros de rede */ });
    }, 15000);
}

// ---- INIT ----
document.addEventListener('DOMContentLoaded', function() {
    // Ler dados JSON embutidos no template (script[type=application/json])
    const tarefasEl = document.getElementById('tarefas-data');
    if (tarefasEl) {
        try {
            TAREFAS_DATA = JSON.parse(tarefasEl.textContent || tarefasEl.innerText || '{}');
        } catch (e) {
            console.error('Falha ao parsear TAREFAS_DATA:', e);
            TAREFAS_DATA = {};
        }
    }
    iniciarContadores();
    pollingEstado();
});
