# 🚀 快速配置指南

## 📝 你的API配置信息

根据你提供的信息：

```
连接URL：https://www.ai678.top/v1
模型名称：claude-sonnet-4-5-20250929
余额查询：https://www.ai678.top/sk.html
```

## ⚡ 快速配置步骤

### 1. 测试API连接

```bash
cd ~/Documents/GitHub/resume-ai-builder
python3 test_new_api.py
# 输入你的API Key进行测试
```

### 2. 如果测试成功，更新 .env 文件

```bash
nano .env
```

填入以下内容：

```env
# Claude API 配置
CLAUDE_API_KEY=你的真实API_KEY
CLAUDE_BASE_URL=https://www.ai678.top
CLAUDE_MODEL=claude-sonnet-4-5-20250929

# Flask 配置
FLASK_PORT=5001
LOG_LEVEL=INFO
```

**重要提示：**
- `CLAUDE_BASE_URL` 填写 `https://www.ai678.top`（不带 /v1）
- 代码会自动处理路径问题

### 3. 验证配置

```bash
python3 fix_and_test.py
```

应该看到：
```
✅ API连接成功！
```

### 4. 启动服务器

```bash
python3 backend/api_server.py
```

访问：http://localhost:5001

## 🔍 故障排查

### 如果出现 401 错误
- 检查API Key是否正确
- 访问 https://www.ai678.top/sk.html 查询余额
- 确认账户有足够余额

### 如果出现超时错误
- 检查网络连接
- 尝试多次重试（中转服务可能不稳定）
- 考虑使用官方API作为备选

### 如果模型不可用
- 尝试其他模型：
  - `claude-3-5-sonnet-20241022`
  - `claude-opus-4-5-20251101`

## 📊 下一步

配置成功后，我们可以开始实现你提出的产品升级功能：

1. ✨ 智能简历解析
2. 🎯 交互式编辑
3. 🔄 增量更新

详见：`IMMEDIATE_FIX_GUIDE.md`
