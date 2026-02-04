// Chat + JD Targeting (Phase 1)

let pendingResumeData = null;

function renderOnboardingFromMeta(resumeData) {
  const box = document.getElementById('chat-system');
  const titleEl = document.getElementById('chat-system-title');
  const bodyEl = document.getElementById('chat-system-body');
  const actionsEl = document.getElementById('chat-system-actions');

  if (!box || !titleEl || !bodyEl || !actionsEl) return;

  const meta = resumeData && resumeData._meta ? resumeData._meta : null;
  const isNew = !!(meta && meta.is_new);
  const parse = meta && meta.jd_parse ? meta.jd_parse : null;
  const analysis = meta && meta.jd_analysis ? meta.jd_analysis : null;

  if (!isNew || !parse) {
    box.style.display = 'none';
    return;
  }

  const company = parse.company_name || 'Unknown';
  const role = parse.role_name || 'Role';
  const slug = parse.slug || '';

  const keywords = analysis && Array.isArray(analysis.top_keywords) ? analysis.top_keywords.slice(0, 10) : [];
  const gaps = analysis && Array.isArray(analysis.gaps) ? analysis.gaps.slice(0, 6) : [];
  const match = (analysis && typeof analysis.match_score !== 'undefined') ? analysis.match_score : null;

  titleEl.textContent = `👋 New Target: ${company} / ${role}${slug ? ` (${slug})` : ''}`;

  const lines = [];
  if (match !== null) lines.push(`Match score: ${match}`);
  if (keywords.length) lines.push(`Keywords: ${keywords.join(', ')}`);
  if (gaps.length) {
    lines.push('Top gaps:');
    gaps.forEach((g) => lines.push(`- ${g}`));
  }
  if (parse.summary) lines.push(`\nJD summary: ${parse.summary}`);

  bodyEl.textContent = lines.join('\n');

  // Actions: prefill instruction and run refine (still user-controlled apply)
  actionsEl.innerHTML = '';
  const mkBtn = (label, instruction) => {
    const b = document.createElement('button');
    b.className = 'btn btn-secondary';
    b.textContent = label;
    b.onclick = () => {
      const ta = document.getElementById('chat-instruction');
      if (ta) {
        ta.value = instruction;
        ta.focus();
      }
    };
    return b;
  };

  actionsEl.appendChild(mkBtn('重写 Summary（更贴 JD）', `Based on this JD, rewrite the resume summary (personal.summary) to better match the role. Keep it concise and factual.`));
  actionsEl.appendChild(mkBtn('优化最近一段经历（量化+关键词）', `Improve the most recent experience section to better match the JD. Add metrics if possible, keep claims factual, and align wording to JD keywords.`));
  actionsEl.appendChild(mkBtn('精简到 1 页（更硬核）', `Condense the resume for this JD to fit one page by prioritizing the most relevant experiences and removing weaker bullets. Keep schema consistent.`));

  const go = document.createElement('button');
  go.className = 'btn btn-primary';
  go.textContent = '生成改动建议';
  go.onclick = () => chatRefine();
  actionsEl.appendChild(go);

  box.style.display = 'block';
}

// Called by app.js after variant switch/create
function onVariantChangedForChat(resumeData) {
  try {
    renderOnboardingFromMeta(resumeData || {});
  } catch (e) {
    console.warn('[chat] onboarding render failed', e);
  }
}

async function chatRefine() {
  if (!isConfigHealthy) {
    showNotification('请先完成 API 配置并测试连接', 'error');
    switchView('config');
    return;
  }

  const instruction = (document.getElementById('chat-instruction')?.value || '').trim();
  if (!instruction) {
    showNotification('请输入 Chat 指令', 'error');
    return;
  }

  showNotification('AI 正在生成建议…', 'success');
  pendingResumeData = null;

  try {
    const result = await apiCall('/api/chat/refine', {
      method: 'POST',
      body: JSON.stringify({ instruction, resume_data: currentResumeData || {}, scope: 'resume' }),
      timeoutMs: 90000,
    });

    if (!result.success) {
      throw new Error(result.error || 'unknown');
    }

    pendingResumeData = result.data;
    const summary = result.summary || '';
    const previewEl = document.getElementById('chat-preview');
    if (previewEl) {
      previewEl.textContent = JSON.stringify(pendingResumeData, null, 2);
    }
    const summaryEl = document.getElementById('chat-summary');
    if (summaryEl) summaryEl.textContent = summary ? `Summary: ${summary}` : '';

    showNotification('建议已生成（可预览后 Apply）');
  } catch (e) {
    showNotification('生成失败：' + e.message, 'error');
  }
}

function applyChatSuggestion() {
  if (!pendingResumeData) {
    showNotification('没有可应用的改动（先生成建议）', 'error');
    return;
  }
  currentResumeData = pendingResumeData;
  pendingResumeData = null;
  if (typeof setDirty === 'function') setDirty(true);

  // refresh edit view JSON
  const el = document.getElementById('resume-data');
  if (el) el.innerHTML = `<pre>${JSON.stringify(currentResumeData, null, 2)}</pre>`;

  const previewEl = document.getElementById('chat-preview');
  if (previewEl) previewEl.textContent = '';

  showNotification(`已应用到当前简历（${typeof activeVariantName === 'string' ? activeVariantName : 'active'}，未保存）`);
}

async function analyzeJD() {
  if (!isConfigHealthy) {
    showNotification('请先完成 API 配置并测试连接', 'error');
    switchView('config');
    return;
  }

  const jd = (document.getElementById('jd-text')?.value || '').trim();
  if (!jd) {
    showNotification('请粘贴 JD 文本', 'error');
    return;
  }

  showNotification('AI 正在分析 JD…', 'success');

  try {
    const result = await apiCall('/api/jd/analyze', {
      method: 'POST',
      body: JSON.stringify({ jd, resume_data: currentResumeData || {} }),
      timeoutMs: 90000,
    });

    if (!result.success) {
      throw new Error(result.error || 'unknown');
    }

    const out = document.getElementById('jd-result');
    if (out) out.textContent = JSON.stringify(result.data, null, 2);

    showNotification('JD 分析完成');
  } catch (e) {
    showNotification('分析失败：' + e.message, 'error');
  }
}
