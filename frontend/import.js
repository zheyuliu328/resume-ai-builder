// PDF Import (Phase 1: text-based PDFs only)

async function importPdf() {
  const input = document.getElementById('import-pdf');
  const status = document.getElementById('import-status');
  if (!input || !input.files || !input.files[0]) {
    showNotification('请选择一个 PDF 文件', 'error');
    return;
  }

  const file = input.files[0];
  status.style.display = 'block';
  status.className = 'muted';
  status.textContent = '正在导入并解析…';

  try {
    const form = new FormData();
    form.append('file', file);

    // Use fetch directly because this is multipart.
    const res = await fetch(`${API_BASE}/api/import/pdf`, {
      method: 'POST',
      body: form,
    });

    const contentType = res.headers.get('content-type') || '';
    const data = contentType.includes('application/json') ? await res.json() : { success: false, error: await res.text() };

    if (!res.ok || !data.success) {
      const msg = data.hint ? `${data.error} (${data.hint})` : (data.error || `HTTP ${res.status}`);
      throw new Error(msg);
    }

    currentResumeData = data.data;
    // Backend already stored to master.json and set active=master.
    if (typeof setDirty === 'function') setDirty(false);
    if (typeof initVariants === 'function') await initVariants({ silent: true });

    showNotification('导入成功：已生成结构化 JSON（已落盘到 master，可在编辑页查看）');
    status.className = 'muted';
    status.textContent = `导入成功：提取字符 ${data.meta && data.meta.chars ? data.meta.chars : '—'}`;

    // Navigate to edit and render JSON
    switchView('edit');
    const el = document.getElementById('resume-data');
    if (el) el.innerHTML = `<pre>${JSON.stringify(currentResumeData, null, 2)}</pre>`;
  } catch (e) {
    showNotification('导入失败：' + e.message, 'error');
    status.className = 'muted';
    status.textContent = '导入失败：' + e.message;
  }
}
