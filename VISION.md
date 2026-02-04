# VISION.md — Resume AI Builder Constitution (不可修改的神谕)

## North Star
打造**全球最快、最稳、最可控**的「本地优先（local-first）」简历生成/投递优化系统：
- 数据层可追溯、可回滚、多版本（master + targets）
- 智能建议可控（preview → apply），不“乱改”
- PDF 输出可靠（1/2 页可拟合），可解释（TRIMMED 必须标记）

## Core Principles (必须遵守)
1) **Local-first**：默认离线/本地存储；不把用户全量资产外发。
2) **Minimalism**：能用 50 行解决就别上 500 行；避免过度抽象。
3) **No dependency creep**：新增依赖必须有清晰收益；优先轻量工具（ruff > pylint，zustand > redux）。
4) **Safety by design**：所有写入都要有显式触发（Apply/Save）；支持回滚；导出有告警。
5) **Observability**：关键路径必须有冒烟测试（smoke test）和可重复验证。
6) **No feature monster**：禁止把它变成“聊天+天气+社交”大杂烩。

## What we optimize for
- 投递成功率（JD 对齐）
- 交付稳定性（导出不崩、不过页）
- 速度（从 JD → target → 改写 → 导出）

## Hard No (明确禁止)
- 引入重型前端状态/数据框架（Redux/GraphQL 等）除非证明必要
- 引入登录/社交/时间线等与简历核心无关的系统
- 自动改写并静默覆盖用户数据（必须 preview/apply）

## Current Baseline
- JD Killer: JD → parse/analyze → create variant → onboarding message → controlled refine/apply
- Smart PDF: fit engine (css shrink + optional trim with TRIMMED marking)
- Ops: watchdog + config snapshot + launchd

## Near-term Targets (V1.1–V1.2)
- 更智能的 Trim（基于 JD relevance，而不是顺序裁剪）
- Export Cockpit 更完善（Auto/1/2 页、模板选择、导出历史）
- 增加“投递证据链”（每个 target 保存 jd_parse/jd_analysis + 导出 meta）

