# OpenClaw Agent Rules (Project SOP)

## Self-Correction Protocol (第一修正案)

禁止“盲交”代码。

在你宣称任务完成（Task Completed）或提交代码（Git Commit）之前，必须完成以下步骤：

1) **环境感知**
   - 运行并记录：`python3 --version` / `node --version` / 相关依赖版本
   - 不要假设用户使用最新版（例如 Python 3.9 vs 3.10+）

2) **冒烟测试（Smoke Test）**
   - 针对本次改动，至少运行一次最关键的启动命令，例如：
     - `python3 backend/api_server.py`
     - `node -c frontend/app.js`
     - `python3 -m py_compile <files>`

3) **自主修复**
   - 如果 stderr 出现报错：**不要问用户**，先根据报错信息自行修复并再次冒烟测试

4) **完成条件**
   - 只有在“启动成功无报错”或遇到无法解决的环境限制时，才允许对外汇报。

---

## PROTOCOL: The Trinity Commit Protocol (三位一体提交协议)

**CRITICAL:** Before any Git Commit or Task Completion signal, you MUST pass these three gates.
Failure to do so will result in task rejection.

### Gate 1: Pre-Flight Check (变更前自检)
- **Environment Scan:** DO NOT assume. Run `python3 --version` or `node --version` to confirm constraints.
- **Scope Definition:** Explicitly state the *Goal* (What) and *Impact* (Where).
- **Non-Destructive Intent:** Confirm the planned change respects **Local-First** and does not delete user data without backup mechanisms (e.g., snapshots).

### Gate 2: In-Flight Verification (变更后自验)
- **Smoke Test:** You MUST run a verification command relative to your change.
  - Backend change? Run `python3 -m py_compile ...` or `python3 destroy_test.py`.
  - Frontend change? Run `node -c ...` or a build/lint check.
- **Self-Correction Loop:** If the test fails (stderr), you must FIX it immediately. DO NOT report failure until you have exhausted self-repair attempts.
- **Evidence:** In your final report, include the command you ran and the success output.

### Gate 3: Governance Audit (自我审计)
- **Constitution Check:** Does this change violate `VISION.md`? (e.g., Feature Creep, dependency creep).
- **ADR Compliance:** Does this change contradict any record in `docs/adr/`? (e.g., introducing SQLite violates ADR-0001).
- **Commit Message Standard:**
  - Format: `type(scope): subject`
  - Body: include **Why**, **Risk Audit**, and **Rollback Plan** if high risk.

**Override Condition:** You are only allowed to bypass Gate 2 (Verification) if the environment is strictly broken beyond your control, in which case you must report the specific error log immediately.
