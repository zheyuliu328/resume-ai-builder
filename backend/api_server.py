#!/usr/bin/env python3
"""
Flask API服务 - 为Electron前端提供RESTful接口
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os
import json
import logging
from functools import wraps
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
load_dotenv(ROOT_DIR / '.env')

log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(ROOT_DIR / 'app.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

sys.path.append(str(ROOT_DIR))
from app import ResumeBuilder


def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"{f.__name__} failed: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500
    return wrapper


def validate_startup():
    issues = []
    try:
        import anthropic
    except ImportError:
        issues.append("❌ 缺少 anthropic: pip install anthropic")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        issues.append("⚠️ 缺少 playwright: pip install playwright && playwright install chromium")
    if not os.getenv('CLAUDE_API_KEY'):
        issues.append("⚠️ 未设置 CLAUDE_API_KEY")
    if issues:
        logger.warning("启动检查:\n" + "\n".join(issues))
    else:
        logger.info("✅ 启动检查通过")


# 获取前端目录路径
FRONTEND_DIR = ROOT_DIR / 'frontend'

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

config = {
    'api_key': os.getenv('CLAUDE_API_KEY', ''),
    'base_url': os.getenv('CLAUDE_BASE_URL', 'https://api.anthropic.com'),
    'model': os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-5-20250929')
}

# 备用模型列表（按优先级排序）
FALLBACK_MODELS = [
    'claude-opus-4-5-20251101',
    'claude-sonnet-4-5-20250929',
    'claude-3-5-sonnet-20241022',
    'gpt-4o-mini'
]


def call_ai_with_fallback(builder, prompt, max_tokens=4096):
    """
    带降级策略的AI调用
    如果主模型失败，自动尝试备用模型
    """
    models_to_try = [builder.model] + [m for m in FALLBACK_MODELS if m != builder.model]
    
    for model in models_to_try:
        try:
            logger.info(f"🤖 尝试使用模型: {model}")
            message = builder.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            logger.info(f"✅ 模型 {model} 调用成功")
            return message
        except Exception as e:
            logger.warning(f"⚠️ 模型 {model} 失败: {str(e)}")
            if model == models_to_try[-1]:
                raise Exception(f"所有模型均失败。最后错误: {str(e)}")
            continue


@app.route('/api/config', methods=['POST'])
@handle_errors
def set_config():
    global config
    config.update(request.json)
    logger.info("配置已更新")
    return jsonify({'success': True, 'message': '配置已更新'})


@app.route('/api/config/test', methods=['POST'])
@handle_errors
def test_connection():
    """
    测试API连接
    返回可用的模型和连接状态
    """
    data = request.json
    test_config = {
        'api_key': data.get('api_key', config['api_key']),
        'base_url': data.get('base_url', config['base_url']),
        'model': data.get('model', config['model'])
    }
    
    # 修复URL：移除尾部的 /v1 以避免路径重复
    base_url = test_config['base_url']
    if base_url and base_url.rstrip('/').endswith('/v1'):
        base_url = base_url.rstrip('/')[:-3]
        logger.info(f"🔧 自动修正 base_url: {test_config['base_url']} → {base_url}")
    
    try:
        builder = ResumeBuilder(test_config['api_key'], base_url, test_config['model'])
        # 发送最小测试请求
        message = builder.client.messages.create(
            model=test_config['model'],
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )
        logger.info(f"✅ API连接测试成功: {test_config['model']}")
        return jsonify({
            'success': True,
            'message': f"连接成功！模型 {test_config['model']} 可用",
            'model': test_config['model']
        })
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ API连接测试失败: {error_msg}")
        
        # 提供友好的错误提示
        if '401' in error_msg or 'authentication' in error_msg.lower():
            suggestion = "API Key 无效，请检查是否正确"
        elif '403' in error_msg or 'permission' in error_msg.lower():
            suggestion = "无权访问此模型，请检查API权限或尝试其他模型"
        elif 'connection' in error_msg.lower():
            suggestion = "网络连接失败，请检查基础URL是否正确"
        else:
            suggestion = "请检查配置或尝试备用模型"
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'suggestion': suggestion
        }), 400


@app.route('/api/resume', methods=['GET'])
@handle_errors
def get_resume():
    builder = ResumeBuilder(config['api_key'], config['base_url'], config['model'])
    return jsonify({'success': True, 'data': builder.resume_data})


@app.route('/api/resume', methods=['POST'])
@handle_errors
def save_resume():
    data = request.json
    builder = ResumeBuilder(config['api_key'], config['base_url'], config['model'])
    builder.resume_data = data['resume_data']
    builder._save_resume()
    return jsonify({'success': True, 'message': '简历已保存'})


@app.route('/api/update', methods=['POST'])
@handle_errors
def update_section():
    data = request.json
    builder = ResumeBuilder(config['api_key'], config['base_url'], config['model'])
    result = builder.update_section(data['section'], data['content'])
    return jsonify({'success': True, 'data': result, 'resume_data': builder.resume_data})


@app.route('/api/translate', methods=['POST'])
@handle_errors
def translate_resume():
    import re
    data = request.json
    builder = ResumeBuilder(config['api_key'], config['base_url'], config['model'])
    target_lang = data['target_lang']
    lang_map = {'zh-CN': '简体中文', 'zh-TW': '繁体中文', 'en-US': '英语'}
    prompt = f"将以下简历翻译成{lang_map.get(target_lang, target_lang)}，返回JSON：\n{json.dumps(builder.resume_data, ensure_ascii=False)}"
    
    # 使用带容错的AI调用
    message = call_ai_with_fallback(builder, prompt, max_tokens=4096)
    json_match = re.search(r'\{.*\}', message.content[0].text, re.DOTALL)
    if json_match:
        return jsonify({'success': True, 'data': json.loads(json_match.group())})
    return jsonify({'success': False, 'error': '翻译失败'}), 500


@app.route('/api/export/html', methods=['POST'])
@handle_errors
def export_html():
    data = request.json or {}
    builder = ResumeBuilder(config['api_key'], config['base_url'], config['model'])
    # 如果前端传了有效数据，使用前端数据；否则使用文件中的数据
    if data.get('resume_data') and isinstance(data['resume_data'], dict):
        # 检查数据是否有实际内容（不只是空结构）
        resume_data = data['resume_data']
        has_content = any([
            resume_data.get('personal', {}).get('name'),
            resume_data.get('education'),
            resume_data.get('experience'),
            resume_data.get('projects')
        ])
        if has_content:
            builder.resume_data = resume_data
    # 否则 builder 会自动从 resume_data.json 加载数据
    logger.info(f"生成HTML预览，数据来源: {'前端' if data.get('resume_data') else '文件'}")
    return jsonify({'success': True, 'html': builder.generate_html()})


@app.route('/api/export/pdf', methods=['POST'])
@handle_errors
def export_pdf():
    data = request.json
    builder = ResumeBuilder(config['api_key'], config['base_url'], config['model'])
    if 'resume_data' in data:
        builder.resume_data = data['resume_data']
    filename = builder.export_pdf(data.get('filename', 'resume.pdf'))
    if filename:
        return jsonify({'success': True, 'filename': filename})
    return jsonify({'success': False, 'error': 'PDF导出失败'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'API服务运行正常'})


# 静态文件服务
@app.route('/')
def serve_index():
    """服务前端首页"""
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """服务其他静态文件"""
    return send_from_directory(FRONTEND_DIR, filename)


if __name__ == '__main__':
    validate_startup()
    port = int(os.getenv('FLASK_PORT', 5001))
    logger.info(f"🚀 Flask API启动: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
