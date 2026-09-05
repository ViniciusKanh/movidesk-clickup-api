from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["admin-ui"])

_PAGE = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Movidesk to ClickUp - Painel</title>
<style>
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background:#f4f5f7; color:#1f2430; }
  header { background:#1f2430; color:#fff; padding:16px 24px; display:flex; justify-content:space-between; align-items:center; }
  header h1 { font-size:16px; margin:0; font-weight:600; }
  #logoutBtn { background:transparent; border:1px solid #4b5568; color:#fff; padding:6px 12px; border-radius:6px; cursor:pointer; }
  main { max-width:920px; margin:24px auto; padding:0 16px; display:flex; flex-direction:column; gap:20px; }
  .card { background:#fff; border-radius:10px; padding:20px; box-shadow:0 1px 3px rgba(0,0,0,.08); }
  .card h2 { margin-top:0; font-size:15px; }
  label { display:block; font-size:13px; margin:10px 0 4px; color:#4b5568; }
  input[type=text], input[type=password] { width:100%; padding:9px 10px; border:1px solid #d7dbe3; border-radius:6px; font-size:14px; }
  button { background:#3454d1; color:#fff; border:none; padding:9px 16px; border-radius:6px; font-size:14px; cursor:pointer; margin-top:12px; }
  button.secondary { background:#eef0f4; color:#1f2430; }
  button:disabled { opacity:.5; cursor:not-allowed; }
  .list-option { display:flex; align-items:center; gap:8px; padding:8px 10px; border:1px solid #e2e5ec; border-radius:6px; margin-top:6px; cursor:pointer; }
  .list-option.selected { border-color:#3454d1; background:#eef1fd; }
  table { width:100%; border-collapse:collapse; font-size:13px; margin-top:8px; }
  th, td { text-align:left; padding:6px 8px; border-bottom:1px solid #eef0f4; }
  .badge { padding:2px 8px; border-radius:999px; font-size:11px; font-weight:600; }
  .badge.ok { background:#e3f6e8; color:#1a7f3c; }
  .badge.warn { background:#fdf1de; color:#9a6a10; }
  .badge.err { background:#fde3e3; color:#a12626; }
  .msg { font-size:13px; margin-top:10px; }
  .msg.error { color:#c0392b; }
  .msg.success { color:#1a7f3c; }
  #loginScreen { max-width:360px; margin:80px auto; }
  [hidden] { display:none !important; }
  small.hint { display:block; color:#7a8296; margin-top:4px; }
</style>
</head>
<body>

<div id="loginScreen" class="card">
  <h2>Entrar no painel</h2>
  <label>Usuario</label>
  <input id="loginUser" type="text" autocomplete="username" />
  <label>Senha</label>
  <input id="loginPass" type="password" autocomplete="current-password" />
  <button id="loginBtn">Entrar</button>
  <div id="loginMsg" class="msg"></div>
</div>

<div id="app" hidden>
  <header>
    <h1>Movidesk &rarr; ClickUp</h1>
    <button id="logoutBtn">Sair</button>
  </header>
  <main>

    <div class="card">
      <h2>Lista ativa do ClickUp</h2>
      <div id="activeListInfo">Carregando...</div>
    </div>

    <div class="card">
      <h2>Configurar pasta/lista do mes</h2>
      <label>Folder ID do ClickUp</label>
      <input id="folderIdInput" type="text" placeholder="Ex: 90123456789" />
      <button id="fetchListsBtn" class="secondary">Buscar listas dessa pasta</button>
      <div id="foldersMsg" class="msg"></div>
      <div id="listsContainer"></div>
      <button id="activateBtn" disabled>Ativar lista selecionada para este mes</button>
      <div id="activateMsg" class="msg"></div>
      <small class="hint">Repita este passo todo mes: cole o Folder ID da pasta atual e escolha a lista correta.</small>
    </div>

    <div class="card">
      <h2>Historico de listas configuradas</h2>
      <table id="historyTable">
        <thead><tr><th>Mes/Ano</th><th>Pasta</th><th>Lista</th><th>Status</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>

    <div class="card">
      <h2>Logs de integracao (mais recentes)</h2>
      <table id="logsTable">
        <thead><tr><th>Ticket</th><th>Assunto</th><th>Status</th><th>Mensagem</th><th>Quando</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>

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
  if (status && status.startsWith("ERROR")) return '<span class="badge err">' + status + '</span>';
  if (status && status.startsWith("IGNORED")) return '<span class="badge warn">' + status + '</span>';
  return '<span class="badge">' + (status || "-") + '</span>';
}

async function loadActiveList() {
  const el = $("activeListInfo");
  try {
    const lists = await api("/admin/clickup-lists");
    const active = lists.find(l => l.active);
    if (!active) {
      el.textContent = "Nenhuma lista ativa configurada ainda.";
    } else {
      el.innerHTML = `<strong>${active.month_name}/${active.year}</strong> &rarr; lista <strong>${active.clickup_list_name}</strong> (ID ${active.clickup_list_id})`
        + (active.clickup_folder_name ? ` &mdash; pasta ${active.clickup_folder_name}` : "");
    }
    renderHistory(lists);
  } catch (e) {
    el.textContent = "Erro ao carregar: " + e.message;
  }
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
  loadActiveList();
  loadLogs();
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
