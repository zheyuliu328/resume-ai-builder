#!/usr/bin/env python3
"""
测试新的API配置：https://www.ai678.top/v1
"""
import anthropic

def test_api():
    print("=" * 60)
    print("🧪 测试 ai678.top API")
    print("=" * 60)
    
    # 你需要提供真实的API Key
    api_key = input("\n请输入你的API Key: ").strip()
    
    if not api_key or api_key == "sk-ant-xxx":
        print("❌ 请提供有效的API Key")
        return
    
    base_url = "https://www.ai678.top"  # 不带/v1，代码会自动添加
    model = "claude-sonnet-4-5-20250929"
    
    print(f"\n📝 配置信息:")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    print(f"   API Key: {api_key[:15]}...{api_key[-4:]}")
    
    try:
        print("\n🤖 创建客户端...")
        client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        
        print("📤 发送测试请求...")
        message = client.messages.create(
            model=model,
            max_tokens=50,
            messages=[{"role": "user", "content": "请用一句话介绍你自己"}]
        )
        
        print("\n✅ API连接成功！")
        print(f"\n🤖 AI回复: {message.content[0].text}")
        
        print("\n" + "=" * 60)
        print("✅ 测试通过！可以使用此配置")
        print("=" * 60)
        
        # 提示如何更新.env
        print("\n📝 请更新 .env 文件:")
        print(f"CLAUDE_API_KEY={api_key}")
        print(f"CLAUDE_BASE_URL={base_url}")
        print(f"CLAUDE_MODEL={model}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ API连接失败: {str(e)}")
        
        error_str = str(e)
        if '401' in error_str:
            print("\n💡 API Key无效，请检查:")
            print(f"   1. 访问 https://www.ai678.top/sk.html 查询余额")
            print("   2. 确认API Key是否正确")
        elif '403' in error_str:
            print("\n💡 无权访问，可能原因:")
            print("   1. 账户余额不足")
            print("   2. 模型不可用")
        elif 'timeout' in error_str.lower():
            print("\n💡 请求超时，可能原因:")
            print("   1. 网络连接问题")
            print("   2. 服务器响应慢")
        else:
            print(f"\n💡 其他错误，请检查配置")
        
        return False

if __name__ == '__main__':
    test_api()
