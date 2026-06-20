# Documentação das rotas

## Páginas

| Rota | Método | Descrição |
|---|---|---|
| `/` | GET | Página inicial |
| `/register` | GET, POST | Registo de utilizador |
| `/login` | GET, POST | Login |
| `/logout` | GET | Logout |
| `/dashboard` | GET | Dashboard do jogo |
| `/construir` | POST | Preparar um espaço |
| `/dar-ordem` | POST | Iniciar uma tarefa |
| `/recolher` | POST | Recolher uma tarefa |
| `/reiniciar` | POST | Reiniciar o jogo quando possível |

## Rotas usadas com Fetch API

### POST `/api/construir`

Prepara um espaço.

Pedido:

```json
{
  "slot": 1
}
```

Resposta:

```json
{
  "sucesso": true,
  "mensagem": "Espaço em preparação.",
  "amor_proprio": 4,
  "lagrimas": 57,
  "estado_emocional": "Desolado"
}
```

### POST `/api/dar_ordem`

Inicia uma tarefa/decisão.

Pedido:

```json
{
  "slot": 1,
  "tarefa_id": "roupas",
  "opcao_id": "B"
}
```

Resposta:

```json
{
  "sucesso": true,
  "mensagem": "Tarefa iniciada.",
  "amor_proprio": 12,
  "lagrimas": 56,
  "estado_emocional": "Desolado"
}
```

### POST `/api/recolher`

Recolhe uma tarefa concluída.

Pedido:

```json
{
  "slot": 1
}
```

Resposta:

```json
{
  "sucesso": true,
  "mensagem": "Tarefa recolhida com sucesso.",
  "amor_proprio": 12,
  "lagrimas": 58,
  "estado_emocional": "Desolado"
}
```

### GET `/api/estado`

Devolve o estado atual dos recursos e slots.

Resposta:

```json
{
  "amor_proprio": 12,
  "lagrimas": 58,
  "estado_emocional": "Desolado",
  "slots": [
    {
      "numero": 1,
      "estado": "processando",
      "segundos_restantes": 120,
      "total_segundos": 300
    }
  ]
}
```

### POST `/api/verificar_tarefa`

Verifica o estado de um slot que está a construir ou a processar uma tarefa.

Pedido:

```json
{
  "slot": 1
}
```

Resposta:

```json
{
  "estado": "construindo",
  "segundos_restantes": 59,
  "mensagem": ""
}
```
