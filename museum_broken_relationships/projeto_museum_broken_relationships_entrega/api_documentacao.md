# Documentação da API

Todas as rotas `/api/` exigem autenticação através de Flask-Login e devolvem JSON.

## POST `/api/construir`

Inicia a preparação de um espaço vazio. A preparação consome Lágrimas e demora 1 minuto.

```json
{"slot": 1}
```

Resposta de sucesso:

```json
{"sucesso": true, "lagrimas": 57, "estado_emocional": "💔 Desolado"}
```

## POST `/api/dar_ordem`

Submete uma decisão. Cada decisão custa uma Lágrima e inicia uma tarefa de 5 minutos.

```json
{"slot": 1, "tarefa_id": "roupas", "opcao_id": "B"}
```

Resposta de sucesso:

```json
{
  "sucesso": true,
  "amor_proprio": 12,
  "lagrimas": 56,
  "delta": "+8",
  "novo_valor": 12,
  "estado_emocional": "💔 Desolado",
  "mensagem": "Resultado da decisão",
  "resposta_correta": true
}
```

## POST `/api/verificar_tarefa`

Verifica o temporizador de preparação ou de uma tarefa.

```json
{"slot": 1}
```

Enquanto decorre:

```json
{"sucesso": false, "segundos_restantes": 3}
```

Quando termina:

```json
{"sucesso": true, "estado": "ativo"}
```

O estado final é `ativo` para uma preparação e `concluida` para uma tarefa.

## POST `/api/recolher`

Recolhe uma tarefa concluída. Respostas corretas permitem avançar e recuperam duas Lágrimas.

```json
{"slot": 1}
```

## GET `/api/estado`

Devolve os recursos e o estado atual dos slots.

```json
{
  "amor_proprio": 12,
  "lagrimas": 58,
  "estado_emocional": "💔 Desolado",
  "slots": []
}
```

## Erros

- `400`: pedido inválido, estado incompatível ou recursos insuficientes;
- `401`: utilizador não autenticado;
- `200` com `sem_recolha: true`: a tarefa ainda não pode ser recolhida.

## Rotas de páginas e autenticação

| Rota | Método | Função |
|---|---|---|
| `/` | GET | Página inicial |
| `/register` | GET, POST | Registo |
| `/login` | GET, POST | Login |
| `/logout` | GET | Logout |
| `/dashboard` | GET | Dashboard protegido |
| `/reiniciar` | POST | Reinicia o jogo quando o Amor-Próprio ou as Lágrimas chegam a zero |
