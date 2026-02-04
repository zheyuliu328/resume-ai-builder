# 🚀 快速启动指南

## 方法一：使用启动脚本（推荐）

```bash
cd GitHub/resume-ai-builder
./start_server.sh
```

服务器启动后，在浏览器打开：**http://localhost:5001**

---

## 方法二：手动启动

### 1️⃣ 配置环境变量

```bash
cd GitHub/resume-ai-builder

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的配置
nano .env  # 或使用其他编辑器
```

**`.env` 文件示例：**
```bash
# API 配置
CLAUDE_API_KEY=sk-ant-xxx  # 你的 API Key
CLAUDE_BASE_URL=https://api.anthropic.com  # 或自定义域名
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# 服务器配置
FLASK_PORT=5001
LOG_LEVEL=INFO
```

### 2️⃣ 安装依赖（首次运行）

```bash
pip3 install -r requirements.txt
playwright install chromium
```

### 3️⃣ 启动服务器

```bash
python3 backend/api_server.py
```

### 4️⃣ 打开浏览器

访问：**http://localhost:5001**

---

## 🎯 新功能：自定义 API 配置

现在支持在 UI 界面配置自定义 API！

### 配置示例（OpenAI Compatible）

1. 打开配置页面
2. 选择 **API 供应商**：`OpenAI Compatible`
3. 填写配置：
   - **基础 URL**：`https://api.xstx.info/v1`
   - **API Key**：你的 key 令牌
   - **模型 ID**：`claude-opus-4-5-20251101`
   - **API 路径**：留空（可选）

4. 点击 **测试连接** 验证配置
5. 点击 **保存配置**

### 配置示例（Anthropic 官方）

1. 选择 **API 供应商**：`Anthropic`
2. 填写配置：
   - **基础 URL**：`https://api.anthropic.com`
   - **API Key**：`sk-ant-xxx`
   - **模型 ID**：`claude-sonnet-4-5-20250929`

---

## 📋 测试功能

### 运行集成测试

```bash
cd GitHub/resume-ai-builder
python3 test_quick.py
```

**预期输出：**
```
✅ 健康检查通过
✅ API配置更新成功
✅ 简历数据获取正常
```

---

## 🛠️ 故障排查

### 问题 1：端口被占用

```bash
# 查看占用端口的进程
lsof -i :5001

# 停止进程
kill -9 <PID>
```

### 问题 2：依赖缺失

```bash
pip3 install -r requirements.txt
playwright install chromium
```

### 问题 3：API 连接失败

1. 检查 `.env` 文件中的 API Key 是否正确
2. 检查网络连接
3. 查看日志：`tail -f app.log`

---

## 📚 更多文档

- **完整文档**：[README.md](README.md)
- **故障排查**：[TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Electron 版本**：[ELECTRON_README.md](ELECTRON_README.md)

---

## 💡 使用提示

1. **首次使用**：建议先在配置页面测试 API 连接
2. **日志查看**：实时日志在 `app.log` 文件中
3. **停止服务器**：按 `Ctrl+C`
4. **多语言支持**：即将推出中英文翻译功能

---

**项目完成度：95%** ✅

核心功能已完成，可以开始使用！
