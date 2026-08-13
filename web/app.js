let activeSlug = null;
let currentPostDetail = null;
let activeTab = 'status';
let currentMode = 2; // Default Modus 2 (Stepper)
let chatSessionId = 'session_' + Date.now();
let chatStarted = false;

function switchAppMode(mode) {
  currentMode = mode;
  document.getElementById('btn-mode-1').classList.toggle('active', mode === 1);
  document.getElementById('btn-mode-2').classList.toggle('active', mode === 2);
  
  document.getElementById('modus-1-view').style.display = mode === 1 ? 'block' : 'none';
  document.getElementById('modus-2-view').style.display = mode === 2 ? 'block' : 'none';

  if (mode === 1 && !chatStarted) {
    initChatSession();
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
    alert(`Fout bij versturen bericht: ${err.message}`);
  }
}

function renderChatMessages(messages) {
  const container = document.getElementById('chat-messages');
  container.innerHTML = messages.map(m => `
    <div class="chat-bubble ${m.role}">
      ${escapeHTML(m.content).replace(/\n/g, '<br>')}
    </div>
  `).join('');
  container.scrollTop = container.scrollHeight;
}

function openFinalizeModal() {
  document.getElementById('finalize-modal').style.display = 'flex';
}

function closeFinalizeModal() {
  document.getElementById('finalize-modal').style.display = 'none';
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
    
    // Naadloos overstappen naar Modus 2
    switchAppMode(2);
    await loadPostsList();
    selectPost(slug);
  } catch (err) {
    alert(`Fout bij afronden brainstorm: ${err.message}`);
  }
}

const PHASES = [
  { id: "intake", label: "Intake", hard: false },
  { id: "outline", label: "Outline", hard: false },
  { id: "draft", label: "Draft", hard: false },
  { id: "style", label: "Stijl", hard: false },
  { id: "series", label: "Reeks", hard: false },
  { id: "critique", label: "Critique", hard: false },
  { id: "synthesis", label: "Synthese", hard: true },
  { id: "visuals", label: "Visuals", hard: false },
  { id: "factcheck", label: "Factcheck", hard: true },
  { id: "deploy", label: "Deploy", hard: true }
];

document.addEventListener('DOMContentLoaded', () => {
  loadPostsList();
  setInterval(() => {
    if (activeSlug) {
      loadPostDetail(activeSlug, false);
    } else {
      loadPostsList();
    }
  }, 5000);
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
    document.getElementById('posts-count').innerText = data.count || 0;

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
  } catch (err) {
    document.getElementById('posts-list').innerHTML = `<div style="color: var(--status-blocked); font-size: 0.85rem;">Fout bij laden: ${err.message}</div>`;
  }
}

async function selectPost(slug) {
  activeSlug = slug;
  loadPostsList();
  await loadPostDetail(slug, true);
}

async function loadPostDetail(slug, resetTab = false) {
  try {
    const detail = await fetchJSON(`/api/posts/${slug}`);
    currentPostDetail = detail;

    const statusInfo = detail.status_info;
    const doctorInfo = detail.doctor_info;

    document.getElementById('post-title').innerText = statusInfo.titel || slug;
    document.getElementById('post-slug').innerText = `slug: ${slug} | post_dir: ${statusInfo.post_dir}`;
    
    // Status Badge
    const badgeEl = document.getElementById('post-status-badge');
    badgeEl.innerHTML = `<span class="badge badge-${statusInfo.status}">${statusInfo.status}</span>`;

    // Toggles instellen
    document.getElementById('toggle-yolo').checked = !!statusInfo.yolo_mode;
    document.getElementById('toggle-skip-synth').checked = !!statusInfo.flags.skip_synthesis;
    document.getElementById('toggle-defer-critique').checked = !!statusInfo.flags.defer_critique;

    // Stepper & Controls
    renderStepper(statusInfo, doctorInfo);
    renderControls(statusInfo.next, statusInfo);

    document.getElementById('controls-bar').style.display = 'flex';
    document.getElementById('viewer-card').style.display = 'block';

    if (resetTab) {
      showTab(activeTab);
    } else {
      updateTabContent();
    }
  } catch (err) {
    console.error('Fout bij ophalen post detail:', err);
  }
}

// --- Stepper Rendering ---

function renderStepper(statusInfo, doctorInfo) {
  const currentPhase = statusInfo.phase;
  const currentStatus = statusInfo.status;
  const currentIdx = PHASES.findIndex(p => p.id === currentPhase);
  const probed = doctorInfo.probed || {};

  const container = document.getElementById('stepper-bar');
  let html = '';

  PHASES.forEach((p, idx) => {
    let nodeClass = '';
    let isCompleted = false;

    if (idx < currentIdx) {
      nodeClass = 'completed';
      isCompleted = true;
    } else if (idx === currentIdx) {
      nodeClass = `active ${currentStatus}`;
    }

    if (p.hard) {
      nodeClass += ' hard-gate';
    }

    html += `
      <div class="step-node ${nodeClass}">
        <div class="dot">${idx}</div>
        <div class="step-label">${p.label}</div>
      </div>
    `;

    if (idx < PHASES.length - 1) {
      const lineCompleted = idx < currentIdx;
      html += `<div class="step-line ${lineCompleted ? 'completed' : ''}"></div>`;
    }
  });

  container.innerHTML = html;
}

// --- Controls Rendering ---

function renderControls(nextAction, statusInfo) {
  const bar = document.getElementById('action-buttons');
  if (!nextAction) {
    bar.innerHTML = '<span>Geen acties.</span>';
    return;
  }

  const act = nextAction.action;
  const phase = nextAction.phase || statusInfo.phase;

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
    bar.innerHTML = `
      <button class="btn btn-secondary" onclick="executeComplete('${phase}')">✔ Rond af: complete ${phase}</button>
    `;
  } else {
    bar.innerHTML = `<span style="font-size: 0.85rem; color: var(--text-secondary);">${escapeHTML(nextAction.summary || '')}</span>`;
  }
}

// --- Actions ---

async function executeRun(phase) {
  try {
    await fetchJSON(`/api/posts/${activeSlug}/run/${phase}`, { method: 'POST' });
    loadPostDetail(activeSlug);
  } catch (err) {
    alert(`Fout bij run: ${err.message}`);
  }
}

async function executeComplete(phase) {
  try {
    await fetchJSON(`/api/posts/${activeSlug}/complete/${phase}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    loadPostDetail(activeSlug);
  } catch (err) {
    alert(`Fout bij complete: ${err.message}`);
  }
}

async function executeApprove() {
  try {
    await fetchJSON(`/api/posts/${activeSlug}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: "Via Web UI goedgekeurd" })
    });
    loadPostDetail(activeSlug);
  } catch (err) {
    alert(`Fout bij approve: ${err.message}`);
  }
}

async function executeReject() {
  const note = prompt("Geef een reden op voor afwijzing (optioneel):");
  try {
    await fetchJSON(`/api/posts/${activeSlug}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: note || "Via Web UI afgekeurd" })
    });
    loadPostDetail(activeSlug);
  } catch (err) {
    alert(`Fout bij reject: ${err.message}`);
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
    alert(`Fout bij instellen vlag: ${err.message}`);
  }
}

// --- Tab Viewer ---

function showTab(tabName) {
  activeTab = tabName;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('onclick').includes(tabName));
  });
  updateTabContent();
}

function updateTabContent() {
  if (!currentPostDetail) return;

  const contentEl = document.getElementById('tab-content');
  const statusInfo = currentPostDetail.status_info;

  if (activeTab === 'status') {
    contentEl.innerText = statusInfo.markdown_table || currentPostDetail.markdown_table || "Geen tabel beschikbaar.";
  } else {
    contentEl.innerText = `Laden van artefact '${activeTab}'... (in volgende uitbreiding gekoppeld)`;
  }
}

// --- Modals ---

function openInitModal() {
  document.getElementById('init-modal').style.display = 'flex';
}

function closeInitModal() {
  document.getElementById('init-modal').style.display = 'none';
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
    selectPost(slug);
  } catch (err) {
    alert(`Fout bij aanmaken post: ${err.message}`);
  }
}

function openDeployModal() {
  document.getElementById('deploy-modal').style.display = 'flex';
}

function closeDeployModal() {
  document.getElementById('deploy-modal').style.display = 'none';
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
    loadPostDetail(activeSlug);
  } catch (err) {
    alert(`Fout bij approve deploy: ${err.message}`);
  }
}

function escapeHTML(str) {
  return str ? str.replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  ) : '';
}
