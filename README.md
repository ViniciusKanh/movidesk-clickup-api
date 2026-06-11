# Movidesk ClickUp API

API em Python/FastAPI para criar tarefas no ClickUp automaticamente a partir de tickets elegíveis do Movidesk para demandas de BI.

## Objetivo da integração

Na Fase 1, quando um ticket do Movidesk for criado ou alterado, um webhook chama esta API. A API extrai o ID do ticket, consulta o ticket completo no Movidesk, valida se ele pertence ao fluxo `GSI > BI > Melhoria/Projeto`, verifica duplicidade, busca a lista mensal ativa do ClickUp no banco e cria uma tarefa no ClickUp.

A Fase 1 não atualiza automaticamente o ticket no Movidesk. A atualização de volta fica preparada para a Fase 2 e permanece desligada por `ENABLE_MOVIDESK_UPDATE=false`.

## Arquitetura

```text
Movidesk webhook -> FastAPI -> Movidesk API -> Banco -> ClickUp API
```

Fluxo resumido:

1. Movidesk dispara webhook.
2. FastAPI recebe o payload e valida `X-Webhook-Secret`.
3. API extrai `ticket_id`.
4. API verifica se já existe log `CREATED_SUCCESSFULLY`.
5. API consulta o ticket completo no Movidesk.
6. API valida serviço, status e campos adicionais de BI.
7. API busca a lista mensal ativa em `clickup_monthly_lists`.
8. API cria tarefa no ClickUp.
9. API registra logs em `integration_logs`.
10. API retorna sucesso ou erro controlado ao Movidesk.

## Estrutura

```text
app/
  main.py
  config.py
  database.py
  models.py
  schemas.py
  routers/
    health.py
    webhooks.py
    admin.py
  services/
    movidesk_service.py
    clickup_service.py
    integration_service.py
    description_builder.py
    movidesk_update_service.py
  utils/
    logging.py
    security.py
tests/
  test_webhook.py
  test_description_builder.py
  test_security.py
  test_integration_service.py
```

## Variáveis de Ambiente

Obrigatórias em produção:

```env
MOVIDESK_TOKEN=[TOKEN_MOVIDESK]
CLICKUP_TOKEN=[TOKEN_CLICKUP]
DATABASE_URL=[DATABASE_URL]
```

`WEBHOOK_SECRET` é opcional. Se ficar vazio ou ausente, a rota do webhook aceita chamadas sem o header `X-Webhook-Secret`.

Defaults seguros da aplicação:

```env
MOVIDESK_BASE_URL=https://api.movidesk.com/public/v1
CLICKUP_BASE_URL=https://api.clickup.com/api/v2
CLICKUP_DEFAULT_LIST_ID=
CLICKUP_DEFAULT_LIST_NAME=Power BI
CLICKUP_TASK_STATUS=Open
CLICKUP_ASSIGNEE_IDS=
CLICKUP_ASSIGNEE_EMAIL=vinicius.souza@penso.com.br
CLICKUP_ASSIGN_AUTHORIZED_USER=true
APP_ENV=dev
LOG_LEVEL=INFO
ENABLE_MOVIDESK_UPDATE=false
MOVIDESK_SUCCESS_STATUS_VALUE=OK
REQUEST_TIMEOUT_SECONDS=30
```

Opcional:

```env
MOVIDESK_TICKET_URL_TEMPLATE=[MOVIDESK_TICKET_URL_TEMPLATE]
```

Use PostgreSQL em produção. SQLite é indicado apenas para desenvolvimento local.

Para `docker compose` local com PostgreSQL, defina também:

```env
POSTGRES_PASSWORD=[POSTGRES_PASSWORD]
```

## Usar Turso como Banco

Sim, o banco pode ser Turso. A URL `https://app.turso.tech/viniciuskanh` é o dashboard da sua conta, não a URL de conexão.

Você precisa criar um database no Turso e obter dois valores:

```env
TURSO_DATABASE_URL=libsql://[NOME_DO_BANCO]-[ORG].turso.io
TURSO_AUTH_TOKEN=[TOKEN_TURSO]
```

Quando `TURSO_DATABASE_URL` estiver preenchido, a aplicação ignora `DATABASE_URL` e usa Turso via SQLAlchemy/libSQL.

Observação para Windows local: a dependência `sqlalchemy-libsql` é instalada automaticamente no Docker/Linux. Em Windows nativo, prefira rodar a API via Docker ou WSL se quiser testar Turso localmente.

Pelo dashboard:

1. Acesse `https://app.turso.tech/viniciuskanh`.
2. Crie um database, por exemplo `movidesk-clickup`.
3. Copie a URL de conexão do banco, no formato `libsql://...turso.io`.
4. Gere um token de acesso para esse database.
5. Configure `TURSO_DATABASE_URL` e `TURSO_AUTH_TOKEN` no `.env` local ou nos Secrets do Hugging Face Space.

Pela CLI do Turso, os comandos equivalentes são:

```bash
turso db create movidesk-clickup
turso db show --url movidesk-clickup
turso db tokens create movidesk-clickup
```

Não coloque o token do Turso no README, Dockerfile ou código.

## Rodar localmente

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Crie o `.env` local a partir do exemplo e preencha com valores reais apenas na sua máquina:

```bash
cp .env.example .env
```

Para desenvolvimento local simples, configure:

```env
DATABASE_URL=sqlite:///./movidesk_clickup.db
```

Suba a API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Healthcheck:

```bash
curl http://localhost:8000/health
```

Resposta:

```json
{"status":"ok","service":"movidesk-clickup-api"}
```

## Rodar com Docker

```bash
docker build -t movidesk-clickup-api .
docker run --rm -p 8000:8000 --env-file .env movidesk-clickup-api
```

Com Docker Compose:

```bash
docker compose up --build
```

O Dockerfile local respeita `PORT` quando a variável existir e usa `8000` como fallback.

## Cadastrar lista mensal ativa

Antes de processar webhooks reais, cadastre a lista mensal ativa do ClickUp. Se `active=true`, todas as demais listas são inativadas.

Como alternativa mais simples, você pode configurar uma lista padrão por variável de ambiente:

```env
CLICKUP_DEFAULT_LIST_ID=901327529184
CLICKUP_DEFAULT_LIST_NAME=Power BI
CLICKUP_TASK_STATUS=Open
CLICKUP_ASSIGNEE_EMAIL=vinicius.souza@penso.com.br
```

Pelo link que você informou, `https://app.clickup.com/37014273/v/b/li/901327529184`, o ID provável da lista é `901327529184`. A API do ClickUp cria tarefas em **Lista**; se `Power BI` for uma pasta, use uma lista dentro dela. Como o link contém `/li/`, ele parece apontar para uma lista.

O ClickUp exige ID numérico para responsável. A aplicação tenta resolver automaticamente pelo e-mail `CLICKUP_ASSIGNEE_EMAIL` na lista e, se o token pertencer ao mesmo e-mail, pelo usuário autenticado. Se quiser evitar qualquer tentativa automática, preencha diretamente:

```env
CLICKUP_ASSIGNEE_IDS=[ID_NUMERICO_DO_USUARIO]
```

Se quiser manter o controle pelo banco, cadastre essa lista como ativa:

```bash
curl -X POST http://localhost:8000/admin/clickup-lists \
  -H "Content-Type: application/json" \
  -d "{\"year\":2026,\"month_number\":6,\"month_name\":\"Junho\",\"clickup_list_name\":\"Power BI\",\"clickup_list_id\":\"901327529184\",\"active\":true}"
```

Listar listas:

```bash
curl http://localhost:8000/admin/clickup-lists
```

Ativar uma lista existente:

```bash
curl -X PUT http://localhost:8000/admin/clickup-lists/1/activate
```

## Testar webhook

Teste com o ticket controlado `717525`.

Se `WEBHOOK_SECRET` estiver vazio, use:

```bash
curl -X POST http://localhost:8000/webhooks/movidesk/clickup \
  -H "Content-Type: application/json" \
  -d "{\"Id\":717525}"
```

Se `WEBHOOK_SECRET` estiver configurado, use:

```bash
curl -X POST http://localhost:8000/webhooks/movidesk/clickup \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: [WEBHOOK_SECRET]" \
  -d "{\"Id\":717525}"
```

Campos aceitos para extração do ID:

```json
{"Id":717525}
{"id":717525}
{"TicketId":717525}
{"ticketId":717525}
{"ticket_id":717525}
{"Ticket":{"Id":717525}}
{"ticket":{"id":717525}}
```

Resposta quando cria tarefa:

```json
{
  "success": true,
  "message": "Tarefa criada no ClickUp com sucesso.",
  "ticket_id": 717525,
  "clickup_task_id": "[ID_TASK]",
  "clickup_task_url": "[URL_TASK]"
}
```

Resposta quando já foi integrado:

```json
{
  "success": true,
  "message": "Ticket já integrado anteriormente. Nenhuma nova tarefa foi criada.",
  "ticket_id": 717525,
  "clickup_task_id": null,
  "clickup_task_url": null
}
```

## Configurar gatilho no Movidesk

Configuração sugerida:

```text
Nome: BI - Enviar para ClickUp via Webhook
Tipo: Tickets
Disparo: ticket criado ou ticket alterado
URL: https://[URL_DA_API]/webhooks/movidesk/clickup
Header: X-Webhook-Secret: [WEBHOOK_SECRET]
Payload: {"Id": "[ID_DO_TICKET]"}
```

Se você não usar `WEBHOOK_SECRET`, deixe esse header fora do gatilho.

Condições recomendadas:

```text
Serviço: GSI > BI > Melhoria/Projeto
Status diferente de Resolvido
Status diferente de Fechado
Status diferente de Cancelado
Status diferente de Aguardando Informação
[BI] Criar tarefa no ClickUp? = Sim, se o campo existir
[BI] Link ClickUp vazio, se o campo existir
```

## Regras de validação

A API não cria tarefa quando:

- o payload não contém ID de ticket;
- o ticket não possui assunto;
- o ticket não pertence a `GSI > BI > Melhoria/Projeto`;
- o ticket está em `Resolvido`, `Fechado`, `Cancelado` ou `Aguardando Informação`;
- `[BI] Criar tarefa no ClickUp?` existe e está diferente de `Sim`;
- `[BI] Link ClickUp` já está preenchido;
- já existe log `CREATED_SUCCESSFULLY` para o mesmo ticket;
- não existe lista mensal ativa do ClickUp.

## Logs

Logs operacionais são emitidos em JSON no stdout. A tabela `integration_logs` registra eventos com payload sanitizado. Chaves como token, senha, secret e authorization são mascaradas.

Consultar logs:

```bash
curl http://localhost:8000/admin/integration-logs
curl "http://localhost:8000/admin/integration-logs?ticket_id=717525"
curl "http://localhost:8000/admin/integration-logs?status=CREATED_SUCCESSFULLY"
```

## Hugging Face Docker Space

A subpasta `movidesk-clickup-api/` está preparada como Hugging Face Space Docker.

No painel do Space, configure os valores reais em **Settings > Variables and secrets**. Não envie `.env` para o Space.

Secrets recomendados:

```text
MOVIDESK_TOKEN
CLICKUP_TOKEN
TURSO_AUTH_TOKEN
```

Variables recomendadas:

```text
MOVIDESK_BASE_URL=https://api.movidesk.com/public/v1
CLICKUP_BASE_URL=https://api.clickup.com/api/v2
TURSO_DATABASE_URL=libsql://[NOME_DO_BANCO]-[ORG].turso.io
CLICKUP_DEFAULT_LIST_ID=901327529184
CLICKUP_DEFAULT_LIST_NAME=Power BI
CLICKUP_TASK_STATUS=Open
CLICKUP_ASSIGNEE_EMAIL=vinicius.souza@penso.com.br
CLICKUP_ASSIGN_AUTHORIZED_USER=true
APP_ENV=prod
LOG_LEVEL=INFO
ENABLE_MOVIDESK_UPDATE=false
REQUEST_TIMEOUT_SECONDS=30
PORT=7860
```

`WEBHOOK_SECRET` e `DATABASE_URL` só precisam ser configurados se você quiser usar, respectivamente, proteção por header ou outro banco que não seja Turso.

O Space Docker usa `app_port: 7860` e o comando Uvicorn escuta em `0.0.0.0`.

## Segurança

- Nunca coloque tokens no código, README, Dockerfile ou commits.
- Nunca versione `.env`.
- Configure segredos reais no Hugging Face pelo painel do Space.
- Use `WEBHOOK_SECRET` em produção quando houver como controlar o header no webhook. Se não houver, deixe vazio e compense com URL difícil de adivinhar, HTTPS e monitoramento de logs.
- Não exponha rotas `/admin` publicamente sem autenticação adicional em produção.
- Revise os logs antes de habilitar o gatilho para muitos tickets.

## Fase 2

Na Fase 2, a atualização automática do Movidesk poderá preencher:

- `[BI] ID ClickUp`
- `[BI] Link ClickUp`
- `[BI] Status integração ClickUp`
- `[BI] Mensagem erro integração`

Para ativar depois que a criação da task no ClickUp estiver validada:

```env
ENABLE_MOVIDESK_UPDATE=true
MOVIDESK_SUCCESS_STATUS_VALUE=OK
```

Quando ativado, a API atualiza os campos adicionais do ticket após criar a task com sucesso. Se o ticket já tiver log `CREATED_SUCCESSFULLY`, uma nova chamada do webhook tenta atualizar os campos no Movidesk sem criar outra task.

## Testes

```bash
python -m compileall app
pytest
```
