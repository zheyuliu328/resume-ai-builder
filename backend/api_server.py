#!/usr/bin/env python3
"""
Flask API服务 - 为Electron前端提供RESTful接口
"""
from flask import Flask, request, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename

# variants_store is a local helper (imported via sys.path below)
from variants_store import (
    ensure_dirs,
    list_variants,
    load_json,
    save_json,
    get_master_path,
    get_variant_path,
    get_history_dir,
    write_snapshot,
    list_history,
    read_active_variant,
    write_active_variant,
)

# Mission Control (local-first)
from application_store import create_application, load_application, save_application, set_status
from gap_engine import gap_analyze

# NOTE: keep imports local-first; no heavy deps.

from flask_cors import CORS
import sys
import os
import json
import logging
from functools import wraps
from dotenv import load_dotenv
from pathlib import Path
from typing import Any, Dict
from datetime import datetime, timezone
from collections import Counter
from statistics import mean

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

# Local utilities
sys.path.append(str(ROOT_DIR / 'tools'))
from pdf_to_resume_json import extract_text, to_json  # type: ignore

# Local data store (variants)
DATA_DIR = ROOT_DIR / 'data'
ensure_dirs(DATA_DIR)
MASTER_PATH = get_master_path(DATA_DIR)


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
    """Run lightweight startup checks and return a list of human-friendly issues."""
    issues = []
    try:
        import anthropic  # noqa: F401
    except ImportError:
        issues.append("missing_dependency:anthropic")
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        issues.append("missing_dependency:playwright")
    if not os.getenv('CLAUDE_API_KEY'):
        issues.append("missing_env:CLAUDE_API_KEY")

    if issues:
        logger.warning("Startup checks failed: %s", ", ".join(issues))
    else:
        logger.info("✅ Startup checks passed")

    return issues


# 获取前端目录路径
FRONTEND_DIR = ROOT_DIR / 'frontend'

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

config = {
    'api_key': os.getenv('CLAUDE_API_KEY', ''),
    'base_url': os.getenv('CLAUDE_BASE_URL', 'https://api.anthropic.com'),
    'model': os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-5-20250929')
}

# Startup diagnostic snapshot (kept in-memory)
STARTUP_ISSUES = []

# 备用模型列表（按优先级排序）
FALLBACK_MODELS = [
    'claude-opus-4-5-20251101',
    'claude-sonnet-4-5-20250929',
    'claude-3-5-sonnet-20241022',
    'gpt-4o-mini'
]


def call_ai_with_fallback(builder, prompt, max_tokens=4096):
    """Call AI with a fallback model list.

    Returns the provider response object.
    """
    models_to_try = [builder.model] + [m for m in FALLBACK_MODELS if m != builder.model]

    for model in models_to_try:
        try:
            logger.info(f"🤖 Trying model: {model}")
            message = builder.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            logger.info(f"✅ Model {model} success")
            return message
        except Exception as e:
            logger.warning(f"⚠️ Model {model} failed: {str(e)}")
            if model == models_to_try[-1]:
                raise Exception(f"All models failed. Last error: {str(e)}")
            continue


def extract_json_from_text(text: str) -> Any:
    """Best-effort JSON extraction from a model response text."""
    import json as _json
    import re as _re

    m = _re.search(r"\{.*\}", text, _re.DOTALL)
    if not m:
        m = _re.search(r"\[.*\]", text, _re.DOTALL)
    if not m:
        raise ValueError("no_json_found")
    return _json.loads(m.group(0))


@app.route('/api/config', methods=['POST'])
@handle_errors
def set_config():
    """Update runtime API config (in-memory)."""
    global config
    payload = request.json or {}
    # Only allow known keys
    for k in ['api_key', 'base_url', 'model']:
        if k in payload:
            config[k] = payload[k]
    logger.info("Config updated")
    return jsonify({'success': True, 'message': 'Config updated'})


@app.route('/api/config/status', methods=['GET'])
@handle_errors
def config_status():
    """Return a safe, read-only config snapshot (no secrets)."""
    return jsonify({
        'success': True,
        'configured': bool(config.get('api_key')),
        'base_url': config.get('base_url', ''),
        'model': config.get('model', ''),
    })


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
        builder.client.messages.create(
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
    data = request.json or {}
    if not isinstance(data.get('resume_data'), dict):
        return jsonify({'success': False, 'error': 'bad_request'}), 400

    builder = ResumeBuilder(config['api_key'], config['base_url'], config['model'])
    builder.resume_data = data['resume_data']
    builder._save_resume()

    # Also persist to active variant store (optional, local)
    try:
        active = read_active_variant(DATA_DIR) or 'master'
        if active == 'master':
            save_json(MASTER_PATH, builder.resume_data)
        else:
            save_json(get_variant_path(DATA_DIR, active), builder.resume_data)

        # Snapshot history (explicit save)
        ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        write_snapshot(DATA_DIR, active, builder.resume_data, ts=ts)
    except Exception as e:
        logger.warning(f"variant save skipped: {e}")

    return jsonify({'success': True, 'message': '简历已保存'})


@app.route('/api/update', methods=['POST'])
@handle_errors
def update_section():
    """Preview-first mutation endpoint.

    Request JSON:
      { section: str, content: str, resume_data?: dict, apply?: bool }

    Semantics:
      - apply=false (default): return suggested resume_data WITHOUT persisting.
      - apply=true: persist (explicit) and return updated resume_data.
    """
    data = request.json or {}
    section = data.get('section')
    content = data.get('content')
    apply_flag = bool(data.get('apply', False))

    if not section or content is None:
        return jsonify({'success': False, 'error': 'bad_request'}), 400

    builder = ResumeBuilder(config['api_key'], config['base_url'], config['model'])

    # Prefer caller-provided baseline so preview reflects current UI state.
    if isinstance(data.get('resume_data'), dict):
        builder.resume_data = data['resume_data']

    result = builder.update_section(section, content, apply=apply_flag)

    # Persist to active variant store only when explicitly applied.
    if apply_flag:
        try:
            active = read_active_variant(DATA_DIR) or 'master'
            if active == 'master':
                save_json(MASTER_PATH, builder.resume_data)
            else:
                save_json(get_variant_path(DATA_DIR, active), builder.resume_data)

            ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            write_snapshot(DATA_DIR, active, builder.resume_data, ts=ts)
        except Exception as e:
            logger.warning(f"variant save skipped: {e}")

    return jsonify({'success': True, 'data': result, 'resume_data': builder.resume_data, 'applied': apply_flag})


@app.route('/api/translate', methods=['POST'])
@handle_errors
def translate_resume():
    data = request.json
    builder = ResumeBuilder(config['api_key'], config['base_url'], config['model'])
    target_lang = data['target_lang']
    lang_map = {'zh-CN': '简体中文', 'zh-TW': '繁体中文', 'en-US': '英语'}
    prompt = f"将以下简历翻译成{lang_map.get(target_lang, target_lang)}，返回JSON：\n{json.dumps(builder.resume_data, ensure_ascii=False)}"

    message = call_ai_with_fallback(builder, prompt, max_tokens=2048)
    parsed = extract_json_from_text(message.content[0].text)
    return jsonify({'success': True, 'data': parsed})


@app.route('/api/chat/refine', methods=['POST'])
@handle_errors
def chat_refine():
    """Refine resume content with AI based on a user instruction.

    Request JSON:
      { instruction: str, resume_data: dict, scope?: str }

    Response:
      { success: true, data: <updated_resume_data>, summary: str }

    This endpoint is designed for the in-app chat sidebar.
    """
    payload: Dict[str, Any] = request.json or {}
    instruction = (payload.get('instruction') or '').strip()
    resume_data = payload.get('resume_data')
    scope = (payload.get('scope') or 'resume').strip()

    if not instruction:
        return jsonify({'success': False, 'error': 'missing_instruction'}), 400
    if not isinstance(resume_data, dict):
        return jsonify({'success': False, 'error': 'missing_resume_data'}), 400

    builder = ResumeBuilder(config['api_key'], config['base_url'], config['model'])

    # Keep prompt bounded to reduce cost
    resume_blob = json.dumps(resume_data, ensure_ascii=False)
    prompt = (
        "You are an expert resume editor.\n"
        "Task: apply the user's instruction to the given resume JSON.\n"
        "Rules: keep JSON schema consistent; do not add new top-level keys; keep bullet points concise; preserve existing factual content unless asked to rewrite.\n"
        f"Scope: {scope}\n"
        f"Instruction: {instruction}\n\n"
        f"Resume JSON:\n{resume_blob}\n\n"
        "Return ONLY valid JSON with keys: {\"summary\": string, \"resume_data\": object}."
    )

    message = call_ai_with_fallback(builder, prompt, max_tokens=900)
    parsed = extract_json_from_text(message.content[0].text)
    updated = parsed.get('resume_data') if isinstance(parsed, dict) else None
    summary = parsed.get('summary') if isinstance(parsed, dict) else None

    if not isinstance(updated, dict):
        return jsonify({'success': False, 'error': 'ai_return_invalid'}), 500

    return jsonify({'success': True, 'data': updated, 'summary': summary or ''})


@app.route('/api/jd/analyze', methods=['POST'])
@handle_errors
def jd_analyze():
    """Analyze a JD against current resume and return gaps + suggestions."""

    payload: Dict[str, Any] = request.json or {}
    jd = (payload.get('jd') or '').strip()
    resume_data = payload.get('resume_data')

    if not jd:
        return jsonify({'success': False, 'error': 'missing_jd'}), 400
    if not isinstance(resume_data, dict):
        return jsonify({'success': False, 'error': 'missing_resume_data'}), 400

    # Allow smoke tests without real API keys.
    if not config.get('api_key'):
        import re
        jd_words = re.findall(r"[A-Za-z][A-Za-z0-9_+-]{2,}", jd)
        jd_keywords = [w.lower() for w in jd_words]
        # De-dupe while preserving order
        seen = set()
        jd_keywords = [w for w in jd_keywords if not (w in seen or seen.add(w))]
        resume_text = json.dumps(resume_data, ensure_ascii=False).lower()
        top_keywords = jd_keywords[:10]
        missing = [k for k in top_keywords if k not in resume_text]
        present = [k for k in top_keywords if k in resume_text]
        denom = max(1, len(top_keywords))
        match_score = int(round(100 * len(present) / denom))
        return jsonify({'success': True, 'data': {
            'match_score': match_score,
            'top_keywords': top_keywords,
            'gaps': missing,
            'suggestions': [f"Consider adding evidence of: {k}" for k in missing[:5]],
        }})

    builder = ResumeBuilder(config['api_key'], config['base_url'], config['model'])
    prompt = (
        "You are a recruiter + resume coach.\n"
        "Given a job description and a resume JSON, output:\n"
        "1) match_score (0-100)\n"
        "2) top_keywords (list)\n"
        "3) gaps (list of actionable missing items)\n"
        "4) suggestions (list of edits to improve alignment)\n"
        "Return ONLY JSON with keys: match_score, top_keywords, gaps, suggestions.\n\n"
        f"Job Description:\n{jd}\n\n"
        f"Resume JSON:\n{json.dumps(resume_data, ensure_ascii=False)}"
    )

    message = call_ai_with_fallback(builder, prompt, max_tokens=800)
    parsed = extract_json_from_text(message.content[0].text)
    if not isinstance(parsed, dict):
        return jsonify({'success': False, 'error': 'ai_return_invalid'}), 500
    return jsonify({'success': True, 'data': parsed})


@app.route('/api/jd/parse', methods=['POST'])
@handle_errors
def jd_parse():
    """Parse a JD into structured metadata for creating a target variant.

    Request JSON:
      { jd: string }

    Response:
      { success: true, data: { company_name, role_name, slug, summary } }
    """
    payload: Dict[str, Any] = request.json or {}
    jd = (payload.get('jd') or '').strip()

    if not jd:
        return jsonify({'success': False, 'error': 'missing_jd'}), 400

    # Allow smoke tests without real API keys.
    if not config.get('api_key'):
        # Heuristic fallback (no external calls)
        first_line = jd.splitlines()[0].strip() if jd.splitlines() else jd[:80]
        company = 'unknown'
        role = 'unknown'
        slug = 'target_unknown_unknown'
        return jsonify({'success': True, 'data': {
            'company_name': company,
            'role_name': role,
            'slug': slug,
            'summary': first_line,
        }})

    builder = ResumeBuilder(config['api_key'], config['base_url'], config['model'])

    prompt = (
        "You are an assistant helping create a resume variant from a Job Description.\n"
        "Extract: company_name, role_name, and create a filesystem-safe slug for the resume variant.\n"
        "Rules:\n"
        "- slug must be lowercase and match /^[a-z0-9._-]+$/\n"
        "- slug should start with 'target_'\n"
        "- be concise; if company/role unknown, use 'unknown'\n"
        "Return ONLY JSON with keys: company_name, role_name, slug, summary.\n\n"
        f"Job Description:\n{jd}\n"
    )

    message = call_ai_with_fallback(builder, prompt, max_tokens=250)
    parsed = extract_json_from_text(message.content[0].text)
    if not isinstance(parsed, dict):
        return jsonify({'success': False, 'error': 'ai_return_invalid'}), 500

    company = str(parsed.get('company_name') or 'unknown').strip() or 'unknown'
    role = str(parsed.get('role_name') or 'unknown').strip() or 'unknown'
    slug = str(parsed.get('slug') or '').strip().lower()
    summary = str(parsed.get('summary') or '').strip()

    import re
    def _slugify(s: str) -> str:
        s = (s or '').strip().lower()
        s = re.sub(r"[^a-z0-9._-]+", "_", s)
        s = re.sub(r"_+", "_", s).strip('_')
        return s

    if not slug or not re.match(r"^[a-z0-9._-]+$", slug) or not slug.startswith('target_'):
        slug = f"target_{_slugify(company)}_{_slugify(role)}"
        slug = re.sub(r"_+", "_", slug).strip('_')
        if not slug.startswith('target_'):
            slug = 'target_' + slug

    return jsonify({'success': True, 'data': {
        'company_name': company,
        'role_name': role,
        'slug': slug,
        'summary': summary,
    }})


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
    data = request.json or {}
    builder = ResumeBuilder(config['api_key'], config['base_url'], config['model'])
    if 'resume_data' in data:
        builder.resume_data = data['resume_data']

    filename = data.get('filename', 'resume.pdf')
    target_pages = data.get('target_pages', 1)
    template = data.get('template', 'modern')

    out = builder.export_pdf(filename, target_pages=target_pages, template=template)
    if not (out and isinstance(out, dict) and out.get('filename')):
        return jsonify({'success': False, 'error': 'PDF导出失败'}), 500

    meta = out.get('meta') or {}

    # Persist export history in _meta (explicit user action: export)
    try:
        ts = datetime.now(timezone.utc).isoformat()
        export_rec = {
            'ts': ts,
            'target_pages': int(target_pages) if target_pages else 1,
            'template': template,
            'pages': meta.get('pages'),
            'trimmed': bool(meta.get('trimmed')),
            'trim_summary': meta.get('trim_summary') or '',
            'filename': out.get('filename'),
        }

        if not isinstance(builder.resume_data, dict):
            builder.resume_data = {}
        meta_obj = builder.resume_data.get('_meta')
        if not isinstance(meta_obj, dict):
            meta_obj = {}
        exports = meta_obj.get('exports')
        if not isinstance(exports, list):
            exports = []
        exports.insert(0, export_rec)
        meta_obj['exports'] = exports[:20]
        builder.resume_data['_meta'] = meta_obj

        active = read_active_variant(DATA_DIR) or 'master'
        if active == 'master':
            save_json(MASTER_PATH, builder.resume_data)
        else:
            save_json(get_variant_path(DATA_DIR, active), builder.resume_data)

        snap_ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        write_snapshot(DATA_DIR, active, builder.resume_data, ts=snap_ts)
    except Exception as e:
        logger.warning(f"export meta persist skipped: {e}")

    return jsonify({
        'success': True,
        'filename': out.get('filename'),
        'target_pages': int(target_pages) if target_pages else 1,
        'template': template,
        'meta': meta,
    })


@app.route('/api/export/pdf/download', methods=['GET'])
@handle_errors
def export_pdf_download():
    """Download an exported PDF by filename."""
    filename = (request.args.get('filename') or '').strip()
    if not filename:
        return jsonify({'success': False, 'error': 'missing_filename'}), 400

    # Basic safety: only allow .pdf and no path separators
    if '/' in filename or '\\' in filename or not filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'error': 'bad_filename'}), 400

    path = (ROOT_DIR / filename).resolve()
    if not str(path).startswith(str(ROOT_DIR)):
        return jsonify({'success': False, 'error': 'bad_path'}), 400
    if not path.exists():
        return jsonify({'success': False, 'error': 'file_not_found'}), 404

    return send_file(str(path), as_attachment=True, download_name=filename, mimetype='application/pdf')


@app.route('/api/applications/create', methods=['POST'])
@handle_errors
def applications_create():
    payload: Dict[str, Any] = request.json or {}
    capture_id = (payload.get('jd_capture_id') or '').strip()
    if not capture_id:
        return jsonify({'success': False, 'error': 'missing_jd_capture_id'}), 400

    # Load capture from disk
    cap_path = (DATA_DIR / 'jd_captures' / capture_id).resolve() if not capture_id.endswith('.json') else (DATA_DIR / 'jd_captures' / capture_id).resolve()
    if not str(cap_path).startswith(str((DATA_DIR / 'jd_captures').resolve())):
        return jsonify({'success': False, 'error': 'bad_capture_id'}), 400
    if not cap_path.exists():
        return jsonify({'success': False, 'error': 'capture_not_found'}), 404

    capture = load_json(cap_path)
    jd_text = str((capture or {}).get('text') or '')
    title = str((capture or {}).get('title') or '')

    # Create a dedicated variant by cloning master
    master = get_master_path(DATA_DIR)
    if master.exists():
        base = load_json(master)
    else:
        base = ResumeBuilder(config['api_key'], config['base_url'], config['model']).resume_data

    import uuid
    suffix = str(uuid.uuid4())[:8]
    variant = (payload.get('variant_name') or f"target_app_{suffix}").strip() or f"target_app_{suffix}"

    # Ensure safe name
    import re
    if not re.match(r"^[a-zA-Z0-9._-]+$", variant):
        return jsonify({'success': False, 'error': 'bad_variant_name'}), 400

    vpath = get_variant_path(DATA_DIR, variant)
    if vpath.exists():
        return jsonify({'success': False, 'error': 'variant_exists'}), 409
    save_json(vpath, base)

    # Create Application object
    app = create_application(
        DATA_DIR,
        jd_capture_id=cap_path.name,
        variant_name=variant,
        status='draft',
        meta={
            'title': title,
            'created_from': 'jd_capture',
        },
    )

    return jsonify({'success': True, 'application': asdict(app) if 'asdict' in globals() else {
        'id': app.id,
        'created_at': app.created_at,
        'status': app.status,
        'jd_capture_id': app.jd_capture_id,
        'variant_name': app.variant_name,
        'meta': app.meta,
    }})


@app.route('/api/applications/<app_id>', methods=['GET'])
@handle_errors
def applications_get(app_id: str):
    app = load_application(DATA_DIR, app_id)

    cap_path = (DATA_DIR / 'jd_captures' / app.jd_capture_id)
    capture = load_json(cap_path) if cap_path.exists() else None

    # Load variant resume data
    if app.variant_name == 'master':
        rpath = get_master_path(DATA_DIR)
    else:
        rpath = get_variant_path(DATA_DIR, app.variant_name)
    resume_data = load_json(rpath) if rpath.exists() else {}

    # Gap analysis: prefer jd_analysis keywords if present
    meta = resume_data.get('_meta') if isinstance(resume_data.get('_meta'), dict) else {}
    jd_analysis = meta.get('jd_analysis') if isinstance(meta.get('jd_analysis'), dict) else {}
    top_kw = jd_analysis.get('top_keywords') if isinstance(jd_analysis.get('top_keywords'), list) else None

    jd_text = str((capture or {}).get('text') or '')
    gaps = gap_analyze(jd_text, resume_data, top_keywords=top_kw)

    return jsonify({'success': True, 'application': {
        'id': app.id,
        'created_at': app.created_at,
        'status': app.status,
        'jd_capture_id': app.jd_capture_id,
        'variant_name': app.variant_name,
        'meta': app.meta,
    }, 'jd_capture': capture, 'resume_data': resume_data, 'gap': gaps})


@app.route('/api/applications/<app_id>/recompute', methods=['POST'])
@handle_errors
def applications_recompute(app_id: str):
    app = load_application(DATA_DIR, app_id)

    cap_path = (DATA_DIR / 'jd_captures' / app.jd_capture_id)
    capture = load_json(cap_path) if cap_path.exists() else None
    jd_text = str((capture or {}).get('text') or '')

    if app.variant_name == 'master':
        rpath = get_master_path(DATA_DIR)
    else:
        rpath = get_variant_path(DATA_DIR, app.variant_name)
    resume_data = load_json(rpath) if rpath.exists() else {}

    meta = resume_data.get('_meta') if isinstance(resume_data.get('_meta'), dict) else {}
    jd_analysis = meta.get('jd_analysis') if isinstance(meta.get('jd_analysis'), dict) else {}
    top_kw = jd_analysis.get('top_keywords') if isinstance(jd_analysis.get('top_keywords'), list) else None

    gaps = gap_analyze(jd_text, resume_data, top_keywords=top_kw)

    # persist a snapshot into application meta (not resume)
    app.meta['gap_snapshot'] = {
        'computed_at': datetime.utcnow().isoformat() + 'Z',
        'gaps': gaps.get('gaps', [])[:32],
        'matches': gaps.get('matches', [])[:32],
    }
    save_application(DATA_DIR, app)

    return jsonify({'success': True, 'application': {
        'id': app.id,
        'status': app.status,
        'meta': app.meta,
    }, 'gap': gaps})


@app.route('/api/applications/<app_id>/status', methods=['POST'])
@handle_errors
def applications_set_status(app_id: str):
    payload: Dict[str, Any] = request.json or {}
    status = (payload.get('status') or '').strip()
    app = set_status(DATA_DIR, app_id, status)
    return jsonify({'success': True, 'application': {
        'id': app.id,
        'status': app.status,
    }})


@app.route('/api/variants', methods=['GET'])
@handle_errors
def variants_list():
    variants = list_variants(DATA_DIR)
    active = read_active_variant(DATA_DIR) or 'master'
    return jsonify({'success': True, 'variants': ['master'] + variants, 'active': active})


@app.route('/api/variants/select', methods=['POST'])
@handle_errors
def variants_select():
    payload = request.json or {}
    name = payload.get('name')
    if not name:
        return jsonify({'success': False, 'error': 'missing_name'}), 400

    if name == 'master':
        if not MASTER_PATH.exists():
            return jsonify({'success': False, 'error': 'master_missing'}), 404
        write_active_variant(DATA_DIR, 'master')
        return jsonify({'success': True, 'name': 'master', 'data': load_json(MASTER_PATH)})

    path = get_variant_path(DATA_DIR, name)
    if not path.exists():
        return jsonify({'success': False, 'error': 'variant_missing'}), 404

    write_active_variant(DATA_DIR, name)
    return jsonify({'success': True, 'name': name, 'data': load_json(path)})


@app.route('/api/variants/save', methods=['POST'])
@handle_errors
def variants_save():
    payload = request.json or {}
    name = payload.get('name')
    data = payload.get('data')
    if not name or not isinstance(data, dict):
        return jsonify({'success': False, 'error': 'bad_request'}), 400

    # Snapshot on every explicit save.
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    try:
        write_snapshot(DATA_DIR, name, data, ts=ts)
    except Exception as e:
        logger.warning(f"snapshot write skipped: {e}")

    if name == 'master':
        save_json(MASTER_PATH, data)
        write_active_variant(DATA_DIR, 'master')
        return jsonify({'success': True, 'name': 'master'})

    path = get_variant_path(DATA_DIR, name)
    save_json(path, data)
    write_active_variant(DATA_DIR, name)
    return jsonify({'success': True, 'name': name})


@app.route('/api/variants/history', methods=['GET'])
@handle_errors
def variants_history():
    name = (request.args.get('name') or '').strip()
    limit_raw = (request.args.get('limit') or '').strip()

    if not name:
        return jsonify({'success': False, 'error': 'missing_name'}), 400

    try:
        limit = int(limit_raw) if limit_raw else 20
    except Exception:
        limit = 20

    items = list_history(DATA_DIR, name, limit=limit)
    return jsonify({'success': True, 'name': name, 'history': [{'ts': ts} for ts in items]})


@app.route('/api/variants/rollback', methods=['POST'])
@handle_errors
def variants_rollback():
    payload = request.json or {}
    name = (payload.get('name') or '').strip()
    ts = (payload.get('ts') or '').strip()

    if not name or not ts:
        return jsonify({'success': False, 'error': 'bad_request'}), 400

    snap_path = get_history_dir(DATA_DIR, name) / f'{ts}.json'
    if not snap_path.exists():
        return jsonify({'success': False, 'error': 'snapshot_not_found'}), 404

    data = load_json(snap_path)

    if name == 'master':
        save_json(MASTER_PATH, data)
        write_active_variant(DATA_DIR, 'master')
    else:
        save_json(get_variant_path(DATA_DIR, name), data)
        write_active_variant(DATA_DIR, name)

    return jsonify({'success': True, 'name': name, 'data': data, 'rolled_back_to': ts})


@app.route('/api/variants/create', methods=['POST'])
@handle_errors
def variants_create():
    payload = request.json or {}
    name = payload.get('name')
    source = payload.get('source', 'master')

    if not name:
        return jsonify({'success': False, 'error': 'missing_name'}), 400

    if source == 'master':
        if MASTER_PATH.exists():
            data = load_json(MASTER_PATH)
        else:
            # fallback to in-memory resume_data.json behavior
            data = ResumeBuilder(config['api_key'], config['base_url'], config['model']).resume_data
    else:
        data = payload.get('data')
        if not isinstance(data, dict):
            return jsonify({'success': False, 'error': 'missing_data'}), 400

    path = get_variant_path(DATA_DIR, name)
    if path.exists():
        return jsonify({'success': False, 'error': 'variant_exists'}), 409

    save_json(path, data)
    write_active_variant(DATA_DIR, name)
    return jsonify({'success': True, 'name': name, 'data': data})


@app.route('/api/import/pdf', methods=['POST'])
@handle_errors
def import_pdf():
    """Import a resume PDF (text-based) and convert to JSON.

    Phase 1 goal: get *usable structured data* into resume_data.json-like schema,
    store it as master.json, and set it as the active variant.

    Request: multipart/form-data with field name `file`.
    Response: { success: true, data: <resume_json>, meta: { chars }, stored: { master: true } }
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'missing_file'}), 400

    f = request.files['file']
    if not f.filename:
        return jsonify({'success': False, 'error': 'empty_filename'}), 400

    filename = secure_filename(f.filename)
    if not filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'error': 'not_pdf'}), 400

    raw = f.read()
    if not raw:
        return jsonify({'success': False, 'error': 'empty_file'}), 400

    tmp_dir = ROOT_DIR / '.tmp'
    tmp_dir.mkdir(exist_ok=True)
    tmp_path = tmp_dir / filename
    tmp_path.write_bytes(raw)

    text = extract_text(tmp_path)
    if not text.strip():
        return jsonify({'success': False, 'error': 'no_extractable_text', 'hint': 'Scanned PDFs need OCR (not supported yet).'}), 400

    data = to_json(text)

    # Persist as master
    save_json(MASTER_PATH, data)
    write_active_variant(DATA_DIR, 'master')

    return jsonify({'success': True, 'data': data, 'meta': {'chars': len(text)}, 'stored': {'master': True}})


@app.route('/api/refinery/analytics', methods=['GET'])
@handle_errors
def refinery_analytics():
    """Aggregate simple analytics across variants (local-first).

    Reads from ./data (master + variants). No external calls.
    Writes a cached copy to data/analytics.json (best-effort).
    """

    variants = list_variants(DATA_DIR)
    names = ['master'] + variants

    per_variant = []
    match_scores = []
    gaps_counter: Counter = Counter()
    kw_counter: Counter = Counter()

    def _load_variant(name: str) -> Dict[str, Any]:
        if name == 'master':
            if not MASTER_PATH.exists():
                return {}
            return load_json(MASTER_PATH)
        p = get_variant_path(DATA_DIR, name)
        return load_json(p) if p.exists() else {}

    for name in names:
        data = _load_variant(name)
        meta = data.get('_meta') if isinstance(data, dict) else None
        meta = meta if isinstance(meta, dict) else {}
        jd = meta.get('jd_analysis') if isinstance(meta, dict) else None
        jd = jd if isinstance(jd, dict) else {}

        ms = jd.get('match_score')
        if isinstance(ms, (int, float)):
            match_scores.append(float(ms))

        gaps = jd.get('gaps')
        if isinstance(gaps, list):
            gaps_counter.update([str(x).strip().lower() for x in gaps if str(x).strip()])

        kws = jd.get('top_keywords')
        if isinstance(kws, list):
            kw_counter.update([str(x).strip().lower() for x in kws if str(x).strip()])

        exports = meta.get('exports') if isinstance(meta, dict) else None
        exports = exports if isinstance(exports, list) else []

        per_variant.append({
            'name': name,
            'has_jd_analysis': bool(jd),
            'match_score': ms if isinstance(ms, (int, float)) else None,
            'gaps_count': len(gaps) if isinstance(gaps, list) else 0,
            'keywords_count': len(kws) if isinstance(kws, list) else 0,
            'exports_count': len(exports),
        })

    stats = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'targets_count': len(variants),
        'variants_total': len(names),
        'avg_match_score': round(mean(match_scores), 2) if match_scores else None,
        'top_gaps': gaps_counter.most_common(15),
        'top_keywords': kw_counter.most_common(15),
        'per_variant': per_variant,
    }

    # Best-effort local cache
    try:
        save_json(DATA_DIR / 'analytics.json', stats)
    except Exception as e:
        logger.warning(f"analytics cache write skipped: {e}")

    return jsonify({'success': True, 'data': stats})


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'message': 'API服务运行正常',
        'startup_issues': STARTUP_ISSUES,
        'configured': bool(config.get('api_key')),
    })


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
    STARTUP_ISSUES[:] = validate_startup()
    port = int(os.getenv('FLASK_PORT', 5001))
    logger.info(f"🚀 Flask API启动: http://localhost:{port}")
    # debug defaults to off for stability; enable via FLASK_DEBUG=1
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
