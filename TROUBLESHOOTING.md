# 故障排查指南

## 常见问题

### 1. 端口被占用
**错误**: `Address already in use: 5000`

**原因**: macOS Monterey+ 的 AirPlay Receiver 占用 5000 端口

**解决**: 项目已改用 5001 端口，无需额外操作

---

### 2. Playwright 报错
**错误**: `playwright._impl._errors.Error: Executable doesn't exist`

**解决**:
```bash
playwright install chromium
```

---

### 3. API Key 无效
**错误**: `AuthenticationError` 或 `Invalid API Key`

**检查**:
1. 确认 `.env` 文件存在
2. 确认 `CLAUDE_API_KEY` 格式正确（以 `sk-ant-` 开头）
3. 确认 API Key 未过期

---

### 4. 模块未找到
**错误**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```bash
pip install -r requirements.txt
```

---

### 5. 日志查看
日志文件位置: `app.log`

查看最新日志:
```bash
tail -f app.log
```

---

## 环境检查

启动时会自动检查:
- ✅ anthropic 依赖
- ✅ playwright 依赖
- ✅ CLAUDE_API_KEY 环境变量

如果看到警告，按提示操作即可。

---

## 获取帮助

1. 查看 `app.log` 日志
2. 运行 `python test_quick.py` 测试
3. 提交 GitHub Issue
