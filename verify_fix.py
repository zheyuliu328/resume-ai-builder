#!/usr/bin/env python3
"""
快速验证脚本 - 确认预览和缩放修复是否生效
执行时间：< 5分钟
"""

import os
import sys
import time
import requests
from pathlib import Path

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_status(status, message):
    if status == "✓":
        print(f"{Colors.GREEN}✓{Colors.END} {message}")
    elif status == "✗":
        print(f"{Colors.RED}✗{Colors.END} {message}")
    elif status == "⚠":
        print(f"{Colors.YELLOW}⚠{Colors.END} {message}")
    else:
        print(f"{Colors.BLUE}ℹ{Colors.END} {message}")

def check_file_paths():
    """检查关键文件路径是否正确锚定"""
    print("\n" + "="*60)
    print("1. 检查文件路径锚定")
    print("="*60)
    
    api_server = Path("backend/api_server.py")
    if not api_server.exists():
        print_status("✗", "backend/api_server.py 不存在")
        return False
    
    content = api_server.read_text()
    
    checks = {
        "ROOT_DIR 定义": "ROOT_DIR = Path(__file__).parent.parent.resolve()" in content,
        ".env 路径": "ROOT_DIR / '.env'" in content or "load_dotenv(ROOT_DIR / '.env')" in content,
        "app.log 路径": "ROOT_DIR / 'app.log'" in content or "logging.FileHandler(ROOT_DIR / 'app.log')" in content,
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        print_status("✓" if passed else "✗", check_name)
        if not passed:
            all_passed = False
    
    return all_passed

def check_electron_config():
    """检查 Electron 启动配置"""
    print("\n" + "="*60)
    print("2. 检查 Electron 配置")
    print("="*60)
    
    main_js = Path("frontend/main.js")
    if not main_js.exists():
        print_status("✗", "frontend/main.js 不存在")
        return False
    
    content = main_js.read_text()
    
    checks = {
        "cwd 设置": "cwd: rootDir" in content,
        "缩放锁定": "setZoomFactor(1)" in content,
        "缩放限制": "setVisualZoomLevelLimits(1, 1)" in content,
        "快捷键拦截": "event.preventDefault()" in content and ("control" in content or "meta" in content),
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        print_status("✓" if passed else "✗", check_name)
        if not passed:
            all_passed = False
    
    return all_passed

def check_frontend_preview():
    """检查前端预览实现"""
    print("\n" + "="*60)
    print("3. 检查前端预览实现")
    print("="*60)
    
    app_js = Path("frontend/app.js")
    if not app_js.exists():
        print_status("✗", "frontend/app.js 不存在")
        return False
    
    content = app_js.read_text()
    
    checks = {
        "iframe.srcdoc 使用": "iframe.srcdoc = result.html" in content or "iframe.srcdoc = data.html" in content,
        "动态高度调整": "iframe.style.height" in content and "scrollHeight" in content,
        "API_BASE 配置": "getApiBase()" in content or "function getApiBase()" in content,
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        print_status("✓" if passed else "✗", check_name)
        if not passed:
            all_passed = False
    
    return all_passed

def check_backend_running():
    """检查后端是否在运行"""
    print("\n" + "="*60)
    print("4. 检查后端服务")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:5001/health", timeout=2)
        if response.status_code == 200:
            print_status("✓", "后端服务运行正常 (端口 5001)")
            return True
        else:
            print_status("✗", f"后端返回异常状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_status("⚠", "后端未运行 - 需要先启动后端")
        print_status("ℹ", "运行: cd GitHub/resume-ai-builder && python backend/api_server.py")
        return False
    except Exception as e:
        print_status("✗", f"检查后端时出错: {e}")
        return False

def check_api_endpoints():
    """检查关键 API 端点"""
    print("\n" + "="*60)
    print("5. 检查 API 端点")
    print("="*60)
    
    endpoints = {
        "/export/html": "预览 HTML 生成",
        "/export/pdf": "PDF 导出",
    }
    
    all_passed = True
    for endpoint, description in endpoints.items():
        try:
            response = requests.post(
                f"http://localhost:5001{endpoint}",
                json={},
                timeout=5
            )
            # 200 或 400 都算正常（400 可能是缺少必需参数）
            if response.status_code in [200, 400]:
                print_status("✓", f"{description} - 端点可访问")
            else:
                print_status("✗", f"{description} - 状态码 {response.status_code}")
                all_passed = False
        except requests.exceptions.ConnectionError:
            print_status("⚠", f"{description} - 后端未运行")
            all_passed = False
        except Exception as e:
            print_status("✗", f"{description} - 错误: {e}")
            all_passed = False
    
    return all_passed

def main():
    print(f"\n{Colors.BLUE}{'='*60}")
    print("Resume AI Builder - 修复验证脚本")
    print(f"{'='*60}{Colors.END}\n")
    
    # 切换到项目目录
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    print_status("ℹ", f"工作目录: {project_dir}")
    
    results = {
        "文件路径锚定": check_file_paths(),
        "Electron 配置": check_electron_config(),
        "前端预览实现": check_frontend_preview(),
        "后端服务": check_backend_running(),
    }
    
    # 只有后端运行时才检查 API
    if results["后端服务"]:
        results["API 端点"] = check_api_endpoints()
    
    # 总结
    print("\n" + "="*60)
    print("验证总结")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        print_status("✓" if result else "✗", check)
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{'='*60}")
        print("✓ 所有检查通过！修复已生效")
        print(f"{'='*60}{Colors.END}\n")
        print_status("ℹ", "下一步：启动 Electron 应用测试预览功能")
        print_status("ℹ", "命令: cd frontend && npm start")
        return 0
    elif passed >= total - 1 and not results["后端服务"]:
        print(f"\n{Colors.YELLOW}{'='*60}")
        print("⚠ 代码修复已完成，需要启动后端验证")
        print(f"{'='*60}{Colors.END}\n")
        print_status("ℹ", "启动后端: python backend/api_server.py")
        print_status("ℹ", "然后重新运行此脚本")
        return 1
    else:
        print(f"\n{Colors.RED}{'='*60}")
        print("✗ 发现问题，需要进一步修复")
        print(f"{'='*60}{Colors.END}\n")
        return 2

if __name__ == "__main__":
    sys.exit(main())
