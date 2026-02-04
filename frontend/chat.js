// Chat + JD Targeting (Phase 1)

let pendingResumeData = null;

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

  // refresh edit view JSON
  const el = document.getElementById('resume-data');
  if (el) el.innerHTML = `<pre>${JSON.stringify(currentResumeData, null, 2)}</pre>`;

  const previewEl = document.getElementById('chat-preview');
  if (previewEl) previewEl.textContent = '';

  showNotification('已应用到当前简历');
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
