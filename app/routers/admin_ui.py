from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["admin-ui"])

_PAGE = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>ViniciusFlow</title>
<style>
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background:#0f1117; color:#e7e9ee; }
  [hidden] { display:none !important; }

  /* ---- Login ---- */
  #loginScreen { max-width:360px; margin:100px auto; background:#171a23; border:1px solid #262b38; border-radius:12px; padding:28px; }
  #loginScreen h1 { font-size:18px; margin:0 0 4px; }
  #loginScreen p.sub { color:#8b93a7; font-size:13px; margin:0 0 18px; }
  label { display:block; font-size:12px; margin:12px 0 4px; color:#9aa3b8; }
  input[type=text], input[type=password] { width:100%; padding:10px 11px; border:1px solid #2b303e; border-radius:8px; font-size:14px; background:#0f1117; color:#e7e9ee; }
  input:focus { outline:2px solid #5b7cff; border-color:#5b7cff; }
  button { background:#5b7cff; color:#fff; border:none; padding:10px 16px; border-radius:8px; font-size:14px; cursor:pointer; font-weight:600; }
  button.secondary { background:#232838; color:#e7e9ee; }
  button.ghost { background:transparent; color:#9aa3b8; border:1px solid #2b303e; }
  button:disabled { opacity:.45; cursor:not-allowed; }
  .msg { font-size:13px; margin-top:10px; }
  .msg.error { color:#ff6b6b; }
  .msg.success { color:#4ade80; }

  /* ---- App shell ---- */
  #app { display:flex; height:100vh; }
  nav.sidebar { width:210px; flex-shrink:0; background:#12141c; border-right:1px solid #20242f; padding:18px 12px; display:flex; flex-direction:column; }
  nav.sidebar .brand { font-weight:700; font-size:15px; padding:0 8px 18px; display:flex; align-items:center; gap:8px; }
  nav.sidebar .brand .dot { width:9px; height:9px; border-radius:50%; background:#5b7cff; box-shadow:0 0 8px #5b7cff; }
  nav.sidebar button.tab { display:flex; align-items:center; gap:10px; width:100%; text-align:left; background:transparent; color:#9aa3b8; border:none; padding:10px 10px; border-radius:8px; font-size:13px; font-weight:500; margin-bottom:2px; cursor:pointer; }
  nav.sidebar button.tab:hover { background:#1c202c; color:#e7e9ee; }
  nav.sidebar button.tab.active { background:#1c2338; color:#fff; }
  nav.sidebar .spacer { flex:1; }
  nav.sidebar .logout { margin-top:8px; }

  main.content { flex:1; overflow:auto; padding:26px 32px; }
  header.top { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:20px; }
  header.top h2 { margin:0; font-size:19px; }
  header.top p { margin:2px 0 0; color:#8b93a7; font-size:13px; }

  /* ---- Fluxo (canvas estilo n8n) ---- */
  .canvas { position:relative; background:
      radial-gradient(circle, #1c2030 1px, transparent 1px) 0 0/18px 18px;
    background-color:#12141c; border:1px solid #20242f; border-radius:14px; padding:60px 40px; min-height:260px; }
  .flow-row { display:flex; align-items:center; gap:0; position:relative; }
  .node { position:relative; z-index:1; width:250px; background:#181c28; border:1px solid #2b303e; border-radius:12px; padding:16px; cursor:pointer; transition:border-color .15s; }
  .node:hover { border-color:#5b7cff; }
  .node .node-head { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
  .node .icon { width:32px; height:32px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:16px; flex-shrink:0; }
  .node.movidesk .icon { background:#2a1f3d; color:#c084fc; }
  .node.clickup .icon { background:#1f2f26; color:#4ade80; }
  .node .title { font-weight:600; font-size:14px; }
  .node .kind { font-size:10px; text-transform:uppercase; letter-spacing:.04em; color:#6b7386; }
  .node .desc { font-size:12.5px; color:#aab1c2; line-height:1.5; }
  .node .badge-row { margin-top:10px; display:flex; gap:6px; flex-wrap:wrap; }
  .badge { font-size:10.5px; padding:3px 8px; border-radius:999px; font-weight:600; }
  .badge.readonly { background:#2a2540; color:#c4b5fd; }
  .badge.createonly { background:#1c3324; color:#86efac; }
  .badge.ok { background:#1c3324; color:#86efac; }
  .badge.warn { background:#3d2f14; color:#fbbf24; }
  .connector { flex:1; height:2px; background:linear-gradient(90deg,#2b303e,#5b7cff); position:relative; min-width:60px; }
  .connector::after { content:"\\25B8"; position:absolute; right:-2px; top:50%; transform:translateY(-50%); color:#5b7cff; font-size:14px; }
  .safety-banner { margin-top:22px; background:#151b14; border:1px solid #2a3d26; color:#9ae6b4; border-radius:10px; padding:12px 16px; font-size:12.5px; line-height:1.6; }
  .safety-banner b { color:#c6f6d5; }

  /* ---- Panels (config abaixo do canvas) ---- */
  .grid2 { display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-top:22px; }
  .card { background:#181c28; border:1px solid #2b303e; border-radius:12px; padding:20px; }
  .card h3 { margin:0 0 4px; font-size:14px; }
  .card p.hint { color:#7d8598; font-size:12px; margin:2px 0 12px; }
  .kv { font-size:13px; color:#c7cce0; margin:4px 0; }
  .kv b { color:#fff; }
  .list-option { display:flex; align-items:center; gap:8px; padding:9px 10px; border:1px solid #2b303e; border-radius:8px; margin-top:6px; cursor:pointer; font-size:13px; }
  .list-option.selected { border-color:#5b7cff; background:#1c2338; }

  /* ---- Integracoes ---- */
  .integration-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(260px,1fr)); gap:16px; }
  .integration-card { background:#181c28; border:1px solid #2b303e; border-radius:12px; padding:18px; }
  .integration-card.disabled { opacity:.5; border-style:dashed; display:flex; align-items:center; justify-content:center; min-height:150px; font-size:13px; color:#7d8598; }
  .integration-card .head { display:flex; align-items:center; gap:10px; margin-bottom:10px; }
  .integration-card .head .icon { width:34px; height:34px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:17px; }
  .integration-card.movidesk .icon { background:#2a1f3d; color:#c084fc; }
  .integration-card.clickup .icon { background:#1f2f26; color:#4ade80; }
  .integration-card h4 { margin:0; font-size:14px; }
  .integration-card .kv { font-size:12.5px; }

  /* ---- Tabela de logs ---- */
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th, td { text-align:left; padding:8px 10px; border-bottom:1px solid #20242f; }
  th { color:#7d8598; font-weight:600; font-size:11.5px; text-transform:uppercase; letter-spacing:.03em; }
</style>
</head>
<body>

<div id="loginScreen">
  <h1>ViniciusFlow</h1>
  <p class="sub">Movidesk &rarr; ClickUp</p>
  <label>Usuario</label>
  <input id="loginUser" type="text" autocomplete="username" />
  <label>Senha</label>
  <input id="loginPass" type="password" autocomplete="current-password" />
  <button id="loginBtn" style="width:100%; margin-top:16px;">Entrar</button>
  <div id="loginMsg" class="msg"></div>
</div>

<div id="app" hidden>
  <nav class="sidebar">
    <div class="brand"><span class="dot"></span> ViniciusFlow</div>
    <button class="tab active" data-tab="fluxo">&#9881; Fluxo</button>
    <button class="tab" data-tab="integracoes">&#128268; Integracoes</button>
    <button class="tab" data-tab="logs">&#128203; Logs</button>
    <div class="spacer"></div>
    <button class="tab logout ghost" id="logoutBtn">&#8592; Sair</button>
  </nav>

  <main class="content">

    <section id="view-fluxo">
      <header class="top">
        <div><h2>Fluxo</h2><p>Movidesk (leitura) &rarr; ClickUp (criacao de tarefa)</p></div>
      </header>

      <div class="canvas">
        <div class="flow-row">
          <div class="node movidesk" id="nodeMovidesk">
            <div class="node-head">
              <div class="icon">&#128218;</div>
              <div><div class="title">Movidesk</div><div class="kind">Gatilho</div></div>
            </div>
            <div class="desc" id="movideskNodeDesc">Carregando regra de responsavel...</div>
            <div class="badge-row"><span class="badge readonly">somente leitura</span></div>
          </div>
          <div class="connector"></div>
          <div class="node clickup" id="nodeClickup">
            <div class="node-head">
              <div class="icon">&#9989;</div>
              <div><div class="title">ClickUp</div><div class="kind">Acao</div></div>
            </div>
            <div class="desc" id="clickupNodeDesc">Carregando lista ativa...</div>
            <div class="badge-row"><span class="badge createonly">so cria tarefas</span></div>
          </div>
        </div>
        <div class="safety-banner">
          <b>Modo seguro:</b> o Movidesk e usado 100% para leitura (nunca exclui ou altera tickets).
          No ClickUp, a integracao apenas cria tarefas novas na lista escolhida - nunca edita ou apaga
          tarefas existentes de outras pessoas na pasta.
        </div>
      </div>

      <div class="grid2">
        <div class="card">
          <h3>No: Movidesk</h3>
          <p class="hint">Regra que decide quando um ticket vira tarefa.</p>
          <div id="movideskCardBody">Carregando...</div>
        </div>
        <div class="card">
          <h3>No: ClickUp - pasta/lista do mes</h3>
          <p class="hint">Cole o Folder ID da pasta atual e escolha a lista certa.</p>
          <label>Folder ID do ClickUp</label>
          <input id="folderIdInput" type="text" placeholder="Ex: 90123456789" />
          <button id="fetchListsBtn" class="secondary" style="margin-top:10px;">Buscar listas dessa pasta</button>
          <div id="foldersMsg" class="msg"></div>
          <div id="listsContainer"></div>
          <button id="activateBtn" disabled style="margin-top:10px;">Ativar lista selecionada para este mes</button>
          <div id="activateMsg" class="msg"></div>
        </div>
      </div>

      <div class="card" style="margin-top:18px;">
        <h3>Historico de listas configuradas</h3>
        <table id="historyTable">
          <thead><tr><th>Mes/Ano</th><th>Pasta</th><th>Lista</th><th>Status</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </section>

    <section id="view-integracoes" hidden>
      <header class="top">
        <div><h2>Integracoes</h2><p>Conexoes configuradas. Aberto para novas integracoes no futuro.</p></div>
      </header>
      <div class="integration-grid">
        <div class="integration-card movidesk">
          <div class="head"><div class="icon">&#128218;</div><h4>Movidesk</h4></div>
          <div id="movideskIntegrationBody">Carregando...</div>
        </div>
        <div class="integration-card clickup">
          <div class="head"><div class="icon">&#9989;</div><h4>ClickUp</h4></div>
          <div id="clickupIntegrationBody">Carregando...</div>
        </div>
        <div class="integration-card disabled">+ Nova integracao (em breve)</div>
      </div>
    </section>

    <section id="view-logs" hidden>
      <header class="top">
        <div><h2>Logs</h2><p>Ultimas execucoes da integracao.</p></div>
      </header>
      <div class="card">
        <table id="logsTable">
          <thead><tr><th>Ticket</th><th>Assunto</th><th>Status</th><th>Mensagem</th><th>Quando</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </section>

  </main>
</div>

<script>
const $ = (id) => document.getElementById(id);
let selectedList = null;

async function api(path, opts) {
  const res = await fetch(path, Object.assign({ credentials: "same-origin" }, opts || {}));
  let data = null;
  try { data = await res.json(); } catch (e) {}
  if (!res.ok) {
    const detail = (data && data.detail) ? data.detail : ("Erro " + res.status);
    throw new Error(detail);
  }
  return data;
}

function statusBadge(status) {
  if (status === "CREATED_SUCCESSFULLY") return '<span class="badge ok">criada</span>';
  if (status && status.startsWith("ERROR")) return '<span class="badge warn">' + status + '</span>';
  if (status && status.startsWith("IGNORED")) return '<span class="badge warn">' + status + '</span>';
  return '<span class="badge">' + (status || "-") + '</span>';
}

// ---- Tabs ----
document.querySelectorAll("nav.sidebar button.tab[data-tab]").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("nav.sidebar button.tab[data-tab]").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const tab = btn.dataset.tab;
    ["fluxo", "integracoes", "logs"].forEach(t => {
      document.getElementById("view-" + t).hidden = (t !== tab);
    });
    if (tab === "integracoes") loadIntegrationsStatus();
    if (tab === "logs") loadLogs();
  });
});

// ---- Fluxo: status/labels ----
async function loadFlowStatus() {
  try {
    const status = await api("/admin/integrations/status");
    const m = status.movidesk;
    $("movideskNodeDesc").textContent = m.owner_value
      ? `So cria tarefa quando o responsavel (${m.owner_rule}) e ${m.owner_value}`
      : "Nenhuma regra de responsavel configurada (nao bloqueia).";
    $("movideskCardBody").innerHTML = `
      <div class="kv">Token configurado: <b>${m.configured ? "sim" : "nao"}</b></div>
      <div class="kv">Regra de responsavel: <b>${m.owner_rule}</b></div>
      <div class="kv">Valor: <b>${m.owner_value || "-"}</b></div>
      <div class="kv">Modo: <b>somente leitura</b></div>
    `;

    const c = status.clickup;
    $("clickupNodeDesc").textContent = c.active_list_name
      ? `Cria tarefas em: ${c.active_list_name}`
      : (c.default_list_name ? `Usando lista padrao: ${c.default_list_name}` : "Nenhuma lista ativa configurada ainda.");
    $("clickupIntegrationBody");
  } catch (e) {
    $("movideskNodeDesc").textContent = "Erro ao carregar: " + e.message;
  }
}

async function loadIntegrationsStatus() {
  try {
    const status = await api("/admin/integrations/status");
    const m = status.movidesk;
    $("movideskIntegrationBody").innerHTML = `
      <div class="kv">Status: <b>${m.configured ? "conectado" : "token ausente"}</b></div>
      <div class="kv">Base URL: <b>${m.base_url}</b></div>
      <div class="kv">Regra de responsavel: <b>${m.owner_rule}</b></div>
      <div class="kv">Modo: <b>somente leitura</b></div>
    `;
    const c = status.clickup;
    $("clickupIntegrationBody").innerHTML = `
      <div class="kv">Status: <b>${c.configured ? "conectado" : "token ausente"}</b></div>
      <div class="kv">Base URL: <b>${c.base_url}</b></div>
      <div class="kv">Lista ativa: <b>${c.active_list_name || "-"}</b></div>
      <div class="kv">Lista padrao: <b>${c.default_list_name || "-"}</b></div>
      <div class="kv">Status da task: <b>${c.task_status || "-"}</b></div>
      <div class="kv">Responsavel (assignee): <b>${c.assignee_mode}</b></div>
    `;
  } catch (e) {
    $("movideskIntegrationBody").textContent = "Erro: " + e.message;
  }
}

// ---- Fluxo: pasta/lista ----
async function loadActiveList() {
  try {
    const lists = await api("/admin/clickup-lists");
    renderHistory(lists);
  } catch (e) {}
}

function renderHistory(lists) {
  const tbody = document.querySelector("#historyTable tbody");
  tbody.innerHTML = "";
  for (const l of lists) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${l.month_name}/${l.year}</td><td>${l.clickup_folder_name || l.clickup_folder_id || "-"}</td><td>${l.clickup_list_name}</td><td>${l.active ? '<span class="badge ok">ativa</span>' : ""}</td>`;
    tbody.appendChild(tr);
  }
}

async function loadLogs() {
  const tbody = document.querySelector("#logsTable tbody");
  try {
    const logs = await api("/admin/integration-logs?limit=50");
    tbody.innerHTML = "";
    for (const log of logs) {
      const tr = document.createElement("tr");
      const when = new Date(log.created_at).toLocaleString("pt-BR");
      tr.innerHTML = `<td>${log.ticket_id ?? "-"}</td><td>${log.ticket_subject ?? "-"}</td><td>${statusBadge(log.status)}</td><td>${log.message ?? ""}</td><td>${when}</td>`;
      tbody.appendChild(tr);
    }
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5">Erro ao carregar logs: ${e.message}</td></tr>`;
  }
}

$("fetchListsBtn").addEventListener("click", async () => {
  const folderId = $("folderIdInput").value.trim();
  const msg = $("foldersMsg");
  const container = $("listsContainer");
  selectedList = null;
  $("activateBtn").disabled = true;
  container.innerHTML = "";
  msg.textContent = "";
  msg.className = "msg";
  if (!folderId) { msg.textContent = "Informe o Folder ID."; msg.className = "msg error"; return; }
  try {
    const lists = await api(`/admin/clickup/folders/${encodeURIComponent(folderId)}/lists`);
    if (!lists.length) { msg.textContent = "Nenhuma lista encontrada nessa pasta."; msg.className = "msg error"; return; }
    for (const item of lists) {
      const div = document.createElement("div");
      div.className = "list-option";
      div.textContent = `${item.name} (ID ${item.id})`;
      div.addEventListener("click", () => {
        document.querySelectorAll(".list-option").forEach(el => el.classList.remove("selected"));
        div.classList.add("selected");
        selectedList = { id: item.id, name: item.name, folderId, folderName: null };
        $("activateBtn").disabled = false;
      });
      container.appendChild(div);
    }
  } catch (e) {
    msg.textContent = e.message;
    msg.className = "msg error";
  }
});

$("activateBtn").addEventListener("click", async () => {
  const msg = $("activateMsg");
  if (!selectedList) return;
  try {
    await api("/admin/clickup/folders/setup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        clickup_folder_id: selectedList.folderId,
        clickup_folder_name: selectedList.folderName,
        clickup_list_id: selectedList.id,
        clickup_list_name: selectedList.name,
      }),
    });
    msg.textContent = "Lista ativada com sucesso para o mes atual.";
    msg.className = "msg success";
    await loadActiveList();
    await loadFlowStatus();
  } catch (e) {
    msg.textContent = e.message;
    msg.className = "msg error";
  }
});

$("logoutBtn").addEventListener("click", async () => {
  await api("/admin/logout", { method: "POST" });
  location.reload();
});

$("loginBtn").addEventListener("click", async () => {
  const msg = $("loginMsg");
  msg.textContent = "";
  msg.className = "msg";
  try {
    await api("/admin/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: $("loginUser").value, password: $("loginPass").value }),
    });
    showApp();
  } catch (e) {
    msg.textContent = e.message;
    msg.className = "msg error";
  }
});

function showApp() {
  $("loginScreen").hidden = true;
  $("app").hidden = false;
  loadFlowStatus();
  loadActiveList();
}

(async function init() {
  try {
    await api("/admin/me");
    showApp();
  } catch (e) {
    $("loginScreen").hidden = false;
    $("app").hidden = true;
  }
})();
</script>
</body>
</html>
"""


@router.get("/admin/ui", response_class=HTMLResponse, include_in_schema=False)
def admin_ui() -> HTMLResponse:
    return HTMLResponse(content=_PAGE)
