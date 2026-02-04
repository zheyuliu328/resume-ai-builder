// API基础URL
const DEFAULT_API_BASE = 'http://localhost:5001';

function getApiBase() {
    if (window.location && window.location.protocol && window.location.protocol.startsWith('http')) {
        return window.location.origin;
    }
    if (typeof process !== 'undefined' && process.env && process.env.FLASK_PORT) {
        return `http://localhost:${process.env.FLASK_PORT}`;
    }
    return DEFAULT_API_BASE;
}

const API_BASE = getApiBase();

// 全局状态
let currentResumeData = null;
let isConfigHealthy = false;

function setNavEnabled(enabled) {
    const ids = ['nav-translate', 'nav-export'];
    ids.forEach((id) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.style.opacity = enabled ? '1' : '0.5';
        el.style.pointerEvents = enabled ? 'auto' : 'none';
        el.title = enabled ? '' : '请先完成 API 配置并测试连接';
    });
}

function setStatusPill(id, text, kind = 'neutral') {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    const styles = {
        ok: { bg: '#ecfdf5', fg: '#065f46' },
        warn: { bg: '#fffbeb', fg: '#92400e' },
        err: { bg: '#fef2f2', fg: '#991b1b' },
        neutral: { bg: '#f3f4f6', fg: '#374151' },
        info: { bg: '#eef2ff', fg: '#3730a3' },
    };
    const s = styles[kind] || styles.neutral;
    el.style.background = s.bg;
    el.style.color = s.fg;
}

// 统一API调用（带日志、错误处理、超时）
async function apiCall(url, options = {}) {
    // Use API_BASE by default if caller passes relative path
    const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`;
    const method = options.method || 'GET';
    const timeoutMs = options.timeoutMs || 15000;

    console.log(`[API] ${method} ${fullUrl}`);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(fullUrl, {
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            },
            signal: controller.signal,
            ...options,
        });

        const contentType = response.headers.get('content-type') || '';
        const result = contentType.includes('application/json') ? await response.json() : { success: response.ok, data: await response.text() };

        if (!response.ok) {
            const msg = (result && result.error) ? result.error : `HTTP ${response.status}`;
            throw new Error(msg);
        }

        if (result && result.success === false && result.error) {
            throw new Error(result.error);
        }

        console.log('[API Success]', result);
        return result;
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error(`请求超时（${timeoutMs}ms）：${url}`);
        }
        console.error('[API Error]', error);
        throw error;
    } finally {
        clearTimeout(timeout);
    }
}

// 更新供应商默认值
function updateProviderDefaults() {
    const provider = document.getElementById('api-provider').value;
    const baseUrl = document.getElementById('base-url');
    const model = document.getElementById('model');
    
    if (provider === 'anthropic') {
        baseUrl.value = 'https://api.anthropic.com';
        model.value = 'claude-sonnet-4-5-20250929';
    } else {
        baseUrl.value = 'https://api.xstx.info/v1';
        model.value = 'claude-opus-4-5-20251101';
    }
}

// 测试API连接
async function testConnection() {
    const status = document.getElementById('config-status');
    status.style.display = 'block';
    status.style.background = '#fef3c7';
    status.innerHTML = '⏳ 测试连接中...';
    
    try {
        const result = await apiCall(`${API_BASE}/health`);
        status.style.background = '#d1fae5';
        status.innerHTML = '✅ 后端连接成功！';
    } catch (error) {
        status.style.background = '#fee2e2';
        status.innerHTML = `❌ 连接失败: ${error.message}`;
    }
}

// 显示通知
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// 切换视图
function switchView(viewName, evt) {
    // 更新导航激活状态
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });

    const clickedNav = evt && evt.target ? evt.target.closest('.nav-item') : null;
    if (clickedNav) {
        clickedNav.classList.add('active');
    } else {
        const navByView = document.querySelector(`.nav-item[data-view="${viewName}"]`);
        if (navByView) {
            navByView.classList.add('active');
        }
    }
    
    // 更新视图
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    const targetView = document.getElementById(`${viewName}-view`);
    if (!targetView) {
        console.warn(`[View] 未找到视图: ${viewName}`);
        return;
    }
    targetView.classList.add('active');
    
    // 更新标题
    const titles = {
        'config': 'API配置',
        'import': '导入PDF',
        'edit': '编辑简历',
        'preview': '预览'
    };
    document.getElementById('view-title').textContent = titles[viewName] || 'AI简历助手';
    
    // 加载对应数据
    if (viewName === 'edit') {
        loadResume();
    } else if (viewName === 'preview') {
        loadPreview();
    }
}

// 保存API配置
async function saveConfig() {
    const apiKey = document.getElementById('api-key').value;
    const baseUrl = document.getElementById('base-url').value;
    const model = document.getElementById('model').value;
    
    if (!apiKey) {
        showNotification('请输入API Key', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey, base_url: baseUrl, model })
        });
        
        const result = await response.json();
        if (result.success) {
            showNotification('配置保存成功！');
        } else {
            showNotification('配置保存失败：' + result.error, 'error');
        }
    } catch (error) {
        showNotification('网络错误：' + error.message, 'error');
    }
}

// 加载简历数据
async function loadResume() {
    try {
        const response = await fetch(`${API_BASE}/api/resume`);
        const result = await response.json();
        
        if (result.success) {
            currentResumeData = result.data;
            document.getElementById('resume-data').innerHTML = 
                `<pre>${JSON.stringify(result.data, null, 2)}</pre>`;
            showNotification('简历数据已加载');
        } else {
            document.getElementById('resume-data').innerHTML = 
                `<p style="color: #ef4444;">加载失败：${result.error}</p>`;
        }
    } catch (error) {
        document.getElementById('resume-data').innerHTML = 
            `<p style="color: #ef4444;">网络错误：${error.message}</p>`;
    }
}

// 保存简历数据
async function saveResume() {
    if (!currentResumeData) {
        showNotification('没有可保存的数据', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/resume`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resume_data: currentResumeData })
        });
        
        const result = await response.json();
        if (result.success) {
            showNotification('简历已保存！');
        } else {
            showNotification('保存失败：' + result.error, 'error');
        }
    } catch (error) {
        showNotification('网络错误：' + error.message, 'error');
    }
}

// AI更新简历部分
async function updateSection() {
    if (!isConfigHealthy) {
        showNotification('请先在「API配置」中保存并测试连接', 'error');
        switchView('config');
        return;
    }

    const section = document.getElementById('update-section').value;
    const content = document.getElementById('update-content').value;

    if (!content.trim()) {
        showNotification('请输入更新内容', 'error');
        return;
    }

    showNotification('AI正在优化中...', 'success');

    try {
        const result = await apiCall('/api/update', {
            method: 'POST',
            body: JSON.stringify({ section, content }),
            timeoutMs: 60000,
        });

        if (result.success) {
            currentResumeData = result.resume_data;
            document.getElementById('resume-data').innerHTML =
                `<pre>${JSON.stringify(result.resume_data, null, 2)}</pre>`;
            document.getElementById('update-content').value = '';
            showNotification('AI优化完成！');
        } else {
            showNotification('更新失败：' + (result.error || '未知错误'), 'error');
        }
    } catch (error) {
        showNotification('请求失败：' + error.message, 'error');
    }
}

// 加载预览
async function loadPreview() {
    const previewContent = document.getElementById('preview-content');
    previewContent.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>生成预览中...</p>
        </div>
    `;
    
    try {
        // 如果没有数据，先加载
        if (!currentResumeData) {
            console.log('[Preview] 数据为空，先加载简历数据...');
            await loadResumeData();
        }

        const payload = currentResumeData ? { resume_data: currentResumeData } : {};
        const response = await fetch(`${API_BASE}/api/export/html`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        if (result.success) {
            // 使用 iframe 渲染预览，避免样式冲突
            previewContent.innerHTML = '';
            const iframe = document.createElement('iframe');
            iframe.id = 'preview-iframe';
            iframe.title = 'Resume Preview';
            iframe.style.width = '100%';
            iframe.style.height = '800px';
            iframe.style.border = '1px solid #e5e7eb';
            iframe.style.borderRadius = '4px';
            iframe.style.display = 'block';
            iframe.srcdoc = result.html;

            iframe.addEventListener('load', () => {
                try {
                    const doc = iframe.contentDocument;
                    const docHeight = doc
                        ? Math.max(doc.documentElement.scrollHeight, doc.body ? doc.body.scrollHeight : 0)
                        : 0;
                    if (docHeight) {
                        iframe.style.height = `${Math.max(docHeight, 800)}px`;
                    }
                } catch (error) {
                    console.warn('[Preview] 无法调整iframe高度:', error);
                }
            });

            previewContent.appendChild(iframe);
        } else {
            previewContent.innerHTML = 
                `<p style="color: #ef4444;">预览失败：${result.error}</p>`;
        }
    } catch (error) {
        previewContent.innerHTML = 
            `<p style="color: #ef4444;">网络错误：${error.message}<br>请确保后端服务已启动 (python backend/api_server.py)</p>`;
    }
}

// 内部加载简历数据（不显示通知）
async function loadResumeData() {
    try {
        const response = await fetch(`${API_BASE}/api/resume`);
        const result = await response.json();
        if (result.success) {
            currentResumeData = result.data;
            return true;
        }
    } catch (error) {
        console.error('[loadResumeData] 加载失败:', error);
    }
    return false;
}

// 翻译简历
async function translateResume() {
    if (!isConfigHealthy) {
        showNotification('请先在「API配置」中保存并测试连接', 'error');
        switchView('config');
        return;
    }

    const targetLang = prompt('请选择目标语言：\n1. zh-CN (简体中文)\n2. zh-TW (繁体中文)\n3. en-US (英语)', 'en-US');
    if (!targetLang) return;

    showNotification('AI正在翻译中...', 'success');

    try {
        const result = await apiCall('/api/translate', {
            method: 'POST',
            body: JSON.stringify({ target_lang: targetLang }),
            timeoutMs: 60000,
        });

        if (result.success) {
            currentResumeData = result.data;
            showNotification('翻译完成！');
            if (document.getElementById('edit-view').classList.contains('active')) {
                loadResume();
            }
        } else {
            showNotification('翻译失败：' + (result.error || '未知错误'), 'error');
        }
    } catch (error) {
        showNotification('请求失败：' + error.message, 'error');
    }
}

// 导出PDF
async function exportPDF() {
    if (!isConfigHealthy) {
        showNotification('请先在「API配置」中保存并测试连接', 'error');
        switchView('config');
        return;
    }

    showNotification('正在生成PDF...', 'success');

    try {
        const result = await apiCall('/api/export/pdf', {
            method: 'POST',
            body: JSON.stringify({ resume_data: currentResumeData }),
            timeoutMs: 90000,
        });

        if (result.success) {
            showNotification(`PDF已导出：${result.filename}`);
        } else {
            showNotification('导出失败：' + (result.error || '未知错误'), 'error');
        }
    } catch (error) {
        showNotification('请求失败：' + error.message, 'error');
    }
}

async function refreshStatus() {
    // Backend health
    try {
        const health = await apiCall('/health', { timeoutMs: 4000 });
        setStatusPill('status-backend', 'Backend: OK', 'ok');

        const issues = (health && health.startup_issues) ? health.startup_issues : [];
        if (issues.length) {
            setStatusPill('status-backend', `Backend: WARN (${issues.length})`, 'warn');
        }
    } catch (e) {
        setStatusPill('status-backend', 'Backend: DOWN', 'err');
        setStatusPill('status-config', 'Config: unknown', 'neutral');
        setStatusPill('status-model', 'Model: —', 'neutral');
        setNavEnabled(false);
        isConfigHealthy = false;
        return;
    }

    // Safe config status
    try {
        const cfg = await apiCall('/api/config/status', { timeoutMs: 4000 });
        const configured = !!(cfg && cfg.configured);
        isConfigHealthy = configured;
        setStatusPill('status-config', configured ? 'Config: OK' : 'Config: missing', configured ? 'ok' : 'warn');
        setStatusPill('status-model', `Model: ${cfg.model || '—'}`, 'neutral');
        setNavEnabled(configured);
    } catch (e) {
        setStatusPill('status-config', 'Config: unknown', 'neutral');
        setStatusPill('status-model', 'Model: —', 'neutral');
        setNavEnabled(false);
        isConfigHealthy = false;
    }
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', () => {
    console.log('AI简历更新助手已启动');
    refreshStatus();
});
