# 🏰 Project OpenClaw: Master Strategic Plan

**Codename:** The Cybernetic Citadel (赛博堡垒)  
**Commander:** Nero  
**Architecture:** Local-First, Privacy-Centric, Autonomous-Assisted.

---

## 📜 宪法与核心原则 (The Constitution)
在执行任何 Milestone 之前，必须诵读以下铁律：

- **Privacy Prime**：数据永远 Local-first (JSON)，严禁私自上传公网。
- **No Feature Creep**：每一个功能必须服务于“拿到 Offer”这一战略目标。
- **Governance**：所有代码必须通过 Trinity Gate (Pre-flight → Verify → Audit)。
- **SOP**：严禁盲目提交，必须执行 `smoke_verify.sh`。

---

## ✅ Milestone 1: Genesis (V1.0) — The JD Killer
**Status:** Completed  
**Goal:** 建立核心简历生成引擎，消灭“针对性简历难写”的痛点。

### 核心模块
- **Resume Refinery**：基于 JSON 的结构化简历存储（`data/resume_master.json`）。
- **Variant System**：继承机制：Master → Target Variant（只修改差异部分）。
- **PDF Engine**：智能排版，自动压缩两页进一页（`_TRIMMED` 标记）。

### 🕹️ 操作指南 (SOP)
- 初始化：`cp data/resume_example.json data/resume_master.json`
- 创建变体：
  ```bash
  # 针对 Google 创建变体
  curl -X POST /api/variants/create -d '{"base": "master", "name": "target_google"}'
  ```
- 导出 PDF：前端点击 **Export** → 选择 **One Page Mode** → 下载。

---

## ✅ Milestone 2: The Arsenal (V1.1–V1.2) — Safety & Expansion
**Status:** Completed  
**Goal:** 从单一工具升级为“职业军火库”，建立风控体系。

### 核心模块
- **Snapshot Rollback**：每次保存自动生成时间戳快照，提供“后悔药”。
- **Scout (V0)**：JD 抓取与清洗工具（Bookmarklet + Local API）。
- **Diplomat**：求职信生成器（Preview-First, Apply-to-Save）。
- **Portfolio**：静态个人主页生成器（默认脱敏）。

### 🕹️ 操作指南 (SOP)
- 抓取 JD：使用浏览器书签工具点击 JD 页面 → 数据存入 `data/jd_captures/`。
- 生成求职信：在 Diplomat 页面选择 Variant + JD → 生成 → 修改 → 保存。
- 部署主页：
  ```bash
  # 生成静态站（自动脱敏）
  curl /api/portfolio/generate
  # 产物位于 public_html/，可直接 push 到 GitHub Pages
  ```

---

## ✅ Milestone 3: Mission Control (V1.3) — The War Room
**Status:** Completed  
**Goal:** 建立战略闭环，连接情报 (JD) 与武器 (Resume)。

### 核心模块
- **Application Object**：战役对象，绑定 JD + Variant + Status。
- **Gap Engine (V0)**：基于 Stemming（词干提取）的关键词差异分析。
- **The War Room**：双屏作战室 UI：
  - 左屏：JD + Gaps（红色高亮）
  - 右屏：Resume 编辑器
  - 交互：点击 Gap → 自动唤起 Chat 修复 → Recompute（红变绿）

### 🕹️ 操作指南 (SOP)
- 建立战役：Mission 面板点击 **New Application** → 选择已抓取的 JD。
- 消除差距：
  - 进入 War Room
  - 点击左侧红色的 “Kubernetes”
  - Chat 自动建议修改
  - 点击 Apply → 点击 Recompute → 看着它变绿

---

## 🚧 Milestone 4: The Expedition (V1.4) — Automation & Integration
**Status:** In Progress / Autonomous Mode  
**Goal:** 补齐后勤自动化，智能化升级，向浏览器端进军。

### 核心任务清单
- **[Ops] Release Automaton**：GitHub Actions 自动发版、Docker 构建（仅限 Release Tag）。
- **[Ops] Dependency Lock**：`requirements.txt`（pip freeze）+ `npm audit`。
- **[Intel] Gap Engine V1**：引入同义词典（`data/synonyms.json`），识别 Go = Golang。
- **[Intel] Evidence Enforcement**：生成求职信时强制引用简历项目。
- **[Sidecar] Chrome Extension V0**：
  - 插件外壳（Manifest V3）
  - 与本地 `localhost:5001` 通信
  - 在 LinkedIn 页面直接显示 Gap 分析侧边栏

### 🕹️ 操作指南 (预期)
- 发布：在 GitHub 提交 Tag `v1.4.0`，Docker 镜像自动推送到 GHCR。
- 插件使用：安装 Chrome 插件 → 打开 LinkedIn → 点击图标 → 侧边栏弹出当前简历评分。

---

## 🔮 Milestone 5: The Conquest (V1.5+) — The Horizon
**Status:** Planned  
**Goal:** 去浏览器化，全平台制霸。

### 战略规划
- **Desktop Wrapper (Tauri)**：
  - Rust + Tauri 打包后端
  - 效果：双击 `.exe` / `.app` 启动，无需终端敲命令
- **System Tray**：桌面通知（“你有 3 个 Gap 没修”）。
- **Mobile Commander (PWA)**：
  - 手机端适配 UI
  - 场景：地铁上审阅 JD，回家电脑自动同步分析

---

## 🛡️ 每日运维 SOP (The Daily Protocol)
指挥官每日必做：

- **净空启动 (Clean Start)**：
  ```bash
  # 彻底杀死旧进程，防止 405 幻觉
  pkill -f backend/api_server.py
  # 启动新后端
  python3 backend/api_server.py &
  ```

- **冒烟测试 (Smoke Verify)**：
  - 每次修改代码后，必须跑：
    ```bash
    bash tools/smoke_verify.sh
    ```
  - 只有全绿（ALL CHECKS PASSED）才能提交。

- **Git 纪律**：
  - `feat/` 分支开发 → 提交 PR → 人类审批（Gate B）→ Squash Merge → 自动触发 Release（仅限打 Tag）。

---

*End of Document. Commander Nero, this is your legacy.*
