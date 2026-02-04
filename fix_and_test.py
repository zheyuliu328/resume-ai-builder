#!/usr/bin/env python3
"""
快速诊断和测试脚本
"""
import os
import sys
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()

def test_api_connection():
    """测试API连接"""
    print("🔍 测试API连接...")
    
    api_key = os.getenv('CLAUDE_API_KEY', '')
    base_url = os.getenv('CLAUDE_BASE_URL', 'https://api.anthropic.com')
    model = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-5-20250929')
    
    if not api_key:
        print("❌ 未设置 CLAUDE_API_KEY")
        return False
    
    print(f"📝 配置信息:")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    print(f"   API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # 修复URL
    if base_url.rstrip('/').endswith('/v1'):
        base_url = base_url.rstrip('/')[:-3]
        print(f"🔧 自动修正 URL: {base_url}")
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        
        print("🤖 发送测试请求...")
        message = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )
        print("✅ API连接成功！")
        return True
    except Exception as e:
        print(f"❌ API连接失败: {str(e)}")
        
        # 提供诊断建议
        error_str = str(e)
        if '401' in error_str or 'authentication' in error_str.lower():
            print("\n💡 建议: API Key 无效")
            print("   1. 检查 .env 文件中的 CLAUDE_API_KEY")
            print("   2. 确认 API Key 是否正确")
        elif '403' in error_str or 'permission' in error_str.lower():
            print("\n💡 建议: 无权访问此模型")
            print("   1. 检查账户是否有权限使用该模型")
            print("   2. 尝试更换模型（如 claude-3-5-sonnet-20241022）")
        elif 'timeout' in error_str.lower() or 'timed out' in error_str.lower():
            print("\n💡 建议: 请求超时")
            print("   1. 检查网络连接")
            print("   2. 尝试使用官方API: https://api.anthropic.com")
            print("   3. 如果使用中转服务，可能服务不稳定")
        else:
            print(f"\n💡 建议: 检查配置或尝试官方API")
        
        return False


def test_flask_server():
    """测试Flask服务器"""
    print("\n🔍 测试Flask服务器...")
    
    try:
        response = requests.get('http://localhost:5001/health', timeout=5)
        if response.status_code == 200:
            print("✅ Flask服务器运行正常")
            return True
        else:
            print(f"⚠️ Flask服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Flask服务器未启动")
        print("\n💡 启动服务器:")
        print("   cd ~/Documents/GitHub/resume-ai-builder")
        print("   python3 backend/api_server.py")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False


def main():
    print("=" * 60)
    print("🚀 简历AI助手 - 诊断工具")
    print("=" * 60)
    
    # 测试1: API连接
    api_ok = test_api_connection()
    
    # 测试2: Flask服务器
    flask_ok = test_flask_server()
    
    print("\n" + "=" * 60)
    print("📊 诊断结果:")
    print("=" * 60)
    print(f"API连接: {'✅ 正常' if api_ok else '❌ 失败'}")
    print(f"Flask服务器: {'✅ 正常' if flask_ok else '❌ 失败'}")
    
    if api_ok and flask_ok:
        print("\n🎉 所有检查通过！可以使用应用了")
        print("\n📱 访问: http://localhost:5001")
    else:
        print("\n⚠️ 存在问题，请根据上述建议修复")
        
        if not api_ok:
            print("\n🔧 快速修复API问题:")
            print("1. 编辑 .env 文件")
            print("2. 设置正确的 CLAUDE_API_KEY")
            print("3. 如果使用中转服务不稳定，改用官方API:")
            print("   CLAUDE_BASE_URL=https://api.anthropic.com")
        
        if not flask_ok:
            print("\n🔧 启动Flask服务器:")
            print("cd ~/Documents/GitHub/resume-ai-builder")
            print("python3 backend/api_server.py")


if __name__ == '__main__':
    main()
