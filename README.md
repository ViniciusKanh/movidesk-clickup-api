<p align="center">
  <strong>Movidesk ClickUp API</strong>
</p>

<p align="center">
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue"></a>
  <a href="https://fastapi.tiangolo.com/"><img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-ready-009688"></a>
  <a href="https://www.docker.com/"><img alt="Docker" src="https://img.shields.io/badge/Docker-ready-2496ED"></a>
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/license-Apache%202.0-green"></a>
</p>

API FastAPI para receber webhooks do Movidesk, consultar o ticket completo, validar regras de elegibilidade e criar tarefas no ClickUp com descrição operacional rica.

O projeto foi desenhado para ser configurável por ambiente. Nenhum token, e-mail, lista, URL privada ou regra de negócio específica precisa ficar no código.

## Sumário

- [Visão Geral](#visão-geral)
- [Fluxo](#fluxo)
- [Funcionalidades](#funcionalidades)
- [Arquitetura](#arquitetura)
- [Estrutura](#estrutura)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Rodando Localmente](#rodando-localmente)
- [Docker](#docker)
- [Hugging Face Spaces](#hugging-face-spaces)
- [Deploy na Vercel](#deploy-na-vercel)
- [Painel Administrativo](#painel-administrativo)
- [Banco de Dados](#banco-de-dados)
- [ClickUp](#clickup)
- [Movidesk](#movidesk)
- [Endpoints](#endpoints)
- [Testes](#testes)
- [Segurança](#segurança)
- [Publicação no GitHub](#publicação-no-github)

## Visão Geral

Esta API automatiza um fluxo comum de operação:

1. Um ticket é criado ou atualizado no Movidesk.
2. Um gatilho do Movidesk chama o endpoint de webhook da API.
3. A API extrai o ID do ticket do payload.
4. A API consulta o ticket completo no Movidesk.
5. A API valida se o ticket pode virar tarefa.
6. A API consulta a lista de destino do ClickUp.
7. A API cria a tarefa no ClickUp.
8. A API registra logs da integração no banco.
9. Opcionalmente, a API atualiza campos adicionais do ticket no Movidesk.

## Fluxo

```mermaid
sequenceDiagram
    participant M as Movidesk
    participant A as FastAPI
    participant DB as Database
    participant C as ClickUp

    M->>A: POST /webhooks/movidesk/clickup
    A->>A: Extract ticket ID
    A->>DB: Check duplicate integration
    A->>M: GET full ticket
    A->>A: Validate rules
    A->>DB: Resolve active/default ClickUp list
    A->>C: Create task
    A->>DB: Save integration log
    opt ENABLE_MOVIDESK_UPDATE=true
        A->>M: PATCH ticket custom fields
    end
    A-->>M: JSON response
```

## Funcionalidades

| Área | Recurso |
| --- | --- |
| Webhook | Recebe payloads variados do Movidesk e extrai o ID de múltiplos formatos |
| Segurança | Suporte opcional a `WEBHOOK_SECRET` |
| Movidesk | Consulta ticket completo com clientes, responsável, ações e campos adicionais |
| Validação | Regras configuráveis por serviço, status, campo de criação e link ClickUp |
| ClickUp | Cria task em lista ativa no banco ou lista padrão por variável |
| Responsável | Atribui responsável por ID, e-mail ou usuário autenticado do token |
| Status | Define status inicial da task, por exemplo `Open` |
| Banco | SQLAlchemy com SQLite local, PostgreSQL ou Turso/libSQL |
| Auditoria | Registra eventos em `integration_logs` |
| Deploy | Dockerfile pronto para servidor próprio e Hugging Face Docker Space |

## Arquitetura

```text
Movidesk Trigger
      |
      v
FastAPI webhook
      |
      +--> Movidesk API: ticket completo
      |
      +--> Database: duplicidade, listas e logs
      |
      +--> ClickUp API: criação da task
      |
      +--> Movidesk API: atualização opcional dos campos adicionais
```

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
    clickup_service.py
    custom_fields.py
    description_builder.py
    integration_service.py
    movidesk_service.py
    movidesk_update_service.py
  utils/
    logging.py
    security.py
tests/
Dockerfile
docker-compose.yml
requirements.txt
pytest.ini
```

## Variáveis de Ambiente

Crie um `.env` local a partir do `.env.example`. Nunca commite `.env`.

### Movidesk

| Variável | Obrigatória | Descrição |
| --- | --- | --- |
| `MOVIDESK_TOKEN` | Sim | Token da API pública do Movidesk |
| `MOVIDESK_BASE_URL` | Não | Default: `https://api.movidesk.com/public/v1` |
| `MOVIDESK_TICKET_URL_TEMPLATE` | Não | Template para link do ticket. Ex.: `https://example.movidesk.com/Ticket/Edit/{ticket_id}` |
| `ENABLE_MOVIDESK_UPDATE` | Não | Se `true`, tenta atualizar campos adicionais do ticket após sucesso |
| `MOVIDESK_SUCCESS_STATUS_VALUE` | Não | Valor gravado no campo de status da integração. Default: `OK` |

### ClickUp

| Variável | Obrigatória | Descrição |
| --- | --- | --- |
| `CLICKUP_TOKEN` | Sim | Token da API do ClickUp |
| `CLICKUP_BASE_URL` | Não | Default: `https://api.clickup.com/api/v2` |
| `CLICKUP_DEFAULT_LIST_ID` | Não | Lista destino padrão quando não houver lista ativa no banco |
| `CLICKUP_DEFAULT_LIST_NAME` | Não | Nome amigável da lista padrão |
| `CLICKUP_TASK_STATUS` | Não | Status inicial da task (precisa existir exatamente com esse nome na lista do ClickUp). Default: `Open`. Ex.: `Pendente` |
| `CLICKUP_ASSIGNEE_IDS` | Não | IDs numéricos do ClickUp separados por vírgula |
| `CLICKUP_ASSIGNEE_EMAIL` | Não | E-mail usado para tentar resolver o responsável na lista |
| `CLICKUP_ASSIGN_AUTHORIZED_USER` | Não | Se `true`, usa o usuário do token quando aplicável |

### Banco

| Variável | Obrigatória | Descrição |
| --- | --- | --- |
| `DATABASE_URL` | Não | SQLAlchemy URL. Default local: `sqlite:///./movidesk_clickup.db` |
| `TURSO_DATABASE_URL` | Não | URL `libsql://...` do Turso. Se definida, tem prioridade sobre `DATABASE_URL` |
| `TURSO_AUTH_TOKEN` | Se usar Turso | Token do banco Turso |
| `POSTGRES_PASSWORD` | Se usar compose local | Senha usada pelo PostgreSQL do `docker-compose.yml` |

### Regras

| Variável | Obrigatória | Descrição |
| --- | --- | --- |
| `REQUIRED_SERVICE_FIRST_LEVEL` | Não | Primeiro nível de serviço esperado no Movidesk |
| `REQUIRED_SERVICE_SECOND_LEVEL` | Não | Segundo nível de serviço esperado |
| `REQUIRED_SERVICE_THIRD_LEVEL` | Não | Terceiro nível de serviço esperado |
| `REQUIRED_SERVICE_DISPLAY_NAME` | Não | Nome exibido na descrição e mensagens |
| `MOVIDESK_REQUIRED_OWNER_ID` | Não | ID do agente responsável exigido. Maior prioridade |
| `MOVIDESK_REQUIRED_OWNER_EMAIL` | Não | E-mail do responsável exigido (comparado normalizado: trim + lowercase). Usado se `MOVIDESK_REQUIRED_OWNER_ID` estiver vazio |
| `MOVIDESK_REQUIRED_OWNER_NAME` | Não | Nome do responsável exigido, fallback de último caso. Usado só se os dois acima estiverem vazios |
| `WEBHOOK_SECRET` | Não | Se definido, exige o segredo via header `X-Webhook-Secret` **ou** query string `?secret=...` (o Movidesk só suporta URL, não cabeçalhos customizados) |
| `APP_ENV` | Não | `dev`, `staging`, `prod` |
| `LOG_LEVEL` | Não | Default: `INFO` |
| `REQUEST_TIMEOUT_SECONDS` | Não | Timeout das chamadas HTTP |

> Se as três variáveis de responsável ficarem vazias, a integração **não bloqueia por responsável** (comportamento anterior preservado). Configure apenas uma delas — a de maior prioridade que você preencher é a única usada.

### Painel administrativo (`/admin/ui`)

| Variável | Obrigatória | Descrição |
| --- | --- | --- |
| `ADMIN_USERNAME` | Para habilitar o painel | Usuário de login do painel `/admin/ui` |
| `ADMIN_PASSWORD` | Para habilitar o painel | Senha do painel (comparada em texto puro via `secrets.compare_digest`, nunca logada) |
| `ADMIN_SESSION_SECRET` | Recomendado | Chave usada para assinar o cookie de sessão. Gere um valor longo e aleatório |
| `ADMIN_SESSION_TTL_MINUTES` | Não | Duração da sessão em minutos. Default: `480` (8h) |

Se `ADMIN_USERNAME`/`ADMIN_PASSWORD` não estiverem configurados, todas as rotas `/admin/*` (exceto `/admin/ui`, que só mostra a tela de login) retornam `503`, ou seja, o painel fica desabilitado por padrão até você configurá-lo.

## Rodando Localmente

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Crie o `.env`:

```bash
cp .env.example .env
```

Suba a API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Teste:

```bash
curl http://localhost:8000/health
```

Resposta esperada:

```json
{"status":"ok","service":"movidesk-clickup-api"}
```

## Docker

Build:

```bash
docker build -t movidesk-clickup-api .
```

Run:

```bash
docker run --rm -p 8000:8000 --env-file .env movidesk-clickup-api
```

Docker Compose com PostgreSQL:

```bash
docker compose up --build
```

## Hugging Face Spaces

Use um Space do tipo **Docker**.

O `README.md` do Space deve conter:

```yaml
---
title: Movidesk ClickUp API
sdk: docker
app_port: 7860
---
```

O Dockerfile deve subir Uvicorn em `0.0.0.0`:

```dockerfile
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
```

Configure tokens em **Settings > Variables and secrets**. Não envie `.env` para o Space.

## Deploy na Vercel

O projeto inclui `api/index.py` (expõe o `app` FastAPI) e `vercel.json` prontos para deploy serverless.

1. Suba o repositório para o GitHub (sem `.env` — confira que o `.gitignore` está correto).
2. Na Vercel, importe o repositório como novo projeto (framework: **Other**).
3. Em **Settings > Environment Variables**, cadastre todas as variáveis de `.env.example` com os valores reais, com atenção especial a:
   - `TURSO_DATABASE_URL` e `TURSO_AUTH_TOKEN` — **obrigatórios em produção**. A Vercel não tem disco persistente, então `DATABASE_URL` (SQLite) não funciona lá; o banco efetivo em produção precisa ser o Turso.
   - `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_SESSION_SECRET` — habilitam o painel `/admin/ui`.
   - `WEBHOOK_SECRET` — a ação "Acionar Webhook" dos gatilhos do Movidesk só tem campo de URL (sem cabeçalhos customizados), então o segredo precisa ir embutido na própria URL: `https://SEU-PROJETO.vercel.app/webhooks/movidesk/clickup?secret=SEU_WEBHOOK_SECRET`. O endpoint aceita tanto esse `?secret=` quanto o header `X-Webhook-Secret` (útil para outros sistemas que suportem cabeçalhos customizados).
4. Deploy. A API fica disponível em `https://SEU-PROJETO.vercel.app`, com o painel em `https://SEU-PROJETO.vercel.app/admin/ui`.
5. No Movidesk, crie um gatilho (Configurações > Automações > Gatilhos) com condição de disparo "Responsável: Alterado" (+ opcionalmente "Responsável: Igual a" o agente desejado, para restringir) e ação "Acionar Webhook" apontando para a URL acima (com `?secret=...` se `WEBHOOK_SECRET` estiver configurado).

> Ative também a **Vercel Deployment Protection** (ou ao menos mantenha o painel só acessível por quem tem usuário/senha) já que a URL fica pública por padrão.

## Painel Administrativo

Acesse `/admin/ui` para:

- ver qual lista do ClickUp está ativa no mês atual;
- colar o **Folder ID** da pasta do mês e escolher, dentre as listas encontradas nela, qual deve receber as tarefas — a API resolve Folder → List automaticamente, sem você precisar descobrir o List ID manualmente;
- acompanhar o histórico de listas já configuradas por mês;
- consultar os logs de integração mais recentes (criado, ignorado, erro).

O login exige `ADMIN_USERNAME`/`ADMIN_PASSWORD` (configurados por variável de ambiente) e mantém uma sessão via cookie assinado (`ADMIN_SESSION_SECRET`) por `ADMIN_SESSION_TTL_MINUTES` minutos. Repita o passo de configurar pasta/lista todo início de mês, quando a pasta do ClickUp mudar.

## Banco de Dados

As tabelas são criadas automaticamente na inicialização:

```text
clickup_monthly_lists
integration_logs
```

### SQLite

Indicado para testes locais:

```env
DATABASE_URL=sqlite:///./movidesk_clickup.db
```

### PostgreSQL

Indicado para produção tradicional:

```env
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/database
```

### Turso

Indicado para deploy simples com libSQL:

```env
TURSO_DATABASE_URL=libsql://your-database-your-org.turso.io
TURSO_AUTH_TOKEN=[TURSO_AUTH_TOKEN]
```

Observação: em Windows nativo, a dependência `sqlalchemy-libsql` pode exigir build tools. Para Turso local, prefira Docker ou WSL.

## ClickUp

A API cria tasks pelo endpoint:

```text
POST /list/{list_id}/task
```

Você pode escolher o destino de duas formas.

### Lista padrão por variável

```env
CLICKUP_DEFAULT_LIST_ID=[CLICKUP_LIST_ID]
CLICKUP_DEFAULT_LIST_NAME=[CLICKUP_LIST_NAME]
```

### Lista ativa no banco

```bash
curl -X POST http://localhost:8000/admin/clickup-lists \
  -H "Content-Type: application/json" \
  -d "{\"year\":2026,\"month_number\":6,\"month_name\":\"June\",\"clickup_list_name\":\"June 2026\",\"clickup_list_id\":\"[CLICKUP_LIST_ID]\",\"active\":true}"
```

Se `active=true`, as demais listas são inativadas.

## Movidesk

Crie um gatilho em:

```text
Tickets -> Gatilhos -> Novo gatilho
```

Configuração sugerida (Configurações > Automações > Gatilhos):

| Campo | Valor |
| --- | --- |
| Nome | `Send eligible tickets to ClickUp` |
| Gatilho para | `Tickets` |
| Condição (bloco "TODAS") | `Responsável` `Alterado` — condição de disparo; usar "Alterado" e não "Igual a", que só valida na criação do ticket |
| Condição opcional (mesmo bloco) | `Responsável` `Igual a` `[agente desejado]` — restringe o disparo a esse agente (a API também valida isso de novo com dados atualizados, então é opcional, mas reduz disparos desnecessários) |
| Ação | `Acionar webhook` |
| URL | `https://your-api-domain.example/webhooks/movidesk/clickup` (adicione `?secret=[WEBHOOK_SECRET]` se `WEBHOOK_SECRET` estiver configurado) |

O Movidesk só oferece o campo de URL nessa ação (sem cabeçalhos HTTP customizados), então o segredo **precisa** ir na própria URL como `?secret=...`. O endpoint aceita esse formato e, alternativamente, o header `X-Webhook-Secret` para outros sistemas que suportem cabeçalhos customizados. Se não usar segredo, deixe `WEBHOOK_SECRET` vazio e a URL sem `?secret=`.

Use a aba **Logs** do painel (`/admin/ui`) para conferir, para um ticket específico, exatamente por que a integração criaria ou não uma tarefa — inclusive antes de configurar o gatilho, para validar as regras com dados reais.

## Endpoints

### `GET /health`

```bash
curl http://localhost:8000/health
```

### `POST /webhooks/movidesk/clickup`

Payload mínimo para teste manual:

```bash
curl -X POST http://localhost:8000/webhooks/movidesk/clickup \
  -H "Content-Type: application/json" \
  -d "{\"Id\":123456}"
```

Campos aceitos para extração do ID:

```json
{"Id":123456}
{"id":123456}
{"TicketId":123456}
{"ticketId":123456}
{"ticket_id":123456}
{"number":123456}
{"Ticket":{"Id":123456}}
{"ticket":{"id":123456}}
```

Sucesso:

```json
{
  "success": true,
  "message": "Tarefa criada no ClickUp com sucesso.",
  "ticket_id": 123456,
  "clickup_task_id": "[CLICKUP_TASK_ID]",
  "clickup_task_url": "[CLICKUP_TASK_URL]"
}
```

Duplicado:

```json
{
  "success": true,
  "message": "Ticket já integrado anteriormente. Nenhuma nova tarefa foi criada.",
  "ticket_id": 123456
}
```

### `GET /admin/clickup-lists`

Lista as listas cadastradas.

### `POST /admin/clickup-lists`

Cadastra uma lista do ClickUp.

### `PUT /admin/clickup-lists/{id}/activate`

Ativa uma lista e inativa as demais.

### `GET /admin/integration-logs`

Filtros disponíveis:

```text
ticket_id
status
start_date
end_date
limit
```

Exemplo:

```bash
curl "http://localhost:8000/admin/integration-logs?ticket_id=123456"
```

### `POST /admin/login` / `POST /admin/logout` / `GET /admin/me`

Autenticação do painel administrativo (ver [Painel Administrativo](#painel-administrativo)). Todas as rotas `/admin/*` abaixo, exceto login, exigem sessão válida (cookie `HttpOnly`).

### `GET /admin/clickup/folders/{folder_id}/lists`

Consulta as listas existentes dentro de uma pasta (Folder) do ClickUp — usado pelo painel para resolver Folder ID → List ID sem que você precise descobrir o List ID manualmente.

### `POST /admin/clickup/folders/setup`

Ativa, para o mês/ano atual, a lista escolhida a partir de uma pasta. Preenche automaticamente ano/mês e desativa as demais listas.

### `GET /admin/ui`

Painel administrativo (HTML) para configurar a pasta/lista do mês e acompanhar os logs de integração.

## Regras de Validação

A API não cria task quando:

- o payload não contém ID do ticket;
- o ticket não possui assunto;
- o responsável atual do ticket não é o usuário configurado em `MOVIDESK_REQUIRED_OWNER_*` (quando alguma dessas variáveis está definida) — log `IGNORED_OWNER`;
- o ticket está em status bloqueado;
- o serviço do ticket não bate com `REQUIRED_SERVICE_*`, quando configurado;
- o campo `[BI] Criar tarefa no ClickUp?` existe e não está como `Sim`;
- o campo `[BI] Link ClickUp` já está preenchido;
- já existe log `CREATED_SUCCESSFULLY` para o ticket;
- não existe lista ativa nem `CLICKUP_DEFAULT_LIST_ID`.

Status bloqueados:

```text
Resolvido
Fechado
Cancelado
Aguardando Informação
```

## Atualização do Movidesk

Quando `ENABLE_MOVIDESK_UPDATE=true`, a API tenta atualizar:

```text
[BI] ID ClickUp
[BI] Link ClickUp
[BI] Status integração ClickUp
[BI] Mensagem erro integração
```

O Movidesk só retorna e atualiza campos adicionais quando as regras de exibição desses campos estão atingidas no ticket. Se esses campos não aparecem na resposta da API, a criação da task continua funcionando, mas a atualização de volta pode não ocorrer.

## Testes

```bash
python -m compileall app
pytest
```

## Segurança

- Nunca commite `.env`.
- Nunca coloque tokens no README, Dockerfile ou código.
- Use Secrets/Variables no provedor de deploy.
- Use `WEBHOOK_SECRET` sempre que possível; no Movidesk, como a ação de webhook só tem campo de URL, envie o segredo como `?secret=...` na própria URL do gatilho (o endpoint também aceita header `X-Webhook-Secret`, para sistemas que suportem).
- Proteja rotas `/admin` antes de expor em produção pública.
- Revise logs para evitar registrar dados sensíveis.

## Publicação no GitHub

Verifique se não há segredos:

```bash
git status --short
git grep -n "TOKEN\\|SECRET\\|PASSWORD"
```

Commit:

```bash
git add .
git commit -m "Prepare public Movidesk ClickUp API"
git push origin main
```

## Licença

Apache License 2.0. Veja [LICENSE](./LICENSE).
