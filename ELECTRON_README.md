# AI简历更新助手 - Electron桌面版

## 🚀 快速开始

### 1. 安装依赖

**后端依赖（Python）：**
```bash
cd /Users/zheyuliu/Documents/GitHub/resume-ai-builder
pip install -r requirements.txt
playwright install chromium
```

**前端依赖（Node.js）：**
```bash
cd frontend
npm install
```

### 2. 启动应用

**方式1：一键启动（推荐）**
```bash
cd frontend
npm start
```

这会自动启动Python后端和Electron前端。

**方式2：分别启动**

终端1 - 启动后端：
```bash
cd backend
python3 api_server.py
```

终端2 - 启动前端：
```bash
cd frontend
npm start
```

### 3. 使用应用

1. **配置API**：首次使用需要在"API配置"页面输入Claude API Key
2. **编辑简历**：在"编辑简历"页面输入新信息，AI自动优化
3. **预览**：实时查看简历效果
4. **多语言翻译**：一键翻译成中文/英文
5. **导出PDF**：生成A4格式PDF文件

---

## 📁 项目结构

```
resume-ai-builder/
├── backend/
│   └── api_server.py       # Flask API服务
├── frontend/
│   ├── main.js            # Electron主进程
│   ├── index.html         # 前端界面
│   ├── app.js             # 前端逻辑
│   └── package.json       # 前端依赖
├── app.py                 # 核心简历构建逻辑
└── requirements.txt       # Python依赖
```

---

## 🎨 功能特性

### ✅ 已实现
- ✅ Electron桌面应用
- ✅ Flask RESTful API
- ✅ AI增量更新简历
- ✅ 实时预览
- ✅ 多语言翻译（中文/英文）
- ✅ PDF导出
- ✅ 美观的现代化UI
- ✅ 自动启动后端服务

### 🔄 待优化
- [ ] 多模板支持
- [ ] 版本历史
- [ ] 深色模式
- [ ] 应用打包（dmg/exe）
- [ ] 自动更新功能

---

## 🛠️ 开发模式

启动开发模式（带DevTools）：
```bash
cd frontend
npm run dev
```

---

## 📦 打包应用

安装electron-builder：
```bash
npm install --save-dev electron-builder
```

添加到package.json：
```json
{
  "scripts": {
    "build": "electron-builder"
  },
  "build": {
    "appId": "com.yourname.resume-builder",
    "productName": "AI简历助手",
    "mac": {
      "target": ["dmg"]
    },
    "win": {
      "target": ["nsis"]
    }
  }
}
```

打包：
```bash
npm run build
```

---

## 🐛 常见问题

### Q: 启动后显示"后端服务未启动"
A: 等待2-3秒让Python后端完全启动，或手动先启动backend/api_server.py

### Q: PDF导出失败
A: 确保已安装playwright：`playwright install chromium`

### Q: API调用失败
A: 检查API Key是否正确，网络是否正常

---

## 🌟 与CLI版本对比

| 特性 | CLI版本 | Electron版本 |
|------|---------|--------------|
| 界面 | 命令行 | 图形界面 ✅ |
| 实时预览 | ❌ | ✅ |
| 易用性 | 中 | 高 ✅ |
| 打包分发 | ❌ | ✅ |
| 开发速度 | 快 | 中 |

---

## 📝 API接口文档

### POST /api/config
设置API配置
```json
{
  "api_key": "sk-ant-...",
  "base_url": "https://api.anthropic.com",
  "model": "claude-sonnet-4-5-20250929"
}
```

### GET /api/resume
获取当前简历数据

### POST /api/update
AI更新简历部分
```json
{
  "section": "experience",
  "content": "2024年7月-12月在字节跳动..."
}
```

### POST /api/translate
翻译简历
```json
{
  "target_lang": "en-US"
}
```

### POST /api/export/pdf
导出PDF
```json
{
  "resume_data": {...},
  "filename": "resume.pdf"
}
```

---

## 💡 技术栈

- **后端**：Python + Flask + Anthropic API
- **前端**：Electron + Vanilla JavaScript
- **样式**：原生CSS（无框架依赖）
- **通信**：RESTful API

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License
