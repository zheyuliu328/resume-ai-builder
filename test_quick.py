#!/usr/bin/env python3
"""快速集成测试"""
import requests

BASE = 'http://localhost:5001'

def test_health():
    r = requests.get(f'{BASE}/health')
    assert r.json()['status'] == 'ok'
    print("✅ 健康检查通过")

def test_config():
    r = requests.post(f'{BASE}/api/config', json={'api_key': 'test'})
    assert r.json()['success']
    print("✅ 配置设置通过")

def test_resume_get():
    r = requests.get(f'{BASE}/api/resume')
    print(f"{'✅' if r.status_code == 200 else '⚠️'} 获取简历: {r.status_code}")

if __name__ == '__main__':
    test_health()
    test_config()
    test_resume_get()
    print("\n🎉 所有测试完成")
