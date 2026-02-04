#!/bin/bash

# Resume AI Builder 一键安装脚本
# 使用方法：./setup.sh

set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║     🚀 AI Resume Builder - 一键安装脚本            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

cd "$(dirname "$0")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Python
echo "📌 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装，请先安装 Python3${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"

# 检查pip
echo ""
echo "📌 检查 pip..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ pip3 已安装${NC}"

# 安装依赖
echo ""
echo "📌 安装 Python 依赖..."
pip3 install -r requirements.txt

# 安装Playwright浏览器
echo ""
echo "📌 安装 Playwright Chromium..."
if python3 -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
    echo "正在安装 Chromium 浏览器..."
    playwright install chromium
    echo -e "${GREEN}✅ Playwright Chromium 已安装${NC}"
else
    echo -e "${YELLOW}⚠️ Playwright 未安装，尝试安装...${NC}"
    pip3 install playwright
    playwright install chromium
fi

# 配置环境变量
echo ""
echo "📌 配置环境变量..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️ 已创建 .env 文件，请编辑填入你的 API Key${NC}"
    echo "   nano .env"
else
    echo -e "${GREEN}✅ .env 文件已存在${NC}"
fi

# 验证安装
echo ""
echo "📌 验证安装..."
python3 -c "
import flask
import anthropic
from playwright.sync_api import sync_playwright
print('所有依赖已正确安装')
" 2>/dev/null && echo -e "${GREEN}✅ 所有依赖验证通过${NC}" || echo -e "${YELLOW}⚠️ 部分依赖可能需要手动检查${NC}"

# 完成
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║              🎉 安装完成！                          ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║                                                      ║"
echo "║  下一步：                                            ║"
echo "║  1. 编辑 .env 文件，填入你的 API Key                ║"
echo "║     nano .env                                        ║"
echo "║                                                      ║"
echo "║  2. 启动服务器                                       ║"
echo "║     ./start_server.sh                                ║"
echo "║                                                      ║"
echo "║  3. 打开浏览器                                       ║"
echo "║     http://localhost:5001                            ║"
echo "║                                                      ║"
echo "╚══════════════════════════════════════════════════════╝"
