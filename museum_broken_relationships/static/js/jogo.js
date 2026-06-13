// =============================================
// MUSEUM OF BROKEN RELATIONSHIPS - Jogo JS
// =============================================s

let currentSlot = null;
// placeholder for tarefas data; will be populated from template JSON
var TAREFAS_DATA = {};

// Tempos de construção em segundos (têm de coincidir com o backend)
const TEMPOS_CONSTRUCAO = {
    'bau': 3,
    'arquivo': 3,
    'mente': 3
};

// ---- MODAL ----

function abrirMenuConstruir(numSlot) {
    currentSlot = numSlot;
    document.getElementById('modal-construir-slot-info').textContent = 'Slot ' + numSlot;
    document.getElementById('modal-construir').style.display = 'flex';
}

function abrirMenuTarefas(numSlot, tipo) {
    currentSlot = numSlot;
    const tarefas = TAREFAS_DATA[tipo] || [];
    const container = document.getElementById('opcoes-tarefas-lista');
    container.innerHTML = '';

    tarefas.forEach(function(t) {
        const tempoTexto = t.tempo < 60 ? t.tempo + 's' : Math.floor(t.tempo / 60) + ' min';
        const hint = t.hint ? `<span class="opcao-hint">${t.hint}</span>` : '<span class="opcao-hint">Resultado incerto</span>';
        const div = document.createElement('div');
        div.className = 'opcao-tarefa';
        div.innerHTML = `
            <strong>${t.nome}</strong>
            <span>💧 ${t.lagrimas} Lágrimas</span>
            <span>⏱ ${tempoTexto}</span>
            ${hint}
        `;
        // marcar para event delegation (substitui onclick inline)
        div.setAttribute('data-action', 'darOrdem');
        div.setAttribute('data-slot', numSlot);
        div.setAttribute('data-tarefa-id', t.id);
        container.appendChild(div);
    });

    document.getElementById('modal-tarefas').style.display = 'flex';
}

// Event delegation: trata elementos com data-action
document.addEventListener('click', function(e) {
    let el = e.target;
    while (el && el !== document) {
        if (el.dataset && el.dataset.action) {
            const action = el.dataset.action;
            const slot = el.dataset.slot ? parseInt(el.dataset.slot) : null;
            const tipo = el.dataset.tipo || null;
            const tarefaId = el.getAttribute('data-tarefa-id');

            if (action === 'abrirMenuConstruir' && slot) {
                abrirMenuConstruir(slot);
            } else if (action === 'abrirMenuTarefas' && slot && tipo) {
                abrirMenuTarefas(slot, tipo);
            } else if (action === 'construir' && tipo) {
                construir(currentSlot, tipo);
            } else if (action === 'recolher' && slot) {
                recolher(slot);
            } else if (action === 'fecharModal') {
                fecharModal();
            } else if (action === 'darOrdem' && slot && tarefaId) {
                darOrdem(slot, tarefaId);
            }

            break;
        }
        el = el.parentNode;
    }
});

function fecharModal() {
    document.getElementById('modal-construir').style.display = 'none';
    document.getElementById('modal-tarefas').style.display = 'none';
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
    const el = document.getElementById('notificacao');
    el.textContent = msg;
    el.style.display = 'block';
    setTimeout(function() {
        el.style.display = 'none';
    }, 4000);
}

// ---- ATUALIZAR RECURSOS NA NAVBAR ----

function atualizarRecursos(amor, lagrimas, estado) {
    const elAmor = document.getElementById('amor-valor');
    const elLag = document.getElementById('lagrimas-valor');
    const elBar = document.getElementById('amor-progresso');
    const elEstado = document.getElementById('estado-emocional');
    if (elAmor && amor !== null && amor !== undefined) elAmor.textContent = amor;
    if (elLag && lagrimas !== null && lagrimas !== undefined) elLag.textContent = lagrimas;
    if (elBar && amor !== null && amor !== undefined) elBar.style.width = Math.max(0, Math.min(100, amor)) + '%';
    if (elEstado && estado) elEstado.textContent = estado;
}

// ---- CONSTRUIR ----

function construir(numSlot, tipo) {
    fecharModal();
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
            atualizarRecursos(data.amor_proprio, null, data.estado_emocional);
            mostrarNotificacao('🔨 Construção iniciada! Aguarda a conclusão.');
            setTimeout(function() { location.reload(); }, 500);
        }
    })
    .catch(function(err) {
        mostrarNotificacao('❌ Erro de ligação ao servidor.');
    });
}

// ---- DAR ORDEM ----

function darOrdem(numSlot, tarefaId) {
    fecharModal();
    fetch('/api/dar_ordem', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot: numSlot, tarefa_id: tarefaId })
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        if (data.erro) {
            mostrarNotificacao('❌ ' + data.erro);
        } else {
            atualizarRecursos(null, data.lagrimas);
            mostrarNotificacao('⏳ Tarefa iniciada! Volta quando estiver pronta.');
            setTimeout(function() { location.reload(); }, 500);
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
        if (data.erro) {
            mostrarNotificacao('❌ ' + data.erro);
        } else {
            const oldEstado = document.getElementById('estado-emocional')?.textContent;
            atualizarRecursos(data.amor_proprio, data.lagrimas, data.estado_emocional);
            mostrarNotificacao(data.mensagem || '🎉 Tarefa concluída!');
            if (data.estado_emocional && oldEstado && data.estado_emocional !== oldEstado) {
                setTimeout(function() {
                    mostrarNotificacao('🎉 Novo Estado Desbloqueado! ' + oldEstado + ' → ' + data.estado_emocional);
                }, 1200);
            }
            setTimeout(function() { location.reload(); }, 1000);
        }
    })
    .catch(function(err) {
        mostrarNotificacao('❌ Erro de ligação ao servidor.');
    });
}

// ---- CONTADORES / BARRAS DE PROGRESSO ----
// Esta função gere as contagens decrescentes nos slots que estão a construir ou processando

function iniciarContadores() {
    const slots = document.querySelectorAll('.slot');
    slots.forEach(function(slotEl) {
        const estado = slotEl.dataset.estado;
        const numSlot = parseInt(slotEl.dataset.numero);

        if (estado === 'construindo' || estado === 'processando') {
            // Pede ao servidor quantos segundos restam
            const rota = estado === 'construindo' ? '/api/verificar_construcao' : '/api/verificar_tarefa';
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

                let segundos = data.segundos_restantes || 0;

                // Calcula tempo total para a barra
                let tipoSlot = slotEl.dataset.tipo;
                let tempoTotal = 60;
                if (estado === 'construindo' && TEMPOS_CONSTRUCAO[tipoSlot]) {
                    tempoTotal = TEMPOS_CONSTRUCAO[tipoSlot];
                } else {
                    // Para tarefas, estimamos o tempo total a partir dos dados JS
                    // (simplificado: usamos os segundos restantes como referência)
                    tempoTotal = segundos > 0 ? segundos * 1.1 : 60;
                }

                const contadorEl = document.getElementById('contador-' + numSlot);
                const barraEl = document.getElementById('barra-' + numSlot);

                // Atualiza a cada segundo
                const intervalo = setInterval(function() {
                    if (segundos <= 0) {
                        clearInterval(intervalo);
                        if (contadorEl) contadorEl.textContent = 'Pronto! A recarregar...';
                        if (barraEl) barraEl.style.width = '100%';
                        setTimeout(function() { location.reload(); }, 800);
                        return;
                    }

                    segundos--;
                    const progresso = Math.min(100, ((tempoTotal - segundos) / tempoTotal) * 100);
                    if (barraEl) barraEl.style.width = progresso + '%';
                    if (contadorEl) contadorEl.textContent = formatarTempo(segundos);
                }, 1000);
            })
            .catch(function() {
                // Se falhar, só não mostra o contador
            });
        }
    });
}

function formatarTempo(segundos) {
    if (segundos < 60) {
        return segundos + 's';
    }
    const min = Math.floor(segundos / 60);
    const seg = segundos % 60;
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
            atualizarRecursos(data.amor_proprio, data.lagrimas, data.estado_emocional);

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
