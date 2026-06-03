# Museum of Broken Relationships 💔

Projeto final da unidade curricular de Desenvolvimento de Aplicações Web (DAW)  
Instituto Politécnico de Setúbal – ESCE | Ano letivo 2025/2026

---

## Descrição

Jogo web de gestão de recursos com o tema **Museum of Broken Relationships**.  
O utilizador supera uma relação amorosa, transformando o processo de desapego  
numa competição de Amor-Próprio contra outros jogadores.

---

## Como executar o projeto

### 1. Pré-requisitos

- Python 3.10 ou superior instalado
- pip instalado

### 2. Clonar / extrair o projeto

```bash
cd museum_broken_relationships
```

### 3. Criar ambiente virtual

```bash
python -m venv venv
```

Ativar no Windows:
```bash
venv\Scripts\activate
```

Ativar no Mac/Linux:
```bash
source venv/bin/activate
```

### 4. Instalar dependências

```bash
pip install -r requirements.txt
```

### 5. Executar o servidor

```bash
python app.py
```

### 6. Abrir no browser

Aceder a: **http://127.0.0.1:5000**

> Nota: não abra o ficheiro `templates/index.html` diretamente no browser. As páginas são geradas pelo Flask e apenas aparecem corretamente quando vistas através do servidor.

---

## Estrutura do Projeto

```
museum_broken_relationships/
├── app.py                  # Aplicação Flask principal (backend)
├── requirements.txt        # Dependências Python
├── README.md               # Este ficheiro
├── game.db                 # Base de dados SQLite gerada automaticamente
├── templates/
│   ├── base.html           # Template base HTML
│   ├── index.html          # Página inicial
│   ├── login.html          # Página de login
│   ├── register.html       # Página de registo
│   └── dashboard.html      # Dashboard principal do jogo
└── static/
    ├── css/
    │   └── style.css       # Estilos CSS
    └── js/
        └── jogo.js         # Lógica JavaScript do jogo
```

---

## Tecnologias usadas

- **Backend:** Python 3 + Flask + Werkzeug
- **Base de dados:** SQLite
- **Frontend:** HTML5, CSS3 e JavaScript
- **Autenticação:** Flask sessions + cookies
