let activeSlug = null;
let currentPostDetail = null;
let activeTab = 'status';
let currentMode = 2; // Default Modus 2 (Stepper)
let chatSessionId = 'session_' + Date.now();
let chatStarted = false;

let ragPollInterval = null;
let isActivelyIndexingUI = false;
let confirmResolver = null;
let workerStatus = { alive: false, state: 'down', job: null, hint: '' };
let lastKnownPostStatus = null;

function showNotification(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const iconMap = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };

  toast.innerHTML = `
    <div style="display: flex; gap: 0.5rem; align-items: flex-start;">
      <span style="font-size: 1.1rem;">${iconMap[type] || 'ℹ️'}</span>
      <div style="line-height: 1.4;">${escapeHTML(message)}</div>
    </div>
    <button style="background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 1rem; margin-left: 0.5rem;" onclick="this.parentElement.remove()">✕</button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s, transform 0.3s';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function showConfirm(title, message) {
  return new Promise((resolve) => {
    confirmResolver = resolve;
    const tEl = document.getElementById('confirm-modal-title');
    const bEl = document.getElementById('confirm-modal-body');
    const mEl = document.getElementById('confirm-modal');
    if (tEl) tEl.innerText = title;
    if (bEl) bEl.innerText = message;
    if (mEl) mEl.style.display = 'flex';
  });
}

function closeConfirmModal(result) {
  const mEl = document.getElementById('confirm-modal');
  if (mEl) mEl.style.display = 'none';
  if (confirmResolver) {
    confirmResolver(result);
    confirmResolver = null;
  }
}

function openDiscrepancyModal(action) {
  if (action === 'error_rejected') {
    executeResolveDiscrepancy('error_rejected', 'Afgekeurd als inhoudelijke fout');
    return;
  }
  const m = document.getElementById('discrepancy-modal');
  if (m) m.style.display = 'flex';
}

function closeDiscrepancyModal() {
  const m = document.getElementById('discrepancy-modal');
  if (m) m.style.display = 'none';
}

async function handleDiscrepancyFormSubmit(event) {
  event.preventDefault();
  const note = document.getElementById('discrepancy-note-input').value.trim();
  if (!note) {
    showNotification('Toelichting is verplicht bij voortschrijdend inzicht.', 'warning');
    return;
  }
  closeDiscrepancyModal();
  await executeResolveDiscrepancy('progressive_insight', note);
}

function switchAppMode(mode) {
  currentMode = mode;
  const b1 = document.getElementById('btn-mode-1');
  const b2 = document.getElementById('btn-mode-2');
  const b3 = document.getElementById('btn-mode-3');

  if (b1) b1.classList.toggle('active', mode === 1);
  if (b2) b2.classList.toggle('active', mode === 2);
  if (b3) b3.classList.toggle('active', mode === 3);

  const m1 = document.getElementById('modus-1-view');
  const m2 = document.getElementById('modus-2-view');
  const m3 = document.getElementById('modus-3-view');

  if (m1) m1.style.display = (mode === 1) ? 'block' : 'none';
  if (m2) m2.style.display = (mode === 2) ? 'block' : 'none';
  if (m3) m3.style.display = (mode === 3) ? 'block' : 'none';

  if (mode === 1 && !chatStarted) {
    initChatSession();
  } else if (mode === 3) {
    loadSavedAdminToken();
    loadRagStatus().then(data => {
      if (data && data.running) {
        startRagPolling();
      }
    });
  }
}

async function initChatSession() {
  chatStarted = true;
  const initialTopic = "Nieuwe AI en Intentie-gedreven Blogpost";
  try {
    const res = await fetchJSON('/api/chat/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: chatSessionId, topic: initialTopic })
    });
    renderChatMessages(res.messages);
  } catch (err) {
    console.error('Chat init error:', err);
  }
}

async function handleSendChatMessage(event) {
  event.preventDefault();
  const inputEl = document.getElementById('chat-input-field');
  const text = inputEl.value.trim();
  if (!text) return;
  inputEl.value = '';

  try {
    const res = await fetchJSON('/api/chat/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: chatSessionId, message: text })
    });
    renderChatMessages(res.messages);
  } catch (err) {
    showNotification(`Fout bij versturen bericht: ${err.message}`, 'error');
  }
}

function renderChatMessages(messages) {
  const container = document.getElementById('chat-messages');
  if (!container) return;
  container.innerHTML = messages.map(m => `
    <div class="chat-bubble ${m.role}">
      ${escapeHTML(m.content).replace(/\n/g, '<br>')}
    </div>
  `).join('');
  container.scrollTop = container.scrollHeight;
}

function openFinalizeModal() {
  const m = document.getElementById('finalize-modal');
  if (m) m.style.display = 'flex';
}

function closeFinalizeModal() {
  const m = document.getElementById('finalize-modal');
  if (m) m.style.display = 'none';
}

async function handleFinalizeChatSubmit(event) {
  event.preventDefault();
  const slug = document.getElementById('finalize-slug').value.trim();
  const titel = document.getElementById('finalize-titel').value.trim();
  const yolo = document.getElementById('finalize-yolo').checked;

  try {
    const res = await fetchJSON('/api/chat/finalize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: chatSessionId, slug, titel, yolo })
    });
    closeFinalizeModal();
    showNotification(`Blogpost '${slug}' succesvol aangemaakt!`, 'success');
    
    switchAppMode(2);
    await loadPostsList();
    selectPost(slug);
  } catch (err) {
    showNotification(`Fout bij afronden brainstorm: ${err.message}`, 'error');
  }
}

// `hard` markeert de gates die onvoorwaardelijk stoppen. De controlefases (stijl, reeks,
// factcheck, alignment) zijn sinds ADR-010 §3.1 voorwaardelijk: ze stoppen alleen bij een
// blokkerende bevinding, en staan hier dus niet als harde gate.
const PHASES = [
  { id: "intake", label: "Intake", hard: true, block: "richten" },
  { id: "outline", label: "Outline", hard: true, block: "richten" },
  { id: "draft", label: "Draft", hard: false, block: "bouwen" },
  { id: "style", label: "Stijl", hard: false, block: "bouwen" },
  { id: "series", label: "Reeks", hard: false, block: "bouwen" },
  { id: "critique", label: "Critique", hard: false, block: "bouwen" },
  { id: "synthesis", label: "Synthese", hard: true, block: "bouwen" },
  { id: "visuals", label: "Visuals", hard: false, block: "bouwen" },
  { id: "factcheck", label: "Factcheck", hard: false, block: "bouwen" },
  { id: "alignment", label: "Alignment", hard: false, block: "bouwen" },
  { id: "deploy", label: "Deploy", hard: true, block: "oordelen" }
];

// De drie blokken uit ADR-010 §3.1, met wat er aan het eind te beslissen valt.
const BLOCKS = [
  { id: "richten", label: "Richten", gate: "onderwerp, invalshoek en bronnen" },
  { id: "bouwen", label: "Bouwen", gate: "stopt alleen bij een blokkerende bevinding" },
  { id: "oordelen", label: "Oordelen", gate: "lezen in WordPress, dan beslissen" }
];

document.addEventListener('DOMContentLoaded', () => {
  loadPostsList();
  loadRagStatus();
  refreshWorkerStatus();
  setInterval(async () => {
    await refreshWorkerStatus();
    if (activeSlug && currentMode === 2) {
      await loadPostDetail(activeSlug, false);
    } else if (currentMode === 2) {
      loadPostsList();
    }
  }, 3000);
});

// --- API Calls ---

async function fetchJSON(url, options = {}) {
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(errData.detail || 'Fout bij netwerkverzoek');
    }
    return await res.json();
  } catch (err) {
    console.error('API Error:', err);
    throw err;
  }
}

async function loadPostsList() {
  try {
    const data = await fetchJSON('/api/posts');
    const listEl = document.getElementById('posts-list');
    const cntEl = document.getElementById('posts-count');
    if (cntEl) cntEl.innerText = data.count || 0;

    if (!listEl) return;

    if (!data.posts || data.posts.length === 0) {
      listEl.innerHTML = '<div style="color: var(--text-secondary); font-size: 0.85rem;">Nog geen blogposts in posts/ map.</div>';
      return;
    }

    listEl.innerHTML = data.posts.map(p => `
      <div class="post-item ${p.slug === activeSlug ? 'active' : ''}" onclick="selectPost('${p.slug}')">
        <div class="post-item-title">${escapeHTML(p.slug)}</div>
        <div class="post-item-meta">
          <span>fase: <strong>${p.phase || 'intake'}</strong></span>
          <span class="badge badge-${p.status || 'ready'}">${p.status || 'ready'}</span>
        </div>
      </div>
    `).join('');

    if (!activeSlug && data.posts.length > 0) {
      selectPost(data.posts[0].slug);
    }
  } catch (err) {
    const listEl = document.getElementById('posts-list');
    if (listEl) listEl.innerHTML = `<div style="color: var(--status-blocked); font-size: 0.85rem;">Fout bij laden: ${err.message}</div>`;
  }
}

async function selectPost(slug) {
  activeSlug = slug;
  lastKnownPostStatus = null;
  loadPostsList();
  await loadPostDetail(slug, true);
}

async function loadPostDetail(slug, resetTab = false) {
  try {
    const detail = await fetchJSON(`/api/posts/${slug}`);
    const prev = lastKnownPostStatus;
    currentPostDetail = detail;
    if (slug === activeSlug) {
      if (prev === 'running' && detail.status && detail.status !== 'running') {
        if (detail.status === 'blocked') {
          showNotification(`Fase ${detail.phase} geblokkeerd.`, 'warning');
        } else if (detail.status === 'waiting_gate') {
          showNotification(`Fase ${detail.phase} wacht op jouw oordeel.`, 'success');
        } else {
          showNotification(`Fase ${detail.phase} is nu ${detail.status}.`, 'info');
        }
        loadPostsList();
      }
      lastKnownPostStatus = detail.status;
    }
    renderPostDetail(detail, resetTab);
  } catch (err) {
    console.error(`Fout bij laden post ${slug}:`, err);
  }
}

async function refreshWorkerStatus() {
  try {
    workerStatus = await fetchJSON('/api/worker');
  } catch (err) {
    workerStatus = { alive: false, state: 'down', job: null, hint: 'Worker-status onbereikbaar.' };
  }
  renderWorkerBanner();
  if (currentPostDetail) {
    renderControls(currentPostDetail.next, currentPostDetail);
  }
}

function renderWorkerBanner() {
  const el = document.getElementById('worker-banner');
  const text = document.getElementById('worker-banner-text');
  if (!el || !text) return;

  if (workerStatus.alive && workerStatus.state === 'busy' && workerStatus.job) {
    el.style.display = 'flex';
    el.className = 'worker-banner busy';
    text.innerHTML = `Worker voert <strong>${escapeHTML(workerStatus.job.phase)}</strong> uit op <code>${escapeHTML(workerStatus.job.slug)}</code>.`;
    return;
  }
  if (!workerStatus.alive) {
    el.style.display = 'flex';
    el.className = 'worker-banner down';
    const hint = workerStatus.hint || 'Start in een tweede terminal: .venv/bin/python scripts/worker.py --watch';
    text.innerHTML = `Worker draait niet. ${escapeHTML(hint)}`;
    return;
  }
  el.style.display = 'none';
}

function renderPostDetail(detail, resetTab) {
  const titleEl = document.getElementById('post-title');
  const slugEl = document.getElementById('post-slug');
  const badgeEl = document.getElementById('post-status-badge');
  const controlsBar = document.getElementById('controls-bar');
  const viewerCard = document.getElementById('viewer-card');

  if (titleEl) titleEl.innerText = detail.titel || detail.slug;
  if (slugEl) slugEl.innerText = `posts/${detail.slug}`;

  if (badgeEl) {
    const st = detail.status || 'ready';
    badgeEl.className = `badge badge-${st}`;
    badgeEl.innerText = `${st.toUpperCase()} (${detail.phase})`;
  }

  renderStepper(detail);
  renderControls(detail.next, detail);

  const yoloEl = document.getElementById('toggle-yolo');
  const skipEl = document.getElementById('toggle-skip-synth');
  const deferEl = document.getElementById('toggle-defer-critique');

  if (yoloEl) yoloEl.checked = !!detail.yolo_mode;
  if (skipEl) skipEl.checked = !!(detail.flags && detail.flags.skip_synthesis);
  if (deferEl) deferEl.checked = !!(detail.flags && detail.flags.defer_critique);

  if (controlsBar) controlsBar.style.display = 'flex';
  if (viewerCard) viewerCard.style.display = 'block';

  if (resetTab) {
    showTab('status');
  } else {
    showTab(activeTab);
  }
}

function renderStepper(detail) {
  const container = document.getElementById('stepper-bar');
  if (!container) return;
  const currentPhase = detail.phase;
  const currentStatus = detail.status;
  
  let currentIdx = PHASES.findIndex(p => p.id === currentPhase);
  if (currentPhase === 'done' || currentStatus === 'done') {
    currentIdx = PHASES.length; // Alle 11 fasen voltooid!
  }

  let html = '';

  PHASES.forEach((p, idx) => {
    let nodeState = 'pending';
    let dotIcon = (idx + 1).toString();

    if (idx < currentIdx) {
      nodeState = 'completed';
      dotIcon = '✓';
    } else if (idx === currentIdx) {
      if (currentStatus === 'running') {
        nodeState = 'running';
        dotIcon = (idx + 1).toString();
      } else if (currentStatus === 'waiting_gate') {
        nodeState = 'waiting';
        dotIcon = '⏸';
      } else if (currentStatus === 'blocked') {
        nodeState = 'blocked';
        dotIcon = '⚠️';
      } else {
        nodeState = 'running';
        dotIcon = (idx + 1).toString();
      }
    }

    const isHardGate = p.hard ? ' hard-gate' : '';
    const isActive = idx === currentIdx ? ' active' : '';

    html += `
      <div class="step-node ${nodeState}${isActive}${isHardGate}" title="Fase ${p.label}">
        <div class="dot">${dotIcon}</div>
        <div class="step-label">${escapeHTML(p.label)}</div>
      </div>
    `;

    if (idx < PHASES.length - 1) {
      const lineCompleted = idx < currentIdx ? ' completed' : '';
      html += `<div class="step-line${lineCompleted}"></div>`;
    }
  });

  container.innerHTML = renderBlockBar(currentIdx) + `<div class="stepper-phases">${html}</div>`;
}

// De drie blokken boven de fases (ADR-010 §3.1). Elf bolletjes zeggen niet waar een
// beslissing valt; drie blokken wel.
function renderBlockBar(currentIdx) {
  const huidigBlok = currentIdx < PHASES.length ? PHASES[currentIdx].block : 'oordelen';
  const balken = BLOCKS.map(b => {
    const fases = PHASES.filter(p => p.block === b.id);
    const gereed = fases.filter(p => PHASES.indexOf(p) < currentIdx).length;
    const staat = b.id === huidigBlok ? 'active' : (gereed === fases.length ? 'completed' : 'pending');
    return `
      <div class="block-node ${staat}" style="flex: ${fases.length}" title="${escapeHTML(b.gate)}">
        <div class="block-label">${escapeHTML(b.label)}</div>
        <div class="block-meta">${gereed}/${fases.length}</div>
      </div>`;
  }).join('');
  return `<div class="block-bar">${balken}</div>`;
}

function renderControls(nextAction, statusInfo) {
  const bar = document.getElementById('action-buttons');
  if (!bar) return;
  if (!nextAction) {
    bar.innerHTML = '<span>Geen acties.</span>';
    return;
  }

  const act = nextAction.action;
  const phase = nextAction.phase || statusInfo.phase;

  // Alleen bij een gevonden bevinding hoort de discrepantie-keuze (ADR-007). Zonder
  // bevinding schuift de fase automatisch door en is er niets te kiezen.
  const alignment = statusInfo.archival_alignment || {};
  if (statusInfo.phase === 'alignment'
      && statusInfo.status === 'waiting_gate'
      && alignment.status === 'DISCREPANCY_DETECTED') {
    const count = (alignment.discrepancies || []).length;
    bar.innerHTML = `
      <span class="badge badge-waiting">⚠️ ${count} inhoudelijke ${count === 1 ? 'bevinding' : 'bevindingen'} t.o.v. het archief</span>
      <button class="btn btn-success" onclick="openDiscrepancyModal('progressive_insight')">💡 Accepteer als Voortschrijdend Inzicht</button>
      <button class="btn btn-danger" onclick="executeResolveDiscrepancy('error_rejected')">❌ Afwijzen als Inhoudelijke Fout</button>
    `;
    return;
  }

  if (statusInfo.status === 'blocked' || act === 'unblock') {
    const reden = statusInfo.blocked_reason || nextAction.summary || 'geen reden';
    bar.innerHTML = `
      <span class="blocked-reason">Geblokkeerd: ${escapeHTML(reden)}</span>
      <button class="btn" onclick="executeRetry('${phase}')">↺ Opnieuw</button>
    `;
    return;
  }

  if (act === 'run') {
    bar.innerHTML = `
      <button class="btn" onclick="executeRun('${phase}')">▶ Voer uit: run ${phase}</button>
    `;
  } else if (act === 'approve_or_reject') {
    bar.innerHTML = `
      <button class="btn btn-success" onclick="executeApprove()">✓ Keur goed (Approve)</button>
      <button class="btn btn-danger" onclick="executeReject()">✗ Wijs af (Reject)</button>
    `;
  } else if (act === 'approve_deploy_first') {
    bar.innerHTML = `
      <button class="btn btn-success" onclick="openDeployModal()">★ Goedgekeurd voor Deploy</button>
    `;
  } else if (act === 'complete') {
    bar.innerHTML = renderRunningControls(phase, statusInfo);
  } else {
    bar.innerHTML = `<span style="font-size: 0.85rem; color: var(--text-secondary);">${escapeHTML(nextAction.summary || '')}</span>`;
  }
}

function renderRunningControls(phase, statusInfo) {
  const job = workerStatus.job || {};
  const thisJob = workerStatus.alive && job.slug === statusInfo.slug && job.phase === phase;
  if (thisJob) {
    return `<span style="font-size: 0.9rem;">Worker voert <strong>${escapeHTML(phase)}</strong> uit. Even wachten.</span>`;
  }
  if (workerStatus.alive) {
    return `<span style="font-size: 0.9rem;">Fase staat op running. De worker pakt hem bij de volgende ronde op.</span>`;
  }
  const hint = workerStatus.hint || '.venv/bin/python scripts/worker.py --watch';
  return `
    <span class="blocked-reason">Worker draait niet. ${escapeHTML(hint)}</span>
    <button class="btn btn-secondary" onclick="executeComplete('${phase}')">Handmatig afronden</button>
  `;
}

async function executeRun(phase) {
  if (!activeSlug) return;
  try {
    await fetchJSON(`/api/posts/${activeSlug}/run/${phase}`, { method: 'POST' });
    showNotification(`Fase '${phase}' gestart.`, 'info');
    lastKnownPostStatus = 'running';
    loadPostDetail(activeSlug);
    if (!workerStatus.alive) {
      showNotification('Worker draait niet. Start scripts/worker.py --watch.', 'warning', 8000);
    }
  } catch (err) {
    showNotification(`Fout bij run ${phase}: ${err.message}`, 'error');
  }
}

async function executeRetry(phase) {
  if (!activeSlug) return;
  try {
    await fetchJSON(`/api/posts/${activeSlug}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: 'Opnieuw vanuit de UI' }),
    });
    await fetchJSON(`/api/posts/${activeSlug}/run/${phase}`, { method: 'POST' });
    lastKnownPostStatus = 'running';
    showNotification(`Fase '${phase}' opnieuw gestart.`, 'info');
    loadPostDetail(activeSlug);
    if (!workerStatus.alive) {
      showNotification('Worker draait niet. Start scripts/worker.py --watch.', 'warning', 8000);
    }
  } catch (err) {
    showNotification(`Opnieuw starten mislukt: ${err.message}`, 'error');
    loadPostDetail(activeSlug);
  }
}

async function executeComplete(phase) {
  if (!activeSlug) return;
  try {
    await fetchJSON(`/api/posts/${activeSlug}/complete/${phase}`, { method: 'POST' });
    showNotification(`Fase '${phase}' afgerond.`, 'success');
    loadPostDetail(activeSlug);
  } catch (err) {
    showNotification(`Fout bij complete ${phase}: ${err.message}`, 'error');
  }
}

async function executeApprove() {
  if (!activeSlug) return;
  try {
    await fetchJSON(`/api/posts/${activeSlug}/approve`, { method: 'POST' });
    showNotification(`Akkoord gegeven!`, 'success');
    loadPostDetail(activeSlug);
  } catch (err) {
    showNotification(`Fout bij approve: ${err.message}`, 'error');
  }
}

async function executeReject() {
  if (!activeSlug) return;
  try {
    await fetchJSON(`/api/posts/${activeSlug}/reject`, { method: 'POST' });
    showNotification(`Fase afgekeurd, teruggezet naar ready.`, 'warning');
    loadPostDetail(activeSlug);
  } catch (err) {
    showNotification(`Fout bij reject: ${err.message}`, 'error');
  }
}

async function executeResolveDiscrepancy(action, customNote = null) {
  const note = customNote || "Afgekeurd als inhoudelijke fout";

  try {
    await fetchJSON(`/api/posts/${activeSlug}/resolve-alignment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: action, note: note })
    });
    showNotification(`Discrepantie verwerkt (${action})`, 'success');
    loadPostDetail(activeSlug);
  } catch (err) {
    showNotification(`Fout bij verwerken beslissing: ${err.message}`, 'error');
  }
}

async function toggleFlag(flagName, value) {
  if (!activeSlug) return;
  try {
    await fetchJSON(`/api/posts/${activeSlug}/flags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: flagName, value: value })
    });
    loadPostDetail(activeSlug);
  } catch (err) {
    showNotification(`Fout bij instellen vlag: ${err.message}`, 'error');
  }
}

function showTab(tab) {
  activeTab = tab;
  const navBtns = document.querySelectorAll('.tab-btn');
  navBtns.forEach(btn => btn.classList.remove('active'));

  const currentBtn = Array.from(navBtns).find(b => b.getAttribute('onclick') === `showTab('${tab}')`);
  if (currentBtn) currentBtn.classList.add('active');

  const contentEl = document.getElementById('tab-content');
  if (!contentEl) return;
  if (!currentPostDetail) {
    contentEl.innerText = 'Geen post geselecteerd.';
    return;
  }

  if (tab === 'status') {
    // De orkestrator levert de tabel; die is gegroepeerd per blok (ADR-010 §3.1).
    // renderStatusMarkdown blijft als terugval voor een oude server zonder dat veld.
    contentEl.innerHTML = currentPostDetail.markdown_table
      ? `<pre style="white-space: pre-wrap; font-family: inherit;">${escapeHTML(currentPostDetail.markdown_table)}</pre>`
      : renderStatusMarkdown(currentPostDetail);
  } else if (tab === 'bevindingen') {
    loadBevindingenTab(contentEl);
  } else if (tab === 'archief') {
    loadArchiefTabContent(contentEl);
  } else {
    const artKey = tab === 'grok' ? 'grok_feedback' : tab;
    const content = currentPostDetail.artefact_contents ? currentPostDetail.artefact_contents[artKey] : null;
    if (content) {
      contentEl.innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit;">${escapeHTML(content)}</pre>`;
    } else {
      contentEl.innerHTML = `<em>Artefact '${tab}' ontbreekt of is leeg voor deze post.</em>`;
    }
  }
}

// De bevindingen van alle controlefases in één lijst (ADR-010 §6, stap 3). Ze worden bij
// het opvragen afgeleid uit de rapporten op schijf, dus dit overzicht kan niet verouderen.
async function loadBevindingenTab(container) {
  container.innerHTML = '<em>Bevindingen ophalen...</em>';
  try {
    const data = await fetchJSON(`/api/posts/${activeSlug}/findings`);
    // Een rapport dat niet te lezen is telt nul bevindingen. Zonder deze waarschuwing
    // leest groen als "alles in orde", terwijl er niets is gecontroleerd.
    const onbetrouwbaar = data.phases.filter(f => f.staat === 'onleesbaar' || f.staat === 'verouderd');
    let kop;
    if (data.blocking) {
      kop = `<span class="badge badge-blocked">${data.blocking} blokkerend</span>`;
    } else if (onbetrouwbaar.length) {
      kop = `<span class="badge badge-waiting">${onbetrouwbaar.length} rapport(en) niet bruikbaar</span>`;
    } else {
      kop = `<span class="badge badge-done">geen blokkerende bevinding</span>`;
    }
    const rijen = data.phases.map(f => `
      <tr>
        <td>${escapeHTML(f.phase)}</td>
        <td>${escapeHTML(f.staat)}</td>
        <td>${f.blocking}</td>
        <td>${f.advisory}</td>
      </tr>`).join('');
    const lijst = data.findings.length
      ? data.findings.map(b => `
          <li>
            <strong>${b.severity === 'blocking' ? '🔴' : '🟡'} ${escapeHTML(b.phase)} · ${escapeHTML(b.categorie)}</strong>
            <span style="color: var(--text-muted);">(${escapeHTML(b.waar)})</span><br>
            ${escapeHTML(b.wat)}
            ${b.suggestie ? `<br><em>suggestie: ${escapeHTML(b.suggestie)}</em>` : ''}
          </li>`).join('')
      : '<li><em>Geen bevindingen.</em></li>';

    container.innerHTML = `
      <div style="margin-bottom: 12px;">${kop}
        <span style="color: var(--text-muted); margin-left: 8px;">${data.advisory} ter overweging</span>
      </div>
      <table class="phase-table">
        <thead><tr><th>Fase</th><th>Staat</th><th>Blokkerend</th><th>Ter overweging</th></tr></thead>
        <tbody>${rijen}</tbody>
      </table>
      <ul style="margin-top: 16px; line-height: 1.6;">${lijst}</ul>`;
  } catch (err) {
    container.innerHTML = `<div style="color: var(--danger-color);">Bevindingen ophalen mislukt: ${escapeHTML(err.message)}</div>`;
  }
}

// Het rapport wordt geschreven door de subagent archief-consistentie-check in fase 5c
// (ADR-007). Dit tabblad toont het; het start geen analyse. De knop ververst het verdict
// in state.json op basis van het rapport dat op schijf staat.
async function loadArchiefTabContent(container) {
  const bestaand = currentPostDetail && currentPostDetail.artefact_contents
    ? currentPostDetail.artefact_contents['archief-consistentie.md']
    : null;

  if (!bestaand) {
    container.innerHTML = `<em>Nog geen <code>archief-consistentie.md</code> voor <code>${escapeHTML(activeSlug)}</code>. `
      + `Draai eerst fase 5c (<code>run alignment</code>); de subagent archief-consistentie-check schrijft het rapport.</em>`;
    return;
  }

  container.innerHTML = `
    <div style="margin-bottom: 12px;">
      <button class="btn" onclick="refreshAlignmentVerdict()">🔄 Verdict opnieuw inlezen</button>
    </div>
    <pre style="white-space: pre-wrap; font-family: inherit; color: var(--text-primary);">${escapeHTML(bestaand)}</pre>`;
}

async function refreshAlignmentVerdict() {
  try {
    const data = await fetchJSON(`/api/posts/${activeSlug}/validate-alignment`, { method: 'POST' });
    showNotification(`Verdict ingelezen: ${data.alignment_status}`, data.is_discrepant ? 'warning' : 'success');
    await loadPostDetail(activeSlug);
  } catch (err) {
    showNotification(`Verdict inlezen mislukt: ${err.message}`, 'error');
  }
}

function renderStatusMarkdown(detail) {
  const flags = detail.flags || {};
  let md = `### Statustabel: ${escapeHTML(detail.titel || detail.slug)}\n\n`;
  md += `* **Fase**: \`${detail.phase}\` | **Status**: \`${detail.status}\` | **YOLO**: \`${detail.yolo_mode ? 'JA' : 'NEE'}\`*\n\n`;
  md += `| Fase | Status | Artefact | Poort | Agent |\n|---|---|---|---|---|\n`;

  PHASES.forEach(p => {
    const isCurrent = p.id === detail.phase;
    const stLabel = isCurrent ? `**${detail.status.toUpperCase()}**` : '---';
    const art = detail.artefacts ? detail.artefacts[p.id] || 'missing' : 'missing';
    const gate = p.hard ? '★ Hard' : 'Soft';
    md += `| ${p.label} | ${stLabel} | \`${art}\` | ${gate} | -\ |\n`;
  });

  return `<pre style="white-space: pre-wrap; font-family: inherit;">${escapeHTML(md)}</pre>`;
}

function openInitModal() {
  const m = document.getElementById('init-modal');
  if (m) m.style.display = 'flex';
}

function closeInitModal() {
  const m = document.getElementById('init-modal');
  if (m) m.style.display = 'none';
}

async function handleInitSubmit(event) {
  event.preventDefault();
  const slug = document.getElementById('init-slug').value.trim();
  const titel = document.getElementById('init-titel').value.trim();
  const yolo = document.getElementById('init-yolo').checked;

  try {
    await fetchJSON('/api/posts/init', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug, titel, yolo })
    });
    closeInitModal();
    showNotification(`Nieuwe post '${slug}' aangemaakt!`, 'success');
    await loadPostsList();
    selectPost(slug);
  } catch (err) {
    showNotification(`Fout bij initialiseren: ${err.message}`, 'error');
  }
}

function openDeployModal() {
  const m = document.getElementById('deploy-modal');
  if (m) m.style.display = 'flex';
}

function closeDeployModal() {
  const m = document.getElementById('deploy-modal');
  if (m) m.style.display = 'none';
}

async function handleDeploySubmit(event) {
  event.preventDefault();
  const note = document.getElementById('deploy-note').value.trim();

  try {
    await fetchJSON(`/api/posts/${activeSlug}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ deploy: true, note: note || "Deploy goedgekeurd via Web UI" })
    });
    closeDeployModal();
    showNotification(`Deploy succesvol goedgekeurd!`, 'success');
    loadPostDetail(activeSlug);
  } catch (err) {
    showNotification(`Fout bij approve deploy: ${err.message}`, 'error');
  }
}

function escapeHTML(str) {
  return str ? str.replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  ) : '';
}

// --- Modus 3: Admin & RAG Settings Handlers ---

function getAdminToken() {
  return sessionStorage.getItem('ADMIN_TOKEN') || '';
}

function saveAdminToken() {
  const token = document.getElementById('admin-token-input').value.trim();
  sessionStorage.setItem('ADMIN_TOKEN', token);
  const msg = document.getElementById('token-status-msg');
  if (msg) msg.textContent = '✓ ADMIN_TOKEN opgeslagen in sessie-geheugen.';
  showNotification('ADMIN_TOKEN opgeslagen.', 'success');
}

function loadSavedAdminToken() {
  const input = document.getElementById('admin-token-input');
  if (input) input.value = getAdminToken();
}

async function loadRagStatus() {
  try {
    const data = await fetchJSON('/api/rag/status');
    updateRagDashboard(data);
    return data;
  } catch (err) {
    console.error('Fout bij ophalen RAG status:', err);
    return null;
  }
}

function updateRagDashboard(data) {
  if (!data) return;
  const chunksEl = document.getElementById('rag-stat-chunks');
  const postsEl = document.getElementById('rag-stat-posts');
  const timeEl = document.getElementById('rag-stat-time');
  const articlesListEl = document.getElementById('rag-articles-list');
  const bannerEl = document.getElementById('global-banner');
  const bannerText = document.getElementById('global-banner-text');
  const pBox = document.getElementById('rag-progress-box');
  const pBar = document.getElementById('rag-progress-bar');
  const pPct = document.getElementById('rag-progress-pct');
  const pMsg = document.getElementById('rag-progress-msg');

  if (chunksEl) chunksEl.textContent = data.total_chunks || 0;
  if (postsEl) postsEl.textContent = data.total_posts || 0;
  if (timeEl) timeEl.textContent = data.last_indexed_at ? formatDateStr(data.last_indexed_at) : 'Nooit';

  const pct = data.percentage || 0;
  const isRunning = !!data.running;

  if (bannerEl) {
    bannerEl.style.display = isRunning ? 'flex' : 'none';
    if (bannerText && isRunning) {
      bannerText.innerHTML = `⚠️ <strong>RAG-indexering actief: [ ${pct}% ]</strong> (${data.progress_current || 0}/${data.progress_total || 0} posts) - ${escapeHTML(data.status_message || '')}`;
    }
  }

  if (isRunning && pBox) {
    pBox.style.display = 'block';
    if (pBar) pBar.style.width = `${pct}%`;
    if (pPct) pPct.textContent = `${pct}%`;
    if (pMsg) pMsg.textContent = data.status_message || 'Indexeren...';
  } else if (!isActivelyIndexingUI && pBox) {
    pBox.style.display = 'none';
  }

  if (articlesListEl && data.articles) {
    if (data.articles.length === 0) {
      articlesListEl.innerHTML = '<em>Geen geïndexeerde artikelen gevonden.</em>';
    } else {
      articlesListEl.innerHTML = data.articles.map(a => `
        <div style="display: flex; justify-content: space-between; padding: 0.4rem 0.6rem; border-bottom: 1px solid var(--border-color);">
          <div>
            <strong><code>${escapeHTML(a.slug)}</code></strong>
            ${a.title && a.title !== a.slug ? `<div style="font-size: 0.8rem; color: var(--text-secondary);">${escapeHTML(a.title)}</div>` : ''}
          </div>
          <span style="color: var(--text-secondary); font-size: 0.8rem;">${a.chunks_count} chunks | Gewijzigd: ${formatDateStr(a.last_modified)}</span>
        </div>
      `).join('');
    }
  }
}

function formatDateStr(str) {
  if (!str) return 'Nooit';
  try {
    const d = new Date(str);
    return isNaN(d.getTime()) ? str : d.toLocaleString('nl-NL');
  } catch (e) {
    return str;
  }
}

// --- Slimme Polling Logica ---

function startRagPolling() {
  if (ragPollInterval) return;
  isActivelyIndexingUI = true;

  const pBox = document.getElementById('rag-progress-box');
  if (pBox) pBox.style.display = 'block';

  ragPollInterval = setInterval(async () => {
    const data = await loadRagStatus();
    if (!data) return;

    if (!data.running) {
      stopRagPolling(data);
    }
  }, 250);
}

function stopRagPolling(data) {
  if (ragPollInterval) {
    clearInterval(ragPollInterval);
    ragPollInterval = null;
  }

  const pBox = document.getElementById('rag-progress-box');
  const pBar = document.getElementById('rag-progress-bar');
  const pPct = document.getElementById('rag-progress-pct');
  const pMsg = document.getElementById('rag-progress-msg');
  const bannerEl = document.getElementById('global-banner');

  if (bannerEl) bannerEl.style.display = 'none';

  if (isActivelyIndexingUI && pBox) {
    isActivelyIndexingUI = false;
    pBox.style.display = 'block';
    if (pBar) pBar.style.width = '100%';
    if (pPct) pPct.textContent = '100%';
    if (pMsg) pMsg.textContent = `✅ RAG-indexering voltooid! (${data ? data.total_posts : 70} artikelen, ${data ? data.total_chunks : 2915} chunks)`;

    setTimeout(() => {
      if (pBox) pBox.style.display = 'none';
    }, 3000);
  } else if (pBox) {
    pBox.style.display = 'none';
  }
}

async function triggerRagReindex(isIncrementalOnly) {
  const token = getAdminToken();
  const purge = document.getElementById('rag-purge-checkbox').checked;

  if (purge) {
    const confirmed = await showConfirm(
      '⚠️ RAG Index Wissen & Herbouwen',
      'Weet je zeker dat je de gehele RAG index wilt wissen en alle 57+ artikelen opnieuw wilt ophalen van edwinvandillen.nl?'
    );
    if (!confirmed) return;
  }

  try {
    const res = await fetchJSON('/api/rag/reindex-async', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Token': token
      },
      body: JSON.stringify({
        purge_and_rebuild: purge,
        incremental: isIncrementalOnly && !purge
      })
    });

    showNotification(`🚀 ${res.message}`, 'success');
    startRagPolling();

  } catch (err) {
    showNotification(`Fout bij starten indexering: ${err.message}`, 'error');
  }
}
