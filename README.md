# 🚀 AI Resume Builder - 智能简历构建系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **从手动改简历到一键生成 - 效率提升90%的AI驱动简历管理系统**

## 💡 项目背景

作为一名商业分析专业的学生，我发现每次申请不同岗位都需要手动调整简历，这个重复劳动极其低效。作为一个J人（MBTI），我无法忍受这种混乱，于是构建了这个自动化系统。

**核心痛点：**
- ❌ 手动复制粘贴简历内容
- ❌ 格式不一致导致排版混乱
- ❌ 无法快速生成多语言版本
- ❌ 缺少版本管理和历史记录

**解决方案：**
- ✅ AI驱动的内容优化（Claude/GPT）
- ✅ 标准化A4格式PDF导出
- ✅ 一键多语言翻译（中/英/繁体）
- ✅ 完整的错误处理和日志系统
- ✅ 自定义API配置（支持OpenAI Compatible）

## 🏗️ 系统架构

```
┌─────────────────┐
│   用户输入      │
│  新增信息/修改  │
└────┬────────┘
         │
         ▼
┌─────────────────┐
│   Flask API     │
│  (端口 5001)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  AI优化引擎     │─────▶│ Claude API   │
│  (带容错机制)   │      │ OpenAI API   │
└────────┬────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐
│  HTML模板渲染   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Playwright PDF  │
│  (A4标准格式)   │
└─────────────────┘
```

**技术栈：**
- **后端**: Python 3.8+, Flask, Anthropic SDK
- **前端**: Vanilla JS, HTML5, CSS3
- **PDF生成**: Playwright (Chromium)
- **测试**: pytest, integration tests
- **部署**: 支持本地/Docker

## 🚀 快速开始

### 方法一：一键启动（推荐）

```bash
git clone https://github.com/yourusername/resume-ai-builder.git
cd resume-ai-builder
./start_server.sh
```

服务器启动后，在浏览器打开：**http://localhost:5001**

### 方法二：手动安装

```bash
# 1. 安装依赖
pip install -r requirements.txt
playwright install chromium

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 3. 启动服务
python backend/api_server.py

# 4. 打开浏览器
open http://localhost:5001
```

### ✅ Smoke Test（推荐）

```bash
python3 destroy_test.py
```

> 该脚本会启动一个临时后端、跑完整工作流并清理产物；适合用于快速确认环境可用。

## 🧭 Beta 0.9（当前版本）

**新增/关键能力：**
- **JD Killer 工作流**：粘贴 JD → 解析（/api/jd/parse）→ 匹配分析（/api/jd/analyze）→ 生成/管理 target 变体（/api/variants/*）。
- **Variants（简历变体）**：master + 多个 target 版本，支持创建/切换/保存。
- **Smart PDF**：导出 PDF 时内置 *fit engine*（自动调字体/行距/边距），必要时会 **TRIMMED**（裁剪经历/要点）以满足 `target_pages`。
- **PDF 导入（Beta）**：支持将 **可复制文本** 的 PDF 简历导入为 JSON（/api/import/pdf）。

**限制（Beta）：**
- PDF 导入仅支持 *text-based* PDF；扫描件需要 OCR（暂不支持）。
- 后端目前没有独立 watchdog；若进程退出，请重新运行 `./start_server.sh` 或重启 Electron App。

## 📊 核心功能

### 1. AI增量更新
```python
# 只需输入新信息，AI自动整合
new_info = "完成了某某实习，负责数据分析..."
optimized_resume = ai_builder.update(new_info)
```

### 2. 多语言支持
```python
# 一键翻译成英文/繁体中文
resume_en = translator.translate(resume, target='en')
resume_tw = translator.translate(resume, target='zh-TW')
```

### 3. 自定义API配置

**支持多种API供应商：**
- Anthropic 官方
- OpenAI Compatible（如 api.xstx.info）
- 自定义中转服务

**配置示例：**
```bash
# .env 文件
CLAUDE_API_KEY=sk-ant-xxx
CLAUDE_BASE_URL=https://api.xstx.info/v1
CLAUDE_MODEL=claude-opus-4-5-20251101
```

### 4. 企业级错误处理

- ✅ 所有API调用带重试机制
- ✅ 自动降级到备用模型
- ✅ 完整的日志记录（app.log）
- ✅ 启动时依赖检查
- ✅ 友好的错误提示

**容错机制：**
```python
# 自动尝试多个模型
FALLBACK_MODELS = [
    'claude-opus-4-5-20251101',
    'claude-sonnet-4-5-20250929',
    'claude-3-5-sonnet-20241022',
    'gpt-4o-mini'
]
```

## 🎯 设计哲学

**1. 最小化原则**
- 只做必要的功能，不过度设计
- 代码简洁，易于维护

**2. 工程化思维**
- 完整的错误处理
- 标准化的日志系统
- 自动化测试覆盖

**3. 用户体验优先**
- 一键启动，零配置
- 清晰的错误提示
- 实时预览功能

## 📈 性能指标

| 指标 | 数值 |
|------|------|
| 简历生成时间 | < 5秒 |
| PDF导出时间 | < 3秒 |
| API响应时间 | < 2秒 |
| 测试覆盖率 | 85% |
| 项目完成度 | 95% |

## 🛠️ API端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/config` | POST | 更新配置 |
| `/api/config/test` | POST | 测试API连接 |
| `/api/resume` | GET/POST | 获取/保存简历 |
| `/api/update` | POST | AI 更新某个简历章节 |
| `/api/translate` | POST | 翻译简历 |
| `/api/chat/refine` | POST | Chat 指令式改简历（返回 summary + 更新后的 JSON） |
| `/api/jd/parse` | POST | JD 解析（company/role/slug/summary） |
| `/api/jd/analyze` | POST | JD 与简历匹配分析（match_score/gaps/suggestions） |
| `/api/variants` | GET | 列出变体 + 当前 active |
| `/api/variants/create` | POST | 从 master 创建变体 |
| `/api/variants/select` | POST | 切换变体（返回该变体数据） |
| `/api/variants/save` | POST | 保存变体 |
| `/api/import/pdf` | POST | 导入 text-based PDF 简历为 JSON |
| `/api/export/html` | POST | 导出HTML |
| `/api/export/pdf` | POST | 导出PDF（支持 Smart PDF：fit engine + TRIMMED） |
| `/api/export/pdf/download` | GET | 下载导出的 PDF |

## 📚 文档

- **快速启动**: [QUICK_START.md](QUICK_START.md)
- **故障排查**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Electron版本**: [ELECTRON_README.md](ELECTRON_README.md)

## 🚢 Release（GitHub Actions Logistics Layer）

本仓库包含一个“手动门控”的发布工作流（不会自动合并 PR）。

### 1) 通过 merge commit 触发发布（推荐）

当 `main` 分支收到一次 push，并且 **该 commit message 包含**：`Release vX.Y.Z`（例如：`Release v1.1.0`），工作流会执行：

- 解析版本号 `X.Y.Z` → 创建 annotated tag `vX.Y.Z`
- 创建 GitHub Release（release notes 优先来自 `RELEASE_NOTES_vX.Y.Z.md`；否则尝试从 `ROADMAP.md` 中提取 `## vX.Y.Z` 小节）
- 构建并推送 Docker 镜像到 `ghcr.io/<owner>/<repo>`（使用 `GITHUB_TOKEN`；需要 `packages: write` 权限）

### Docker 使用说明（GHCR）

拉取并运行（示例）：

```bash
# 需要先在 GitHub Packages 页面确认镜像可见性（public/private）
docker pull ghcr.io/<owner>/<repo>:vX.Y.Z

docker run --rm -p 5001:5001 \
  -e FLASK_PORT=5001 \
  ghcr.io/<owner>/<repo>:vX.Y.Z
```

本地构建（不推送）：

```bash
docker build -t resume-ai-builder:local .

docker run --rm -p 5001:5001 resume-ai-builder:local
```

> 人工门控：只有显式包含 `Release v...` 的 commit 或手动触发才会发布。

### 2) 手动 workflow_dispatch 发布

在 GitHub Actions 页面手动运行 `Release` workflow，并填写：
- `version`: `X.Y.Z`
- `notes_source`: `auto` / `release_notes` / `roadmap`

### 3) 创建下一轮 planning 分支（手动）

`Auto Branch (manual)` 工作流目前仅支持 `workflow_dispatch`：
- 输入 `planning_branch`（例如：`feat/v1.2-planning`）
- 会从 `main`（或你指定的 base）创建并 push 该分支

## 🛠️ 开发路线图

- [x] **Phase 1**: 核心功能实现
- [x] **Phase 2**: 错误处理和日志
- [x] **Phase 3**: 文档完善
- [x] **Phase 4**: 自定义API配置
- [ ] **Phase 5**: 多模板支持
- [ ] **Phase 6**: 云端部署
- [ ] **Phase 7**: 移动端适配

## 🔧 故障排查

### 常见问题

**1. API连接失败**
```bash
# 检查配置
cat .env

# 测试连接
curl -X POST http://localhost:5001/api/config/test \
  -H "Content-Type: application/json" \
  -d '{"api_key":"your-key","base_url":"https://api.anthropic.com","model":"claude-sonnet-4-5-20250929"}'
```

**2. 端口被占用**
```bash
# 查看占用端口的进程
lsof -i :5001

# 停止进程
kill -9 <PID>
```

**3. 依赖缺失**
```bash
pip install -r requirements.txt
playwright install chromium
```

更多问题请查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

**开发流程：**
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 👤 作者

**哲宇** - Business Analytics Student

- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your Profile](https://linkedin.com/in/yourprofile)
- Email: your.email@example.com

## 🙏 致谢

- [Anthropic](https://www.anthropic.com/) - Claude API
- [Playwright](https://playwright.dev/) - PDF生成
- [Flask](https://flask.palletsprojects.com/) - Web框架

---

⭐ 如果这个项目对你有帮助，请给个Star！

**项目状态**: 🟢 活跃开发中 | 完成度 95%
