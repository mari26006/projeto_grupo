// =============================================
// MUSEUM OF BROKEN RELATIONSHIPS - Jogo JS
// =============================================

let TAREFAS_DATA = {};
let TEMPO_NOTIFICACAO_MS = 15000;
let TEMPO_RECARREGAR_APOS_MENSAGEM_MS = 7000;
let TEMPO_RECARREGAR_APOS_RECOLHA_MS = 900;
let popupCuraMostrado = false;

function formatarDuracao(segundos) {
    if (segundos % 60 === 0) {
        return (segundos / 60) + ' min';
    }
    return segundos + 's';
}

// ---- MODAL ----

function abrirMenuTarefas(numSlot, tipo) {
    let slotEl = document.getElementById('slot-' + numSlot);
    let etapa = 1;
    if (slotEl && slotEl.getAttribute('data-etapa')) {
        etapa = parseInt(slotEl.getAttribute('data-etapa'), 10);
    }

    let tarefas = TAREFAS_DATA[tipo] || [];
    let tarefa = tarefas[etapa - 1] || tarefas[0];
    let container = document.getElementById('opcoes-tarefas-lista');
    container.innerHTML = '';

    if (!tarefa) {
        container.innerHTML = '<div class="opcao-tarefa"><p>Não há momento disponível neste espaço.</p></div>';
        document.getElementById('modal-tarefas').style.display = 'flex';
        return;
    }

    let card = document.createElement('div');
    card.className = 'opcao-tarefa';
    card.innerHTML =
        '<div class="situacao-tarefa">' +
            '<strong>' + tarefa.nome + '</strong>' +
            '<p class="modal-momento">Momento ' + etapa + '</p>' +
            '<p>' + tarefa.situacao + '</p>' +
            '<p class="modal-pergunta">O que pretendes fazer?</p>' +
            '<p class="texto-custo"><i class="fa-solid fa-droplet" style="color: rgb(98, 195, 233);"></i> 1 Lágrima · <i class="fa-solid fa-stopwatch" style="color: rgb(80, 79, 79);"></i> ' + formatarDuracao(tarefa.tempo) + '</p>' +
        '</div>';

    for (let i = 0; i < tarefa.opcoes.length; i++) {
        let opcao = tarefa.opcoes[i];
        let botao = document.createElement('button');
        botao.type = 'button';
        botao.className = 'btn btn-opcao';
        botao.textContent = opcao.id + '. ' + opcao.label;
        botao.setAttribute('data-action', 'darOrdem');
        botao.setAttribute('data-slot', numSlot);
        botao.setAttribute('data-tarefa-id', tarefa.id);
        botao.setAttribute('data-opcao-id', opcao.id);
        card.appendChild(botao);
    }

    container.appendChild(card);
    document.getElementById('modal-tarefas').style.display = 'flex';
}

// Trata os cliques nos botões que possuem o atributo data-action
function obterElementoComAcao(target) {
    if (!target || target === document) {
        return null;
    }

    if (target.closest) {
        return target.closest('[data-action]');
    }

    let el = target;
    while (el && el !== document) {
        if (el.getAttribute && el.getAttribute('data-action')) {
            return el;
        }
        el = el.parentNode;
    }
    return null;
}

document.addEventListener('click', function(e) {
    let el = obterElementoComAcao(e.target);
    if (!el) {
        return;
    }

    let action = el.getAttribute('data-action');
    let slotAttr = el.getAttribute('data-slot');
    let slot = slotAttr ? parseInt(slotAttr, 10) : null;
    let tipo = el.getAttribute('data-tipo') || null;
    let tarefaId = el.getAttribute('data-tarefa-id');

    if (action === 'abrirMenuTarefas' && slot && tipo) {
        abrirMenuTarefas(slot, tipo);
    } else if (action === 'construir' && tipo) {
        if (slot) {
            construir(slot);
        }
    } else if (action === 'recolher' && slot) {
        recolher(slot);
    } else if (action === 'fecharModal') {
        fecharModal();
    } else if (action === 'fecharPopupCura') {
        fecharPopupCura();
    } else if (action === 'darOrdem' && slot && tarefaId) {
        let opcaoId = el.getAttribute('data-opcao-id');
        darOrdem(slot, tarefaId, opcaoId);
    }
});

function fecharModal() {
    let tarefasModal = document.getElementById('modal-tarefas');
    if (tarefasModal) {
        tarefasModal.style.display = 'none';
    }
}

function mostrarPopupCura(deveMostrar) {
    let popup = document.getElementById('popup-cura');

    if (popup && deveMostrar && !popupCuraMostrado) {
        popupCuraMostrado = true;
        popup.style.display = 'flex';
    }
}

function fecharPopupCura() {
    let popup = document.getElementById('popup-cura');

    if (popup) {
        popup.style.display = 'none';
    }

    location.reload();
}

// Fechar modal ao clicar fora
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        fecharModal();
    }
});

// ---- NOTIFICAÇÃO ----

function mostrarNotificacao(msg) {
    let el = document.getElementById('notificacao');
    el.innerHTML = msg.replace(/\n/g, '<br>');
    el.style.display = 'block';
    setTimeout(function() {
        el.style.display = 'none';
    }, TEMPO_NOTIFICACAO_MS);
}

// ---- ATUALIZAR RECURSOS NA NAVBAR ----

function atualizarRecursos(amor, estado, lagrimas) {
    let elAmor = document.getElementById('amor-valor');
    let elBar = document.getElementById('amor-progresso');
    let elEstado = document.getElementById('estado-emocional');
    let elLagrimas = document.getElementById('lagrimas-valor');

    if (elAmor && amor !== null && amor !== undefined) {
        elAmor.textContent = amor;
    }
    if (elBar && amor !== null && amor !== undefined) {
        elBar.style.width = Math.max(0, Math.min(100, amor)) + '%';
    }
    if (elEstado && estado) {
        elEstado.textContent = estado;
    }
    if (elLagrimas && lagrimas !== null && lagrimas !== undefined) {
        elLagrimas.textContent = lagrimas;
    }
}

// ---- INICIAR ESPAÇO ----

function inicializarBarraAmor() {
    let elBar = document.getElementById('amor-progresso');
    if (!elBar) {
        return;
    }

    let amor = parseInt(elBar.getAttribute('data-amor-proprio'), 10);
    if (!isNaN(amor)) {
        atualizarRecursos(amor, null, null);
    }
}

function construir(numSlot) {
    fecharModal();
    if (!numSlot) {
        mostrarNotificacao('<i class="fa-solid fa-x" style="color: rgb(203, 14, 55);"></i> Slot inválido para construir.');
        return;
    }
    fetch('/api/construir', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot: numSlot })
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        if (data.erro) {
            mostrarNotificacao('<i class="fa-solid fa-x" style="color: rgb(203, 14, 55);"></i> ' + data.erro);
        } else {
            atualizarRecursos(null, data.estado_emocional, data.lagrimas);
            mostrarNotificacao('<wa-icon name="star" style="color: rgb(226, 196, 83);"></wa-icon> A preparar o espaço...');
            setTimeout(function() { location.reload(); }, 500);
        }
    })
    .catch(function(err) {
        mostrarNotificacao('<i class="fa-solid fa-x" style="color: rgb(203, 14, 55);"></i> Erro de ligação ao servidor.');
    });
}

// ---- DAR ORDEM ----

function darOrdem(numSlot, tarefaId, opcaoId) {
    fecharModal();
    let estadoEl = document.getElementById('estado-emocional');
    let oldEstado = estadoEl ? estadoEl.textContent : '';
    fetch('/api/dar_ordem', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot: numSlot, tarefa_id: tarefaId, opcao_id: opcaoId })
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        if (data.erro) {
            mostrarNotificacao('<i class="fa-solid fa-x" style="color: rgb(203, 14, 55);"></i> ' + data.erro);
        } else {
            atualizarRecursos(data.amor_proprio, data.estado_emocional, data.lagrimas);
            let deltaMessage = '<i class="fa-solid fa-heart-crack" style="color: rgb(202, 46, 84);"></i> Amor-Próprio ' + data.delta;
            if (data.delta && data.delta.startsWith('+')) {
                deltaMessage = '<i class="fa-solid fa-heart" style="color: rgb(202, 46, 84);"></i> Amor-Próprio ' + data.delta;
            }
            mostrarNotificacao(deltaMessage + '<br>' + data.mensagem + '<br> Novo valor: ' + data.novo_valor + '/100');
            if (data.estado_emocional && oldEstado && data.estado_emocional !== oldEstado) {
                setTimeout(function() {
                    mostrarNotificacao('<i class="fa-solid fa-medal" style="color: rgb(200, 169, 38);"></i> Estado emocional mudou: ' + oldEstado + ' → ' + data.estado_emocional);
                }, 1200);
            }
            setTimeout(function() { location.reload(); }, TEMPO_RECARREGAR_APOS_MENSAGEM_MS);
        }
    })
    .catch(function(err) {
        mostrarNotificacao('<i class="fa-solid fa-x" style="color: rgb(203, 14, 55);"></i> Erro de ligação ao servidor.');
    });
}

// ---- RECOLHER ----

function recolher(numSlot) {
    let botao = document.querySelector('[data-action="recolher"][data-slot="' + numSlot + '"]');

    if (botao) {
        botao.disabled = true;
        botao.textContent = 'A avançar...';
    }

    fetch('/api/recolher', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot: numSlot })
    })
    .then(function(res) { return res.json(); })
    .then(function(data) {
        if (data.erro) {
            mostrarNotificacao('Erro: ' + data.erro);
            restaurarBotaoRecolher(botao);
            return;
        }
        if (data.sem_recolha) {
            mostrarNotificacao('A tarefa ainda está a terminar. Tenta novamente.');
            restaurarBotaoRecolher(botao);
            return;
        }
        if (data.erro) {
            mostrarNotificacao('<i class="fa-solid fa-x" style="color: rgb(203, 14, 55);"></i> ' + data.erro);
            restaurarBotaoRecolher(botao);
        } else {
            let estadoEl = document.getElementById('estado-emocional');
            let oldEstado = estadoEl ? estadoEl.textContent : '';
            atualizarRecursos(data.amor_proprio, data.estado_emocional, data.lagrimas);
            mostrarPopupCura(data.mostrar_popup_cura);
            mostrarNotificacao(data.mensagem || '<i class="fa-solid fa-trophy" style="color: rgb(204, 165, 79);"></i> Tarefa concluída!');
            if (data.estado_emocional && oldEstado && data.estado_emocional !== oldEstado) {
                setTimeout(function() {
                    mostrarNotificacao('<i class="fa-solid fa-trophy" style="color: rgb(204, 165, 79);"></i> Novo Estado Desbloqueado! ' + oldEstado + ' → ' + data.estado_emocional);
                }, 1200);
            }
            if (!data.mostrar_popup_cura) {
                setTimeout(function() { location.reload(); }, TEMPO_RECARREGAR_APOS_RECOLHA_MS);
            }
        }
    })
    .catch(function(err) {
        mostrarNotificacao('<i class="fa-solid fa-x" style="color: rgb(203, 14, 55);"></i> Erro de ligação ao servidor.');
        restaurarBotaoRecolher(botao);
    });
}

function restaurarBotaoRecolher(botao) {
    if (botao) {
        botao.disabled = false;
        botao.innerHTML = 'Tentar seguir em Frente <wa-icon name="star" style="color: rgb(226, 196, 83);"></wa-icon>';
    }
}

// ---- CONTADORES / BARRAS DE PROGRESSO ----
// Esta função gere as contagens decrescentes nos slots que estão a iniciar ou processando

function iniciarContadores() {
    let slots = document.querySelectorAll('.slot');
    for (let i = 0; i < slots.length; i++) {
        let slotEl = slots[i];
        let estado = slotEl.getAttribute('data-estado');
        let numSlot = parseInt(slotEl.getAttribute('data-numero'), 10);

        if (estado === 'processando' || estado === 'construindo') {
            // Pede ao servidor quantos segundos restam
            let rota = '/api/verificar_tarefa';
            fetch(rota, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ slot: numSlot })
            })
            .then(function(res) { return res.json(); })
            .then(function(data) {
                if (data.estado === 'concluida' || data.estado === 'ativo') {
                    mostrarNotificacao(data.mensagem || '<wa-icon name="star" style="color: rgb(226, 196, 83);"></wa-icon> Processo concluído!');
                    setTimeout(function() { location.reload(); }, 900);
                    return;
                }

                let segundos = data.segundos_restantes || 0;

                // Calcula tempo total para a barra
                let tempoTotal = 60;
                tempoTotal = segundos > 0 ? segundos * 1.1 : 60;

                let contadorEl = document.getElementById('contador-' + numSlot);
                let barraEl = document.getElementById('barra-' + numSlot);

                // Atualiza a cada segundo
                let intervalo = setInterval(function() {
                    if (segundos <= 0) {
                        clearInterval(intervalo);
                        if (contadorEl) {
                            contadorEl.textContent = 'Pronto! A recarregar...';
                        }
                        if (barraEl) {
                            barraEl.style.width = '100%';
                        }
                        setTimeout(function() { location.reload(); }, 800);
                        return;
                    }

                    segundos--;
                    let progresso = Math.min(100, ((tempoTotal - segundos) / tempoTotal) * 100);
                    if (barraEl) {
                        barraEl.style.width = progresso + '%';
                    }
                    if (contadorEl) {
                        contadorEl.textContent = formatarTempo(segundos);
                    }
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
    let min = Math.floor(segundos / 60);
    let seg = segundos % 60;
    return min + 'm ' + seg + 's';
}

// ---- POLLING: verifica o estado a cada 15 segundos ----
// Isto garante que a página atualiza mesmo que o utilizador não recarregue

function pollingEstado() {
    setInterval(function() {
        fetch('/api/estado')
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.erro || !Array.isArray(data.slots)) {
                return;
            }

            // Atualiza recursos
            atualizarRecursos(data.amor_proprio, data.estado_emocional, data.lagrimas);

            // Verifica se algum slot mudou para 'concluida' e deve ser recarregado
            data.slots.forEach(function(s) {
                let slotEl = document.getElementById('slot-' + s.numero);
                if (!slotEl) {
                    return;
                }
                let estadoAtual = slotEl.getAttribute('data-estado');

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
    let tarefasEl = document.getElementById('tarefas-data');
    if (tarefasEl) {
        try {
            TAREFAS_DATA = JSON.parse(tarefasEl.textContent || tarefasEl.innerText || '{}');
        } catch (e) {
            console.error('Falha ao parsear TAREFAS_DATA:', e);
            TAREFAS_DATA = {};
        }
    }
    inicializarBarraAmor();
    iniciarContadores();
    pollingEstado();
});
