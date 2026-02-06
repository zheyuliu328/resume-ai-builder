// Mission Control (War Room) - minimal UI

let currentApplicationId = null;
let lastGapSet = new Set();

function _pill(text, kind = 'gap') {
  const el = document.createElement('span');
  el.textContent = text;
  el.className = 'pill';
  if (kind === 'gap') {
    el.classList.add('pill--gap');
  } else if (kind === 'match') {
    el.classList.add('pill--match');
  }
  if (kind === 'flash') {
    el.classList.add('pill--match', 'pill--flash');
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
    box.className = 'status-group';

    const header = document.createElement('div');
    header.className = 'status-group-header';
    header.innerHTML = `<span class="status-group-title">${st}</span><span class="status-group-count">${items.length}</span>`;
    box.appendChild(header);

    const list = document.createElement('div');
    list.style.display = 'grid';
    list.style.gap = '6px';

    items.slice(0, 20).forEach((it) => {
      const btn = document.createElement('button');
      btn.className = 'app-item';
      btn.textContent = it.title ? it.title : it.id.slice(0, 8);
      btn.onclick = () => {
        // Remove active from all
        root.querySelectorAll('.app-item').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        missionLoad(it.id);
      };
      list.appendChild(btn);
    });

    box.appendChild(list);
    root.appendChild(box);
  });
}

function missionDemoFill(reason = 'manual') {
  // Dev-only demo content for styling/iteration (hands-off visual QA)
  try {
    const isLocal = location && (location.hostname === 'localhost' || location.hostname === '127.0.0.1');
    const params = new URLSearchParams(location.search || '');
    const enabled = isLocal && (params.get('demo') === '1' || localStorage.getItem('rab-demo') === '1');
    if (!enabled) return false;

    const jdEl = document.getElementById('jd-text-preview');
    const resumeEl = document.getElementById('mission-resume');
    if (!jdEl || !resumeEl) return false;

    // Only fill if empty (avoid overwriting real data)
    if ((jdEl.textContent || '').trim() || (resumeEl.textContent || '').trim()) return false;

    jdEl.textContent = [
      'Company: Example Analytics Co.',
      'Role: Data Analyst (Growth)',
      '',
      'Responsibilities',
      '- Build dashboards and weekly reporting for growth KPIs',
      '- Design A/B tests and analyze results with statistical rigor',
      '- Partner with product and marketing to define success metrics',
      '',
      'Requirements',
      '- SQL (advanced), Python (pandas), and data visualization',
      '- Experience with experimentation and causal inference',
      '- Strong communication; can translate data → decisions',
      '',
      'Nice to have',
      '- Airflow / dbt, Looker, and metrics layer concepts',
    ].join('\n');

    resumeEl.textContent = [
      '哲宇 / Zheyu',
      'Email: you@example.com | GitHub: github.com/you',
      '',
      'SUMMARY',
      'Data analyst with a track record of shipping metric systems and experiment insights. Local-first tooling builder.',
      '',
      'EXPERIENCE',
      '- ByteDance | Data Analyst Intern (2024.07–2024.12)',
      '  • Built weekly growth dashboard (SQL + BI), reducing manual reporting time by 80%.',
      '  • Designed A/B test analysis pipeline; improved decision speed by 2 days per iteration.',
      '  • Partnered with PMM to define north-star metrics and guardrails.',
      '',
      'PROJECTS',
      '- Resume AI Builder (local-first)',
      '  • JD → gaps → targeted variants → smart PDF fit (TRIMMED marked).',
      '  • Controlled edits: preview → apply; multi-language export.',
      '',
      'SKILLS',
      'SQL • Python (pandas) • Experimentation • Dashboarding • Communication',
    ].join('\n');

    // Demo gaps/matches
    const gapRoot = document.getElementById('gap-list');
    const matchRoot = document.getElementById('match-list');
    if (gapRoot) gapRoot.innerHTML = '';
    if (matchRoot) matchRoot.innerHTML = '';

    const gaps = ['causal inference', 'dbt', 'metrics layer'];
    const matches = ['SQL', 'Python (pandas)', 'A/B tests', 'dashboards'];

    gaps.forEach((g) => {
      const pill = _pill(g, 'gap');
      pill.onclick = () => missionClickGap(g);
      gapRoot && gapRoot.appendChild(pill);
    });

    matches.forEach((m) => {
      const pill = _pill(m, 'match');
      matchRoot && matchRoot.appendChild(pill);
    });

    const variantEl = document.getElementById('mission-variant');
    if (variantEl) variantEl.textContent = `demo | reason: ${reason}`;

    const badge = document.getElementById('mission-demo-badge');
    if (badge) badge.style.display = 'inline-flex';

    showNotification('Mission demo data injected (demo=1)', 'info');
    return true;
  } catch (e) {
    return false;
  }
}

// Expose for console usage
window.__demoFillMission = missionDemoFill;

async function missionInit() {
  try {
    const res = await apiCall('/api/applications', { timeoutMs: 8000 });
    if (res && res.success) {
      _renderGroups(res.groups);

      // Auto-inject demo content if no applications exist (dev-only)
      const hasAny = res.groups && Object.values(res.groups).some((arr) => Array.isArray(arr) && arr.length);
      if (!hasAny) missionDemoFill('no-apps');
    }
  } catch (e) {
    // If backend is down, still allow demo fill to support styling iteration.
    missionDemoFill('init-failed');
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
      gapRoot && gapRoot.appendChild(pill);
    });

    matches.slice(0, 40).forEach((m) => {
      const isNewMatch = lastGapSet.has(m);
      const pill = _pill(m, isNewMatch ? 'flash' : 'match');
      matchRoot && matchRoot.appendChild(pill);
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
