from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["admin-ui"])

_PAGE = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>ViniciusFlow</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
<style>
  :root {
    color-scheme: dark;
    --bg: #14151a;
    --surface: #1b1d24;
    --surface-2: #22242c;
    --border: #2b2e37;
    --border-soft: #22242c;
    --text: #eceef2;
    --text-dim: #888ca0;
    --text-faint: #5c5f6e;
    --violet: #9b8afb;
    --violet-dim: rgba(155,138,251,.13);
    --teal: #29d3b0;
    --teal-dim: rgba(41,211,176,.13);
    --amber: #f5a623;
    --amber-dim: rgba(245,166,35,.13);
    --coral: #ff6b5d;
    --coral-dim: rgba(255,107,93,.13);
    --radius: 10px;
    --sans: "Space Grotesk", system-ui, -apple-system, sans-serif;
    --mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
  }
  * { box-sizing: border-box; }
  body { margin:0; font-family: var(--sans); background: var(--bg); color: var(--text); }
  [hidden] { display:none !important; }
  ::selection { background: var(--violet-dim); color: var(--text); }
  :focus-visible { outline: 2px solid var(--violet); outline-offset: 2px; }

  label { display:block; font-size:12.5px; margin:14px 0 6px; color: var(--text-dim); }
  input[type=text], input[type=password] {
    width:100%; padding:11px 12px; border:1px solid var(--border); border-radius:8px;
    font-size:14px; background: var(--bg); color: var(--text); font-family: var(--sans);
  }
  input::placeholder { color: var(--text-faint); }
  input[type=text]:focus, input[type=password]:focus { border-color: var(--violet); }
  select {
    width:100%; padding:10px 12px; border:1px solid var(--border); border-radius:8px;
    font-size:13.5px; background: var(--bg); color: var(--text); font-family: var(--sans);
  }
  select:disabled { opacity:.5; cursor:not-allowed; }
  select:focus { border-color: var(--violet); }
  a { color: var(--teal); }

  button { font-family: var(--sans); border:none; border-radius:8px; font-size:14px; cursor:pointer; font-weight:600; }
  button.primary { background: var(--violet); color:#100e1c; padding:11px 18px; }
  button.primary:hover { filter:brightness(1.08); }
  button.secondary { background: var(--surface-2); color: var(--text); border:1px solid var(--border); padding:9px 14px; }
  button.secondary:hover { border-color: var(--teal); }
  button.ghost { background:transparent; color: var(--text-dim); border:1px solid var(--border); padding:9px 14px; }
  button.ghost:hover { color: var(--text); border-color: var(--text-dim); }
  button.tiny { padding:6px 11px; font-size:12px; }
  button:disabled { opacity:.4; cursor:not-allowed; }

  .msg { font-size:13px; margin-top:10px; font-family: var(--mono); }
  .msg.error { color: var(--coral); }
  .msg.success { color: var(--teal); }
  .hint-block { font-size:11.5px; color: var(--text-faint); line-height:1.5; margin-top:8px; }

  svg.icon { width:18px; height:18px; stroke:currentColor; fill:none; stroke-width:1.6; stroke-linecap:round; stroke-linejoin:round; flex-shrink:0; }

  /* ---- Marca ---- */
  .mark { width:30px; height:30px; border-radius:8px; background: var(--surface-2); border:1px solid var(--border);
    display:flex; align-items:center; justify-content:center; flex-shrink:0; }
  .mark svg { width:16px; height:16px; }
  .mark .dot-a { fill: var(--violet); }
  .mark .dot-b { fill: var(--teal); }
  .mark .wire { stroke: var(--text-faint); stroke-width:1.4; }

  /* ================= Login (layout partido) ================= */
  #loginScreen { min-height:100vh; display:flex; }
  .login-rail {
    flex:0 0 38%; max-width:420px; background: var(--surface);
    border-right:1px solid var(--border); padding:48px 40px; display:flex; flex-direction:column;
  }
  .login-rail .brand-row { display:flex; align-items:center; gap:10px; font-weight:600; font-size:16px; }
  .login-rail .rail-spacer { flex:1; min-height:40px; }
  .login-schema { display:flex; align-items:center; gap:0; margin:8px 0 18px; }
  .login-schema .node-chip {
    display:flex; align-items:center; gap:8px; padding:9px 12px; border:1px solid var(--border);
    border-radius:8px; background: var(--bg); font-family: var(--mono); font-size:12px;
  }
  .login-schema .node-chip .swatch { width:8px; height:8px; border-radius:50%; }
  .login-schema .node-chip.src .swatch { background: var(--violet); }
  .login-schema .node-chip.dst .swatch { background: var(--teal); }
  .login-schema .wire { flex:1; height:1px; background: var(--border); min-width:22px; position:relative; }
  .login-rail .rail-caption { font-family: var(--mono); font-size:12px; color: var(--text-dim); line-height:1.7; }
  .login-rail .rail-caption .line { display:block; }
  .login-rail .rail-caption .ok { color: var(--teal); }
  .login-rail .rail-caption .lock { color: var(--violet); }
  .login-rail .rail-foot { font-size:11.5px; color: var(--text-faint); margin-top:auto; padding-top:24px; }

  .login-main { flex:1; display:flex; align-items:center; justify-content:center; padding:24px; }
  .login-form { width:100%; max-width:320px; }
  .login-form h1 { font-size:22px; margin:0 0 6px; font-weight:600; }
  .login-form p.sub { color: var(--text-dim); font-size:13.5px; margin:0 0 8px; }
  .login-form button.primary { width:100%; margin-top:20px; padding:12px; font-size:14.5px; }

  /* ================= App shell ================= */
  #app { display:flex; min-height:100vh; }
  nav.sidebar {
    width:216px; flex-shrink:0; background: var(--surface); border-right:1px solid var(--border);
    padding:20px 12px; display:flex; flex-direction:column;
  }
  nav.sidebar .brand { font-weight:600; font-size:14.5px; padding:2px 8px 20px; display:flex; align-items:center; gap:9px; }
  nav.sidebar button.tab {
    display:flex; align-items:center; gap:11px; width:100%; text-align:left; background:transparent;
    color: var(--text-dim); border:none; padding:9px 10px; border-radius:8px; font-size:13.5px;
    font-weight:500; margin-bottom:2px; cursor:pointer; font-family: var(--sans);
  }
  nav.sidebar button.tab:hover { background: var(--surface-2); color: var(--text); }
  nav.sidebar button.tab.active { background: var(--violet-dim); color: var(--violet); }
  nav.sidebar .spacer { flex:1; }

  main.content { flex:1; overflow:auto; padding:32px 40px; max-width:1180px; }
  header.top { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:22px; }
  header.top h2 { margin:0; font-size:20px; font-weight:600; }
  header.top p { margin:3px 0 0; color: var(--text-dim); font-size:13.5px; }

  /* ---- Fluxo: canvas estilo n8n (nos arrastaveis) ---- */
  .canvas {
    position:relative; background-image: radial-gradient(circle, var(--border-soft) 1px, transparent 1px);
    background-size:20px 20px; background-color: var(--surface); border:1px solid var(--border);
    border-radius:var(--radius); height:280px; overflow:hidden;
  }
  .wire-svg { position:absolute; inset:0; width:100%; height:100%; pointer-events:none; }
  .wire-svg .pulse-dot { fill: var(--teal); filter:drop-shadow(0 0 4px var(--teal)); }
  @media (prefers-reduced-motion: reduce) { .wire-svg .pulse-dot { display:none; } }

  .node {
    position:absolute; z-index:1; width:250px; background: var(--bg); border:1px solid var(--border);
    border-left:3px solid var(--border); border-radius:8px; padding:14px 16px; user-select:none;
  }
  .node.dragging { border-color: var(--violet); box-shadow:0 8px 24px rgba(0,0,0,.35); z-index:2; }
  .node.movidesk { border-left-color: var(--violet); }
  .node.clickup { border-left-color: var(--teal); }
  .node .node-head { display:flex; align-items:center; gap:10px; margin-bottom:8px; cursor:grab; }
  .node .node-head:active { cursor:grabbing; }
  .node .node-head svg.icon { width:16px; height:16px; }
  .node.movidesk .node-head svg.icon { color: var(--violet); }
  .node.clickup .node-head svg.icon { color: var(--teal); }
  .node .title { font-weight:600; font-size:13.5px; }
  .node .kind { font-family: var(--mono); font-size:10px; color: var(--text-faint); }
  .node .desc { font-size:12px; color: var(--text-dim); line-height:1.5; }
  .node .badge-row { margin-top:8px; }
  .canvas-hint {
    position:absolute; left:16px; bottom:12px; font-family: var(--mono); font-size:10.5px;
    color: var(--text-faint); pointer-events:none;
  }

  .safety-banner {
    margin-top:16px; background: var(--teal-dim); border:1px solid rgba(41,211,176,.28); color: var(--text);
    border-radius:8px; padding:13px 16px; font-size:12.5px; line-height:1.65;
  }
  .safety-banner strong { color: var(--teal); font-family: var(--mono); font-weight:600; }

  /* ---- Paineis abaixo do canvas ---- */
  .grid2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:20px; }
  .card { background: var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:20px; }
  .card h3 { margin:0 0 4px; font-size:14px; font-weight:600; }
  .card p.hint { color: var(--text-faint); font-size:12px; margin:2px 0 14px; }
  .kv { font-size:13px; color: var(--text-dim); margin:5px 0; display:flex; justify-content:space-between; gap:10px; }
  .kv b { color: var(--text); font-family: var(--mono); font-weight:500; }
  .list-option {
    display:flex; align-items:center; gap:8px; padding:10px 11px; border:1px solid var(--border);
    border-radius:8px; margin-top:6px; cursor:pointer; font-size:13px; font-family: var(--mono);
  }
  .list-option:hover { border-color: var(--text-dim); }
  .list-option.selected { border-color: var(--teal); background: var(--teal-dim); color: var(--teal); }

  /* ---- Badges (codificam status, nao decoram) ---- */
  .badge { font-size:10.5px; padding:3px 8px; border-radius:5px; font-weight:600; font-family: var(--mono); }
  .badge.readonly { background: var(--violet-dim); color: var(--violet); }
  .badge.createonly { background: var(--teal-dim); color: var(--teal); }
  .badge.ok { background: var(--teal-dim); color: var(--teal); }
  .badge.warn { background: var(--amber-dim); color: var(--amber); }
  .badge.down { background: var(--coral-dim); color: var(--coral); }

  /* ---- Integracoes ---- */
  .integration-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(280px,1fr)); gap:16px; }
  .integration-card { background: var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:18px; }
  .integration-card.disabled {
    opacity:.55; border-style:dashed; display:flex; align-items:center; justify-content:center;
    min-height:170px; font-size:13px; color: var(--text-faint); font-family: var(--mono);
  }
  .integration-card .head { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
  .integration-card .head .head-left { display:flex; align-items:center; gap:10px; }
  .integration-card .head svg.icon { width:18px; height:18px; }
  .integration-card.movidesk .head svg.icon { color: var(--violet); }
  .integration-card.clickup .head svg.icon { color: var(--teal); }
  .integration-card h4 { margin:0; font-size:14.5px; font-weight:600; }
  .integration-card .kv { font-size:12.5px; }
  .integration-card .test-row { margin-top:14px; padding-top:14px; border-top:1px dashed var(--border); display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
  .status-pill { font-family: var(--mono); font-size:11.5px; padding:4px 10px; border-radius:999px; background: var(--surface-2); color: var(--text-faint); }
  .status-pill.ok { background: var(--teal-dim); color: var(--teal); }
  .status-pill.down { background: var(--coral-dim); color: var(--coral); }
  .status-pill.checking { background: var(--amber-dim); color: var(--amber); }

  /* ---- Tabelas ---- */
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th, td { text-align:left; padding:9px 10px; border-bottom:1px solid var(--border-soft); }
  td { font-family: var(--mono); font-size:12.5px; color: var(--text-dim); }
  th { color: var(--text-faint); font-weight:600; font-size:11px; letter-spacing:.02em; font-family: var(--sans); }

  @media (max-width: 860px) {
    #loginScreen { flex-direction:column; }
    .login-rail { flex:none; max-width:none; padding:28px 24px; }
    .login-rail .rail-spacer { min-height:16px; }
    .login-main { padding:32px 24px; }
    #app { flex-direction:column; }
    nav.sidebar { width:auto; flex-direction:row; align-items:center; padding:12px 14px; overflow-x:auto; }
    nav.sidebar .brand { padding:0 12px 0 0; }
    nav.sidebar .spacer { display:none; }
    main.content { padding:22px 18px; }
    .grid2 { grid-template-columns:1fr; }
    .canvas { height:auto; padding:16px; }
    .wire-svg { display:none; }
    .canvas-hint { display:none; }
    .node { position:static !important; width:100%; margin-bottom:12px; }
    .node .node-head { cursor:default; }
  }
</style>
</head>
<body>

<div id="loginScreen">
  <div class="login-rail">
    <div class="brand-row">
      <span class="mark"><svg viewBox="0 0 24 24"><circle class="dot-a" cx="6" cy="12" r="2.6"/><line class="wire" x1="8.6" y1="12" x2="15.4" y2="12"/><circle class="dot-b" cx="18" cy="12" r="2.6"/></svg></span>
      ViniciusFlow
    </div>
    <div class="rail-spacer"></div>
    <div class="login-schema">
      <div class="node-chip src"><span class="swatch"></span>movidesk</div>
      <div class="wire"></div>
      <div class="node-chip dst"><span class="swatch"></span>clickup</div>
    </div>
    <div class="rail-caption">
      <span class="line"><span class="lock">&#9679;</span> Movidesk: acesso somente leitura</span>
      <span class="line"><span class="ok">&#9679;</span> ClickUp: cria tarefas, nunca edita</span>
    </div>
    <div class="rail-foot">Penso Tecnologia &middot; integracao interna</div>
  </div>
  <div class="login-main">
    <div class="login-form">
      <h1>Entrar</h1>
      <p class="sub">Acesso ao painel da integracao.</p>
      <label>Usuario</label>
      <input id="loginUser" type="text" autocomplete="username" placeholder="seu.usuario@penso.com.br" />
      <label>Senha</label>
      <input id="loginPass" type="password" autocomplete="current-password" placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;" />
      <button id="loginBtn" class="primary">Entrar</button>
      <div id="loginMsg" class="msg"></div>
    </div>
  </div>
</div>

<div id="app" hidden>
  <nav class="sidebar">
    <div class="brand">
      <span class="mark"><svg viewBox="0 0 24 24"><circle class="dot-a" cx="6" cy="12" r="2.6"/><line class="wire" x1="8.6" y1="12" x2="15.4" y2="12"/><circle class="dot-b" cx="18" cy="12" r="2.6"/></svg></span>
      ViniciusFlow
    </div>
    <button class="tab active" data-tab="fluxo">
      <svg class="icon" viewBox="0 0 24 24"><circle cx="5" cy="12" r="2"/><circle cx="19" cy="6" r="2"/><circle cx="19" cy="18" r="2"/><path d="M7 12h4M11 12l6-5M11 12l6 5"/></svg>
      Fluxo
    </button>
    <button class="tab" data-tab="integracoes">
      <svg class="icon" viewBox="0 0 24 24"><path d="M9 2v4M15 2v4M6 8h12l-1 5a5 5 0 0 1-10 0L6 8Z"/><path d="M12 17v5"/></svg>
      Integracoes
    </button>
    <button class="tab" data-tab="logs">
      <svg class="icon" viewBox="0 0 24 24"><path d="M6 4h12v16l-3-2-3 2-3-2-3 2V4Z"/><path d="M9 9h6M9 13h6"/></svg>
      Logs
    </button>
    <div class="spacer"></div>
    <button class="tab ghost" id="logoutBtn">
      <svg class="icon" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/></svg>
      Sair
    </button>
  </nav>

  <main class="content">

    <section id="view-fluxo">
      <header class="top">
        <div><h2>Fluxo</h2><p>Movidesk (leitura) &rarr; ClickUp (criacao de tarefa) &mdash; arraste os nos para reorganizar</p></div>
      </header>

      <div class="canvas" id="flowCanvas">
        <svg class="wire-svg" id="wireSvg"><path id="wirePath" fill="none" stroke="#29d3b0" stroke-width="1.4"/><circle class="pulse-dot" r="3.4"><animateMotion id="wireMotion" dur="3s" repeatCount="indefinite" path="M0,0" /></circle></svg>

        <div class="node movidesk" id="nodeMovidesk">
          <div class="node-head" data-drag-handle>
            <svg class="icon" viewBox="0 0 24 24"><path d="M4 5h16v11H8l-4 4V5Z"/><path d="M8 9h8M8 12h5"/></svg>
            <div><div class="title">Movidesk</div><div class="kind">gatilho / origem</div></div>
          </div>
          <div class="desc" id="movideskNodeDesc">Carregando regra de responsavel...</div>
          <div class="badge-row"><span class="badge readonly">somente leitura</span></div>
        </div>

        <div class="node clickup" id="nodeClickup">
          <div class="node-head" data-drag-handle>
            <svg class="icon" viewBox="0 0 24 24"><path d="M20 7 10 18l-6-6"/></svg>
            <div><div class="title">ClickUp</div><div class="kind">acao / destino</div></div>
          </div>
          <div class="desc" id="clickupNodeDesc">Carregando lista ativa...</div>
          <div class="badge-row"><span class="badge createonly">so cria tarefas</span></div>
        </div>

        <div class="canvas-hint">arraste pelos titulos dos cards para reposicionar</div>
      </div>

      <div class="safety-banner">
        <strong>modo seguro</strong> &mdash; o Movidesk e usado 100% para leitura (nunca exclui ou altera tickets).
        No ClickUp, a integracao apenas cria tarefas novas na lista escolhida &mdash; nunca edita ou apaga
        tarefas existentes de outras pessoas na pasta.
      </div>

      <div class="grid2">
        <div class="card">
          <h3>No: Movidesk</h3>
          <p class="hint">Regra que decide quando um ticket vira tarefa.</p>
          <div id="movideskCardBody">Carregando...</div>
        </div>
        <div class="card">
          <h3>No: ClickUp &mdash; pasta/lista do mes</h3>
          <p class="hint">Navegue Workspace &rarr; Space &rarr; Pasta (sem precisar copiar nenhum ID a mao).</p>

          <label>Workspace</label>
          <select id="teamSelect"><option value="">Carregando...</option></select>
          <label>Space</label>
          <select id="spaceSelect" disabled><option value="">Escolha o workspace primeiro</option></select>
          <label>Pasta (Folder)</label>
          <select id="folderSelect" disabled><option value="">Escolha o space primeiro</option></select>
          <div id="browseMsg" class="msg"></div>

          <div class="hint-block">
            Prefere colar o ID manualmente? <a href="#" id="toggleManualFolder" style="color:var(--teal);">Usar campo manual</a>.
          </div>
          <div id="manualFolderBlock" hidden style="margin-top:10px;">
            <label>Folder ID do ClickUp</label>
            <input id="folderIdInput" type="text" placeholder="Ex: 90123456789" />
            <div class="hint-block">
              No ClickUp: abra a PASTA (nao a lista) &rarr; "..." &rarr; Copiar link. O numero no
              final do link costuma ser o mesmo ID da lista dentro dela, nao o da pasta &mdash; por
              isso o navegador acima e mais confiavel. Colar aqui o ID de uma lista (o mesmo numero
              que aparece em "lista padrao" abaixo) sempre resulta em erro 404.
            </div>
          </div>

          <button id="fetchListsBtn" class="secondary" style="margin-top:10px;">Buscar listas dessa pasta</button>
          <div id="foldersMsg" class="msg"></div>
          <div id="listsContainer"></div>
          <button id="activateBtn" class="primary" disabled style="margin-top:12px; width:100%;">Ativar lista selecionada para este mes</button>
          <div id="activateMsg" class="msg"></div>
        </div>
      </div>

      <div class="card" style="margin-top:16px;">
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
          <div class="head">
            <div class="head-left">
              <svg class="icon" viewBox="0 0 24 24"><path d="M4 5h16v11H8l-4 4V5Z"/><path d="M8 9h8M8 12h5"/></svg>
              <h4>Movidesk</h4>
            </div>
          </div>
          <div id="movideskIntegrationBody">Carregando...</div>
          <div class="test-row">
            <button class="secondary tiny" id="testMovideskBtn">Testar conexao</button>
            <span class="status-pill" id="movideskStatusPill">nao testado</span>
          </div>
        </div>
        <div class="integration-card clickup">
          <div class="head">
            <div class="head-left">
              <svg class="icon" viewBox="0 0 24 24"><path d="M20 7 10 18l-6-6"/></svg>
              <h4>ClickUp</h4>
            </div>
          </div>
          <div id="clickupIntegrationBody">Carregando...</div>
          <div class="test-row">
            <button class="secondary tiny" id="testClickupBtn">Testar conexao</button>
            <span class="status-pill" id="clickupStatusPill">nao testado</span>
          </div>
        </div>
        <div class="integration-card disabled">+ nova integracao (em breve)</div>
      </div>
    </section>

    <section id="view-logs" hidden>
      <header class="top">
        <div><h2>Logs</h2><p>Ultimas execucoes da integracao.</p></div>
      </header>
      <div class="card">
        <h3>Diagnostico de ticket</h3>
        <p class="hint">Informe o numero de um ticket do Movidesk para ver, agora, por que a integracao criaria ou nao criaria uma tarefa (somente leitura, nao cria nada).</p>
        <label>Numero do ticket</label>
        <input id="diagTicketInput" type="text" placeholder="Ex: 123456" />
        <button id="diagTicketBtn" class="secondary" style="margin-top:10px;">Verificar</button>
        <div id="diagMsg" class="msg"></div>
        <div id="diagResult" style="margin-top:12px;"></div>
      </div>
      <div class="card" style="margin-top:16px;">
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
    if (tab === "fluxo") setTimeout(updateWire, 0);
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
      <div class="kv"><span>Token configurado</span><b>${m.configured ? "sim" : "nao"}</b></div>
      <div class="kv"><span>Regra de responsavel</span><b>${m.owner_rule}</b></div>
      <div class="kv"><span>Valor</span><b>${m.owner_value || "-"}</b></div>
      <div class="kv"><span>Modo</span><b>somente leitura</b></div>
    `;

    const c = status.clickup;
    $("clickupNodeDesc").textContent = c.active_list_name
      ? `Cria tarefas em: ${c.active_list_name}`
      : (c.default_list_name ? `Usando lista padrao: ${c.default_list_name}` : "Nenhuma lista ativa configurada ainda.");
  } catch (e) {
    $("movideskNodeDesc").textContent = "Erro ao carregar: " + e.message;
  }
}

function setStatusPill(el, state, text) {
  el.className = "status-pill" + (state ? " " + state : "");
  el.textContent = text;
}

async function loadIntegrationsStatus() {
  try {
    const status = await api("/admin/integrations/status");
    const m = status.movidesk;
    $("movideskIntegrationBody").innerHTML = `
      <div class="kv"><span>Status</span><b>${m.configured ? "conectado" : "token ausente"}</b></div>
      <div class="kv"><span>Base URL</span><b>${m.base_url}</b></div>
      <div class="kv"><span>Regra de responsavel</span><b>${m.owner_rule}</b></div>
      <div class="kv"><span>Modo</span><b>somente leitura</b></div>
    `;
    const c = status.clickup;
    $("clickupIntegrationBody").innerHTML = `
      <div class="kv"><span>Status</span><b>${c.configured ? "conectado" : "token ausente"}</b></div>
      <div class="kv"><span>Base URL</span><b>${c.base_url}</b></div>
      <div class="kv"><span>Lista ativa</span><b>${c.active_list_name || "-"}</b></div>
      <div class="kv"><span>Lista padrao</span><b>${c.default_list_name || "-"}</b></div>
      <div class="kv"><span>Status da task</span><b>${c.task_status || "-"}</b></div>
      <div class="kv"><span>Responsavel (assignee)</span><b>${c.assignee_mode}</b></div>
    `;
  } catch (e) {
    $("movideskIntegrationBody").textContent = "Erro: " + e.message;
  }
}

async function testConnection(path, pillEl) {
  setStatusPill(pillEl, "checking", "verificando...");
  try {
    const result = await api(path);
    setStatusPill(pillEl, result.ok ? "ok" : "down", result.message);
  } catch (e) {
    setStatusPill(pillEl, "down", e.message);
  }
}

$("testMovideskBtn").addEventListener("click", () => testConnection("/admin/movidesk/test-connection", $("movideskStatusPill")));
$("testClickupBtn").addEventListener("click", () => testConnection("/admin/clickup/test-connection", $("clickupStatusPill")));

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

// ---- Diagnostico de ticket (somente leitura) ----
function diagRow(label, value) {
  return `<div class="kv"><span>${label}</span><b>${value === null || value === undefined || value === "" ? "-" : value}</b></div>`;
}

function diagBool(value) {
  if (value === true) return '<span class="badge ok">sim</span>';
  if (value === false) return '<span class="badge warn">nao</span>';
  return "-";
}

async function runTicketDiagnostic() {
  const ticketId = ($("diagTicketInput").value || "").trim();
  const resultEl = $("diagResult");
  const msgEl = $("diagMsg");
  resultEl.innerHTML = "";
  msgEl.textContent = "";

  if (!ticketId) {
    msgEl.textContent = "Informe o numero do ticket.";
    return;
  }

  msgEl.textContent = "Consultando ticket no Movidesk...";
  try {
    const d = await api(`/admin/diagnostics/ticket/${encodeURIComponent(ticketId)}`);
    msgEl.textContent = "";

    if (!d.found) {
      resultEl.innerHTML = `<div class="kv"><span>Resultado</span><b>${d.error || "Ticket nao encontrado."}</b></div>`;
      return;
    }

    const verdictClass = d.would_create_task ? "ok" : (d.already_integrated ? "" : "warn");
    resultEl.innerHTML = `
      <div class="kv"><span>Veredito</span><b><span class="badge ${verdictClass}">${d.verdict}</span></b></div>
      ${diagRow("Assunto", d.subject)}
      ${diagRow("Status", d.status)}
      ${diagRow("Ja integrado?", diagBool(d.already_integrated))}
      ${d.existing_clickup_task_url ? diagRow("Tarefa existente", `<a href="${d.existing_clickup_task_url}" target="_blank" style="color:var(--teal);">abrir no ClickUp</a>`) : ""}
      ${diagRow("Regra de responsavel", d.owner_rule)}
      ${diagRow("Valor exigido", d.owner_required_value)}
      ${diagRow("Responsavel no ticket (ID)", d.owner_id)}
      ${diagRow("Responsavel no ticket (email)", d.owner_email)}
      ${diagRow("Responsavel no ticket (nome)", d.owner_name)}
      ${diagRow("Responsavel confere?", diagBool(d.owner_matches))}
      ${diagRow("Servico", [d.service_first_level, d.service_second_level, d.service_third_level].filter(Boolean).join(" > "))}
      ${diagRow("[BI] Criar tarefa no ClickUp?", d.custom_field_criar_tarefa)}
      ${diagRow("[BI] Link ClickUp", d.custom_field_link_clickup)}
      ${diagRow("Lista ativa do ClickUp", d.active_clickup_list_name || d.active_clickup_list_id)}
      ${d.validation_error ? diagRow("Motivo do bloqueio", d.validation_error) : ""}
    `;
  } catch (e) {
    msgEl.textContent = "Erro: " + e.message;
  }
}

$("diagTicketBtn").addEventListener("click", runTicketDiagnostic);
$("diagTicketInput").addEventListener("keydown", (ev) => { if (ev.key === "Enter") runTicketDiagnostic(); });

// ---- Navegador ClickUp: Workspace -> Space -> Folder (evita colar ID errado) ----
function currentFolderSelection() {
  const manualVisible = !$("manualFolderBlock").hidden;
  if (manualVisible) {
    const id = $("folderIdInput").value.trim();
    return id ? { id, name: null } : null;
  }
  const sel = $("folderSelect");
  if (!sel.value) return null;
  return { id: sel.value, name: sel.selectedOptions[0]?.textContent || null };
}

function fillSelect(sel, items, placeholder) {
  sel.innerHTML = "";
  const opt0 = document.createElement("option");
  opt0.value = "";
  opt0.textContent = placeholder;
  sel.appendChild(opt0);
  for (const item of items) {
    const opt = document.createElement("option");
    opt.value = item.id;
    opt.textContent = item.name || item.id;
    sel.appendChild(opt);
  }
}

async function loadTeams() {
  const browseMsg = $("browseMsg");
  try {
    const teams = await api("/admin/clickup/teams");
    fillSelect($("teamSelect"), teams, teams.length ? "Selecione..." : "Nenhum workspace encontrado");
    $("spaceSelect").disabled = true;
    $("folderSelect").disabled = true;
  } catch (e) {
    browseMsg.textContent = "Erro ao listar workspaces: " + e.message;
    browseMsg.className = "msg error";
  }
}

$("teamSelect").addEventListener("change", async () => {
  const teamId = $("teamSelect").value;
  const spaceSel = $("spaceSelect");
  const folderSel = $("folderSelect");
  fillSelect(folderSel, [], "Escolha o space primeiro");
  folderSel.disabled = true;
  if (!teamId) { fillSelect(spaceSel, [], "Escolha o workspace primeiro"); spaceSel.disabled = true; return; }
  spaceSel.disabled = true;
  fillSelect(spaceSel, [], "Carregando...");
  try {
    const spaces = await api(`/admin/clickup/teams/${encodeURIComponent(teamId)}/spaces`);
    fillSelect(spaceSel, spaces, spaces.length ? "Selecione..." : "Nenhum space encontrado");
    spaceSel.disabled = false;
  } catch (e) {
    $("browseMsg").textContent = "Erro ao listar spaces: " + e.message;
    $("browseMsg").className = "msg error";
  }
});

$("spaceSelect").addEventListener("change", async () => {
  const spaceId = $("spaceSelect").value;
  const folderSel = $("folderSelect");
  if (!spaceId) { fillSelect(folderSel, [], "Escolha o space primeiro"); folderSel.disabled = true; return; }
  folderSel.disabled = true;
  fillSelect(folderSel, [], "Carregando...");
  try {
    const folders = await api(`/admin/clickup/spaces/${encodeURIComponent(spaceId)}/folders`);
    fillSelect(folderSel, folders, folders.length ? "Selecione..." : "Nenhuma pasta encontrada");
    folderSel.disabled = false;
  } catch (e) {
    $("browseMsg").textContent = "Erro ao listar pastas: " + e.message;
    $("browseMsg").className = "msg error";
  }
});

$("toggleManualFolder").addEventListener("click", (ev) => {
  ev.preventDefault();
  const block = $("manualFolderBlock");
  block.hidden = !block.hidden;
  ev.target.textContent = block.hidden ? "Usar campo manual" : "Usar o navegador acima";
});

$("fetchListsBtn").addEventListener("click", async () => {
  const selection = currentFolderSelection();
  const msg = $("foldersMsg");
  const container = $("listsContainer");
  selectedList = null;
  $("activateBtn").disabled = true;
  container.innerHTML = "";
  msg.textContent = "";
  msg.className = "msg";
  if (!selection) { msg.textContent = "Escolha uma pasta (ou informe o Folder ID manualmente)."; msg.className = "msg error"; return; }
  const { id: folderId, name: folderName } = selection;
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
        selectedList = { id: item.id, name: item.name, folderId, folderName };
        $("activateBtn").disabled = false;
      });
      container.appendChild(div);
    }
  } catch (e) {
    msg.textContent = e.message + " (confira se a pasta escolhida realmente tem listas, e nao colou um List ID no campo manual)";
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
  loadTeams();
  setTimeout(layoutNodes, 0);
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

// ---- Canvas: nos arrastaveis estilo n8n (template Movidesk -> ClickUp ja pre-ligado) ----
const canvas = $("flowCanvas");
const nodeMovidesk = $("nodeMovidesk");
const nodeClickup = $("nodeClickup");
let userMovedNodes = false;

function layoutNodes() {
  if (userMovedNodes || !canvas.clientWidth) return;
  const w = canvas.clientWidth;
  const nodeW = nodeMovidesk.offsetWidth || 250;
  nodeMovidesk.style.left = "36px";
  nodeMovidesk.style.top = "70px";
  nodeClickup.style.left = Math.max(36, w - nodeW - 36) + "px";
  nodeClickup.style.top = "70px";
  updateWire();
}

function anchorPoint(node, side) {
  const rect = node.getBoundingClientRect();
  const canvasRect = canvas.getBoundingClientRect();
  const y = rect.top - canvasRect.top + rect.height / 2;
  const x = side === "right" ? (rect.right - canvasRect.left) : (rect.left - canvasRect.left);
  return { x, y };
}

function updateWire() {
  if (window.innerWidth <= 860) return;
  const a = anchorPoint(nodeMovidesk, "right");
  const b = anchorPoint(nodeClickup, "left");
  const midX = (a.x + b.x) / 2;
  const d = `M ${a.x} ${a.y} C ${midX} ${a.y}, ${midX} ${b.y}, ${b.x} ${b.y}`;
  $("wirePath").setAttribute("d", d);
  $("wireMotion").setAttribute("path", d);
}

function makeDraggable(node) {
  const handle = node.querySelector("[data-drag-handle]");
  let dragging = false;
  let offsetX = 0, offsetY = 0;

  handle.addEventListener("pointerdown", (ev) => {
    dragging = true;
    userMovedNodes = true;
    node.classList.add("dragging");
    const rect = node.getBoundingClientRect();
    offsetX = ev.clientX - rect.left;
    offsetY = ev.clientY - rect.top;
    handle.setPointerCapture(ev.pointerId);
  });
  handle.addEventListener("pointermove", (ev) => {
    if (!dragging) return;
    const canvasRect = canvas.getBoundingClientRect();
    let x = ev.clientX - canvasRect.left - offsetX;
    let y = ev.clientY - canvasRect.top - offsetY;
    x = Math.max(0, Math.min(x, canvas.clientWidth - node.offsetWidth));
    y = Math.max(0, Math.min(y, canvas.clientHeight - node.offsetHeight));
    node.style.left = x + "px";
    node.style.top = y + "px";
    updateWire();
  });
  handle.addEventListener("pointerup", (ev) => {
    dragging = false;
    node.classList.remove("dragging");
    try { handle.releasePointerCapture(ev.pointerId); } catch (e) {}
  });
}

makeDraggable(nodeMovidesk);
makeDraggable(nodeClickup);
window.addEventListener("resize", layoutNodes);
</script>
</body>
</html>
"""


@router.get("/admin/ui", response_class=HTMLResponse, include_in_schema=False)
def admin_ui() -> HTMLResponse:
    return HTMLResponse(content=_PAGE)
