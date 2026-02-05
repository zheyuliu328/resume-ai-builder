// Mission Control (War Room) - minimal UI

let currentApplicationId = null;
let lastGapSet = new Set();

function _pill(text, kind = 'gap') {
  const el = document.createElement('span');
  el.textContent = text;
  el.style.padding = '4px 10px';
  el.style.borderRadius = '999px';
  el.style.fontSize = '12px';
  el.style.border = '1px solid var(--border)';
  el.style.background = 'rgba(255,255,255,0.06)';
  el.style.cursor = kind === 'gap' ? 'pointer' : 'default';
  if (kind === 'gap') {
    el.style.borderColor = 'rgba(255,90,107,0.35)';
    el.style.background = 'rgba(255,90,107,0.12)';
    el.style.color = '#ffd0d6';
  }
  if (kind === 'match') {
    el.style.borderColor = 'rgba(99,255,181,0.30)';
    el.style.background = 'rgba(99,255,181,0.10)';
    el.style.color = '#bfffe0';
  }
  if (kind === 'flash') {
    el.style.boxShadow = '0 0 0 4px rgba(99,255,181,0.12)';
  }
  return el;
}

function _renderGroups(groups) {
  const root = document.getElementById('app-groups');
  if (!root) return;
  root.innerHTML = '';

  const order = ['draft', 'ready', 'applied', 'archived'];
  order.forEach((st) => {
    const items = (groups && groups[st]) ? groups[st] : [];
    const box = document.createElement('div');
    box.style.border = '1px solid var(--border)';
    box.style.borderRadius = '12px';
    box.style.padding = '10px';
    box.style.background = 'rgba(255,255,255,0.03)';

    const title = document.createElement('div');
    title.style.display = 'flex';
    title.style.justifyContent = 'space-between';
    title.style.alignItems = 'center';
    title.style.marginBottom = '8px';
    title.innerHTML = `<span style="font-weight:650;">${st.toUpperCase()}</span><span class="muted" style="font-size:12px;">${items.length}</span>`;
    box.appendChild(title);

    const list = document.createElement('div');
    list.style.display = 'grid';
    list.style.gap = '6px';

    items.slice(0, 20).forEach((it) => {
      const btn = document.createElement('button');
      btn.className = 'btn btn-secondary';
      btn.style.width = '100%';
      btn.style.justifyContent = 'flex-start';
      btn.textContent = it.title ? it.title : it.id.slice(0, 8);
      btn.onclick = () => missionLoad(it.id);
      list.appendChild(btn);
    });

    box.appendChild(list);
    root.appendChild(box);
  });
}

async function missionInit() {
  try {
    const res = await apiCall('/api/applications', { timeoutMs: 8000 });
    if (res && res.success) {
      _renderGroups(res.groups);
    }
  } catch (e) {
    showNotification('Mission 初始化失败：' + e.message, 'error');
  }
}

async function missionLoad(appId) {
  currentApplicationId = appId;
  try {
    const res = await apiCall(`/api/applications/${appId}`, { timeoutMs: 15000 });
    if (!res.success) throw new Error(res.error || 'unknown');

    const app = res.application || {};
    const cap = res.jd_capture || {};
    const resume = res.resume_data || {};
    const gap = res.gap || {};

    // Make resume available to Chat workflows.
    currentResumeData = resume;

    const variantEl = document.getElementById('mission-variant');
    if (variantEl) variantEl.textContent = `variant: ${app.variant_name || '—'} | status: ${app.status || '—'}`;

    const jdEl = document.getElementById('jd-text-preview');
    if (jdEl) jdEl.textContent = cap.text || '';

    const resumeEl = document.getElementById('mission-resume');
    if (resumeEl) resumeEl.textContent = JSON.stringify(resume, null, 2);

    // Render gap/match pills
    const gapRoot = document.getElementById('gap-list');
    const matchRoot = document.getElementById('match-list');
    if (gapRoot) gapRoot.innerHTML = '';
    if (matchRoot) matchRoot.innerHTML = '';

    const gaps = Array.isArray(gap.gaps) ? gap.gaps : [];
    const matches = Array.isArray(gap.matches) ? gap.matches : [];

    const newGapSet = new Set(gaps);

    gaps.slice(0, 40).forEach((g) => {
      const pill = _pill(g, 'gap');
      pill.onclick = () => missionClickGap(g);
      if (gapRoot) gapRoot.appendChild(pill);
    });

    matches.slice(0, 40).forEach((m) => {
      const kind = lastGapSet.has(m) ? 'flash' : 'match';
      const pill = _pill(m, kind === 'flash' ? 'match' : 'match');
      if (kind === 'flash') {
        pill.style.boxShadow = '0 0 0 4px rgba(99,255,181,0.12)';
      }
      if (matchRoot) matchRoot.appendChild(pill);
    });

    lastGapSet = newGapSet;

    showNotification('Mission 已加载');
  } catch (e) {
    showNotification('加载 Application 失败：' + e.message, 'error');
  }
}

function missionClickGap(gapToken) {
  const ta = document.getElementById('chat-instruction');
  if (ta) {
    ta.value = `监测到 Gap：${gapToken}。请在最相关的 section（experience/projects/skills）中补充该技能/能力的证据描述。保持事实与量化结果，schema 不变。`;
  }
  showNotification(`已生成修复指令：${gapToken}`);
}

function missionOpenChat() {
  switchView('chat');
  const ta = document.getElementById('chat-instruction');
  if (ta) ta.focus();
}

async function missionRecompute() {
  if (!currentApplicationId) {
    showNotification('请先选择一个 Application', 'error');
    return;
  }
  try {
    const res = await apiCall(`/api/applications/${currentApplicationId}/recompute`, {
      method: 'POST',
      body: JSON.stringify({}),
      timeoutMs: 30000,
    });
    if (!res.success) throw new Error(res.error || 'unknown');

    // reload full view for green flash effect
    await missionLoad(currentApplicationId);
    showNotification('Recompute 完成');
  } catch (e) {
    showNotification('Recompute 失败：' + e.message, 'error');
  }
}
