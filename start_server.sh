#!/bin/bash

# Resume AI Builder 启动脚本
# 使用方法：./start_server.sh

cd "$(dirname "$0")"

echo "🚀 启动 Resume AI Builder 服务器..."
echo "📍 工作目录: $(pwd)"
echo ""

# 检查依赖
if ! python3 -c "import flask" 2>/dev/null; then
    echo "❌ 缺少依赖，正在安装..."
    pip3 install -r requirements.txt
fi

# 检查环境变量
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件"
    echo "📝 请复制 .env.example 并填入你的 API Key："
    echo "   cp .env.example .env"
    echo "   然后编辑 .env 文件"
    echo ""
fi

# 启动服务器
echo "🌐 启动服务器在 http://localhost:5001"
echo "📋 日志输出到 app.log"
echo "⏹️  按 Ctrl+C 停止服务器"
echo ""

python3 backend/api_server.py
