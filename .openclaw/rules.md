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
