#!/usr/bin/env python3
"""
AI简历更新助手
支持增量更新、AI优化、HTML生成和PDF导出
"""
import json
import os
from datetime import datetime
from pathlib import Path
import anthropic

class ResumeBuilder:
    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com", model: str = "claude-sonnet-4-5-20250929"):
        """初始化简历构建器"""
        # 修复URL路径问题：anthropic SDK 会自动添加 /v1/messages
        # 如果用户配置了 /v1 结尾的URL，需要移除以避免路径重复
        if base_url and base_url.rstrip('/').endswith('/v1'):
            base_url = base_url.rstrip('/')[:-3]  # 移除 /v1
        self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        self.model = model
        self.data_file = Path(__file__).resolve().parent / "resume_data.json"
        self.resume_data = self._load_resume()
    
    def _load_resume(self) -> dict:
        """加载现有简历数据"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "personal": {"name": "", "email": "", "phone": "", "summary": ""},
            "education": [],
            "experience": [],
            "projects": [],
            "skills": []
        }
    
    def _save_resume(self):
        """保存简历数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.resume_data, f, ensure_ascii=False, indent=2)
    
    def update_section(self, section: str, content: str):
        """使用AI优化并更新简历部分"""
        prompt = f"""请根据以下新信息，优化并更新简历的{section}部分。
        
现有内容：
{json.dumps(self.resume_data.get(section, []), ensure_ascii=False, indent=2)}

新信息：
{content}

请返回JSON格式的更新内容，保持专业、简洁、突出成果。"""
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # 提取AI返回的内容
        response_text = message.content[0].text
        # 尝试解析JSON
        try:
            import re
            json_match = re.search(r'\{.*\}|\[.*\]', response_text, re.DOTALL)
            if json_match:
                updated_content = json.loads(json_match.group())
                self.resume_data[section] = updated_content
                self._save_resume()
                return updated_content
        except:
            pass
        return response_text
    
    def _safe_render_list(self, items, render_func):
        """安全渲染列表，过滤掉非字典类型的元素"""
        if not items:
            return ''
        valid_items = [item for item in items if isinstance(item, dict)]
        return ''.join([render_func(item) for item in valid_items])
    
    def _safe_get_list(self, data, default=None):
        """安全获取列表，处理字符串情况"""
        if default is None:
            default = []
        if isinstance(data, str):
            return [data] if data else default
        if isinstance(data, list):
            return data
        return default
    
    def generate_html(self, *, template: str = 'modern', style=None, data=None) -> str:
        """生成专业的A4简历HTML

        Params:
          - template: 'modern' | 'compact'
          - style: CSS tuning knobs used by the fit engine (font_size_pt, line_height, padding_cm, section_gap_px)
          - data: optional resume_data override (e.g., trimmed version for fitting)
        """
        style = style or {}
        template = (template or 'modern').strip().lower()
        # Allow generating from an overridden dataset (fit engine)
        resume_data = data if isinstance(data, dict) else self.resume_data

        # 安全获取个人信息
        personal = resume_data.get('personal', {})
        if isinstance(personal, str):
            personal = {'name': personal}
        
        name = personal.get('name', '')
        email = personal.get('email', '')
        phone = personal.get('phone', '')
        linkedin = personal.get('linkedin', '')
        linkedin_url = personal.get('linkedin_url', f'https://www.linkedin.com/in/{linkedin}' if linkedin else '')
        profile = personal.get('profile', personal.get('summary', ''))
        
        # 渲染教育经历
        def render_education(edu):
            school = edu.get('school', '')
            location = edu.get('location', '')
            degree = edu.get('degree', '')
            period = edu.get('period', '')
            highlights = self._safe_get_list(edu.get('highlights', []))
            highlights_html = ''.join([f'<li>{h}</li>' for h in highlights if h])
            
            return f'''<div class="entry">
                <p class="title-line">
                    <span><strong>{school},</strong> {location}</span>
                    <span><i>{period}</i></span>
                </p>
                <p class="subtitle">{degree}</p>
                {'<ul>' + highlights_html + '</ul>' if highlights_html else ''}
            </div>'''
        
        # 渲染工作经历
        def render_experience(exp):
            company = exp.get('company', '')
            location = exp.get('location', '')
            position = exp.get('position', '')
            period = exp.get('period', '')
            highlights = self._safe_get_list(exp.get('highlights', []))
            highlights_html = ''.join([f'<li>{h}</li>' for h in highlights if h])
            
            return f'''<div class="entry">
                <p class="title-line">
                    <span><strong>{company},</strong> {location}</span>
                    <span><i>{period}</i></span>
                </p>
                <p class="subtitle">{position}</p>
                {'<ul>' + highlights_html + '</ul>' if highlights_html else ''}
            </div>'''
        
        # 渲染项目经历
        def render_project(proj):
            name = proj.get('name', '')
            category = proj.get('category', proj.get('period', ''))
            description = proj.get('description', '')
            highlights = self._safe_get_list(proj.get('highlights', []))
            github = proj.get('github', '')
            
            # 合并描述和亮点
            all_points = []
            if description:
                all_points.append(description)
            all_points.extend(highlights)
            if github:
                all_points.append(f'<strong>GitHub:</strong> <a href="{github}">{github}</a>')
            
            points_html = ''.join([f'<li>{p}</li>' for p in all_points if p])
            
            return f'''<div class="entry">
                <p class="title-line">
                    <span><strong>{name}</strong></span>
                    <span><i>{category}</i></span>
                </p>
                {'<ul>' + points_html + '</ul>' if points_html else ''}
            </div>'''
        
        # 渲染技能
        skills_data = resume_data.get('skills', {})
        if isinstance(skills_data, list):
            # 旧格式：列表
            skills_html = '<p>' + ', '.join([s for s in skills_data if isinstance(s, str)]) + '</p>'
        elif isinstance(skills_data, dict):
            # 新格式：分类字典
            skills_items = []
            for category, value in skills_data.items():
                if value:
                    skills_items.append(f'<p class="skill-category">{category.title()}:</p><p>{value}</p>')
            skills_html = '<div class="skills-grid">' + ''.join(skills_items) + '</div>' if skills_items else ''
        elif isinstance(skills_data, str):
            skills_html = f'<p>{skills_data}</p>'
        else:
            skills_html = ''
        
        # 联系信息行
        contact_parts = []
        if phone:
            contact_parts.append(phone)
        if email:
            contact_parts.append(email)
        if linkedin:
            contact_parts.append(f'<a href="{linkedin_url}">{linkedin}</a>')
        contact_line = ' │ '.join(contact_parts)
        
        # Style knobs (fit engine)
        font_size_pt = float(style.get('font_size_pt', 9.5))
        line_height = float(style.get('line_height', 1.35))
        padding_cm = float(style.get('padding_cm', 1.0))
        section_gap_px = float(style.get('section_gap_px', 8))

        # Template defaults
        if template == 'compact':
            font_size_pt = float(style.get('font_size_pt', 9.0))
            line_height = float(style.get('line_height', 1.25))
            padding_cm = float(style.get('padding_cm', 0.85))
            section_gap_px = float(style.get('section_gap_px', 6))

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}的简历</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
    <style>
        /* 页面和字体基础设置 - 专业A4简历 */
        body {{
            font-family: 'Lato', 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;
            font-size: {font_size_pt}pt;
            line-height: {line_height};
            background-color: #ffffff;
            color: #1a1a1a;
            margin: 0;
            padding: 0;
        }}
        p {{ margin: 0; }}
        .resume-container {{
            width: 100%;
            max-width: 210mm;
            min-height: 297mm;
            padding: {padding_cm}cm;
            margin: 0 auto;
            background-color: #ffffff;
            box-sizing: border-box;
        }}

        /* 顶部姓名和联系信息 */
        .header {{
            text-align: center;
            margin-bottom: {section_gap_px}px;
        }}
        .header h1 {{
            font-size: 24pt;
            font-weight: 700;
            margin: 0;
            padding: 0;
            letter-spacing: 1px;
        }}
        .header p {{
            font-size: 9.5pt;
            margin: 4px 0 0 0;
            padding: 0;
        }}
        
        /* 各个部分的标题 */
        h2 {{
            font-size: 11pt;
            font-weight: 700;
            margin: 12px 0 6px 0;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            border-bottom: 0.75px solid #333;
            padding-bottom: 3px;
        }}

        /* 经历条目容器 */
        .entry {{
            margin-bottom: 10px;
        }}

        .title-line {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 700;
            font-size: 10pt;
            margin: 0;
            gap: 6px;
            flex-wrap: wrap;
        }}
        .title-line span:last-child {{
           font-weight: normal;
           font-style: italic;
        }}

        .subtitle {{
            font-style: italic;
            margin: 1px 0 4px 0;
        }}

        ul {{
            padding-left: 1.5em;
            margin: 0;
        }}
        li {{
            margin-bottom: 3px;
            text-align: left; 
        }}
        
        /* 技能区网格布局 */
        .skills-grid {{
            display: grid;
            grid-template-columns: max-content 1fr;
            gap: 0 8px;
            align-items: start;
        }}
        .skills-grid p {{ margin: 0; padding: 0; }}
        .skill-category {{ font-weight: 700; }}
        a {{ color: #0b57d0; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}

        @media print {{
            @page {{ size: A4; margin: 0; }}
            body {{ margin: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            .resume-container {{ width: 210mm; min-height: 297mm; padding: 6mm 8mm; display: flex; flex-direction: column; }}
            .content {{ flex: 1; display: flex; flex-direction: column; justify-content: space-between; }}
            h2 {{ margin: 10px 0 5px 0; }}
            .entry {{ break-inside: avoid; page-break-inside: avoid; margin-bottom: {section_gap_px}px; }}
        }}
    </style>
</head>
<body>
    <div class="resume-container">
        <div class="content">
        <div class="header">
            <h1>{name}</h1>
            <p>{contact_line}</p>
        </div>
        
        {f'<h2>PROFILE</h2><p style="margin-bottom: 10px;">{profile}</p>' if profile else ''}
        
        <h2>EDUCATION</h2>
        {self._safe_render_list(resume_data.get('education', []), render_education)}
        
        <h2>PROFESSIONAL EXPERIENCE</h2>
        {self._safe_render_list(resume_data.get('experience', []), render_experience)}
        
        <h2>PROJECTS</h2>
        {self._safe_render_list(resume_data.get('projects', []), render_project)}
        
        <h2>SKILLS</h2>
        {skills_html}
        
        </div>
    </div>
</body>
</html>'''
        return html
    
    def export_html(self, filename: str = "resume.html"):
        """导出HTML文件"""
        html = self.generate_html()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        return filename
    
    def export_pdf(self, filename: str = "resume.pdf", *, target_pages: int = 1, template: str = 'modern'):
        """导出PDF文件（需要安装playwright）。

        Phase 2: Smart PDF (fit engine)
        - target_pages: 1 or 2
        - template: 'modern' | 'compact'

        Returns:
          { "filename": str, "meta": { target_pages, template, pages, trimmed, style, trim } }

        Strategy:
        1) Try CSS shrink (font-size/line-height/padding/spacing)
        2) If still too long, trim content (reduce experiences + bullets)
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("请安装playwright: pip install playwright && playwright install chromium")
            return None

        try:
            from pypdf import PdfReader
        except Exception:
            PdfReader = None

        import tempfile
        import copy

        target_pages = int(target_pages) if target_pages else 1
        if target_pages not in (1, 2):
            target_pages = 1

        def count_pages(path: str) -> int:
            if PdfReader is None:
                # If we can't count pages, just export once (no fit loop).
                return 999
            try:
                reader = PdfReader(path)
                return len(reader.pages)
            except Exception:
                return 999

        # Fit attempts (CSS knobs)
        style_steps = [
            # baseline
            {},
            {'font_size_pt': 9.3, 'line_height': 1.32, 'padding_cm': 0.95, 'section_gap_px': 7},
            {'font_size_pt': 9.1, 'line_height': 1.28, 'padding_cm': 0.9, 'section_gap_px': 6},
            {'font_size_pt': 8.9, 'line_height': 1.24, 'padding_cm': 0.85, 'section_gap_px': 5},
            {'font_size_pt': 8.7, 'line_height': 1.20, 'padding_cm': 0.8, 'section_gap_px': 4},
        ]

        # Content trim steps (only applied after CSS steps fail)
        trim_steps = [
            None,
            {'max_experiences': 3, 'max_bullets': 4},
            {'max_experiences': 2, 'max_bullets': 3},
            {'max_experiences': 2, 'max_bullets': 2},
        ]

        def apply_trim(data: dict, trim):
            if not trim:
                return data
            d = copy.deepcopy(data)
            max_exps = trim.get('max_experiences')
            max_bullets = trim.get('max_bullets')
            if isinstance(d.get('experience'), list) and max_exps:
                d['experience'] = [e for e in d['experience'] if isinstance(e, dict)][:max_exps]
                if max_bullets:
                    for e in d['experience']:
                        if isinstance(e.get('highlights'), list):
                            e['highlights'] = [h for h in e['highlights'] if h][:max_bullets]
            if isinstance(d.get('projects'), list) and max_bullets:
                # Also trim project bullets a bit
                for p in d['projects']:
                    if isinstance(p, dict) and isinstance(p.get('highlights'), list):
                        p['highlights'] = [h for h in p['highlights'] if h][:max_bullets]
            return d

        # Render + fit loop
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page()

                best_pdf = None
                best_pages = 999
                best_meta = {"pages": 999, "trimmed": False, "style": {}, "trim": None}

                for trim in trim_steps:
                    for style in style_steps:
                        data_override = apply_trim(self.resume_data, trim)
                        html = self.generate_html(template=template, style=style, data=data_override)

                        with tempfile.TemporaryDirectory() as td:
                            html_path = os.path.join(td, 'resume.html')
                            pdf_path = os.path.join(td, 'resume.pdf')
                            with open(html_path, 'w', encoding='utf-8') as f:
                                f.write(html)

                            page.goto(f"file://{os.path.abspath(html_path)}")
                            page.pdf(path=pdf_path, format='A4', print_background=True)

                            pages = count_pages(pdf_path)
                            trimmed = bool(trim)

                            if pages < best_pages:
                                best_pages = pages
                                with open(pdf_path, 'rb') as rf:
                                    best_pdf = rf.read()
                                best_meta = {"pages": pages, "trimmed": trimmed, "style": style, "trim": trim}

                            if pages <= target_pages:
                                with open(filename, 'wb') as out:
                                    out.write(best_pdf)
                                return {"filename": filename, "meta": {"target_pages": target_pages, "template": template, **best_meta}}

                # If we never reached target, still output best attempt.
                if best_pdf is not None:
                    with open(filename, 'wb') as out:
                        out.write(best_pdf)
                    return {"filename": filename, "meta": {"target_pages": target_pages, "template": template, **best_meta}}

                # Fallback (shouldn't happen)
                html_file = self.export_html("temp_resume.html")
                page.goto(f"file://{os.path.abspath(html_file)}")
                page.pdf(path=filename, format="A4", print_background=True)
                os.remove(html_file)
                return {"filename": filename, "meta": {"target_pages": target_pages, "template": template, "pages": 999, "trimmed": False, "style": {}, "trim": None}}
            finally:
                browser.close()


def main():
    """交互式命令行界面"""
    print("=== AI简历更新助手 ===\n")
    
    # 配置API
    api_key = input("请输入Claude API Key: ").strip()
    base_url = input("API Base URL (默认官方): ").strip() or "https://api.anthropic.com"
    model = input("模型名称 (默认claude-sonnet-4-5-20250929): ").strip() or "claude-sonnet-4-5-20250929"
    
    builder = ResumeBuilder(api_key, base_url, model)
    
    while True:
        print("\n可用操作：")
        print("1. 更新个人信息")
        print("2. 添加/更新教育经历")
        print("3. 添加/更新工作经历")
        print("4. 添加/更新项目经历")
        print("5. 更新技能")
        print("6. 导出HTML")
        print("7. 导出PDF")
        print("8. 查看当前简历")
        print("0. 退出")
        
        choice = input("\n请选择操作: ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            content = input("请输入个人信息更新内容: ")
            builder.update_section("personal", content)
            print("✅ 已更新")
        elif choice == "2":
            content = input("请输入教育经历（如：2020-2024 清华大学 计算机科学 本科）: ")
            builder.update_section("education", content)
            print("✅ 已更新")
        elif choice == "3":
            content = input("请输入工作经历: ")
            builder.update_section("experience", content)
            print("✅ 已更新")
        elif choice == "4":
            content = input("请输入项目经历: ")
            builder.update_section("projects", content)
            print("✅ 已更新")
        elif choice == "5":
            content = input("请输入技能（逗号分隔）: ")
            builder.update_section("skills", content)
            print("✅ 已更新")
        elif choice == "6":
            filename = builder.export_html()
            print(f"✅ HTML已导出: {filename}")
        elif choice == "7":
            filename = builder.export_pdf()
            if filename:
                print(f"✅ PDF已导出: {filename}")
        elif choice == "8":
            print(json.dumps(builder.resume_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
