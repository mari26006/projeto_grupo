// Elementos usados para alterar o tema da página
let themeToggle = document.getElementById('theme-toggle');
let body = document.body;

function aplicarTema(tema) {
    if (tema === 'dark') {
        body.classList.add('dark-mode');
        if (themeToggle) {
            themeToggle.textContent = 'Modo claro';
        }
    } else {
        body.classList.remove('dark-mode');
        if (themeToggle) {
            themeToggle.textContent = 'Modo escuro';
        }
    }
}

function obterTemaPreferido() {
    let temaGuardado = localStorage.getItem('preferred-theme');

    if (temaGuardado) {
        return temaGuardado;
    }

    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
    }

    return 'light';
}

function alterarTema() {
    let proximoTema = 'dark';

    if (body.classList.contains('dark-mode')) {
        proximoTema = 'light';
    }

    localStorage.setItem('preferred-theme', proximoTema);
    aplicarTema(proximoTema);
}

aplicarTema(obterTemaPreferido());

if (themeToggle) {
    themeToggle.addEventListener('click', alterarTema);
}
