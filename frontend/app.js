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

// 统一API调用（带日志和错误处理）
async function apiCall(url, options = {}) {
    console.log(`[API] ${options.method || 'GET'} ${url}`);
    try {
        const response = await fetch(url, options);
        const result = await response.json();
        if (!result.success && result.error) {
            throw new Error(result.error);
        }
        console.log('[API Success]', result);
        return result;
    } catch (error) {
        console.error('[API Error]', error);
        throw error;
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
        'edit': '编辑简历',
        'preview': '预览'
    };
    document.getElementById('view-title').textContent = titles[viewName];
    
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
    const section = document.getElementById('update-section').value;
    const content = document.getElementById('update-content').value;
    
    if (!content.trim()) {
        showNotification('请输入更新内容', 'error');
        return;
    }
    
    showNotification('AI正在优化中...', 'success');
    
    try {
        const response = await fetch(`${API_BASE}/api/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ section, content })
        });
        
        const result = await response.json();
        if (result.success) {
            currentResumeData = result.resume_data;
            document.getElementById('resume-data').innerHTML = 
                `<pre>${JSON.stringify(result.resume_data, null, 2)}</pre>`;
            document.getElementById('update-content').value = '';
            showNotification('AI优化完成！');
        } else {
            showNotification('更新失败：' + result.error, 'error');
        }
    } catch (error) {
        showNotification('网络错误：' + error.message, 'error');
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
    const targetLang = prompt('请选择目标语言：\n1. zh-CN (简体中文)\n2. zh-TW (繁体中文)\n3. en-US (英语)', 'en-US');
    
    if (!targetLang) return;
    
    showNotification('AI正在翻译中...', 'success');
    
    try {
        const response = await fetch(`${API_BASE}/api/translate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_lang: targetLang })
        });
        
        const result = await response.json();
        if (result.success) {
            currentResumeData = result.data;
            showNotification('翻译完成！');
            if (document.getElementById('edit-view').classList.contains('active')) {
                loadResume();
            }
        } else {
            showNotification('翻译失败：' + result.error, 'error');
        }
    } catch (error) {
        showNotification('网络错误：' + error.message, 'error');
    }
}

// 导出PDF
async function exportPDF() {
    showNotification('正在生成PDF...', 'success');
    
    try {
        const response = await fetch(`${API_BASE}/api/export/pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resume_data: currentResumeData })
        });
        
        const result = await response.json();
        if (result.success) {
            showNotification(`PDF已导出：${result.filename}`);
        } else {
            showNotification('导出失败：' + result.error, 'error');
        }
    } catch (error) {
        showNotification('网络错误：' + error.message, 'error');
    }
}

// 页面加载完成后初始化
window.addEventListener('DOMContentLoaded', () => {
    console.log('AI简历更新助手已启动');
    // 检查后端连接
    fetch(`${API_BASE}/health`)
        .then(res => res.json())
        .then(data => {
            console.log('后端连接成功:', data);
            showNotification('应用已就绪');
        })
        .catch(err => {
            console.error('后端连接失败:', err);
            showNotification('后端服务未启动，请检查', 'error');
        });
});
