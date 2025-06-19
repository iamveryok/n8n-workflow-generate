#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试n8n API认证
"""

import requests
import json
from config import N8N_CONFIG

def test_n8n_connection():
    """测试n8n连接和认证"""
    print("🔍 开始测试n8n API连接...")
    print(f"📋 N8N配置信息:")
    print(f"   - 基础URL: {N8N_CONFIG['base_url']}")
    print(f"   - API密钥: {N8N_CONFIG['api_key'][:20]}..." if N8N_CONFIG['api_key'] else "   - API密钥: 未设置")
    
    # 测试1: 检查n8n服务是否运行
    print("\n🔍 测试1: 检查n8n服务是否运行...")
    try:
        response = requests.get(f"{N8N_CONFIG['base_url']}/", timeout=10)
        print(f"   📡 响应状态码: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ n8n服务正在运行")
        else:
            print(f"   ⚠️ n8n服务响应异常: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 无法连接到n8n服务: {e}")
        return False
    
    # 测试2: 测试API密钥认证
    print("\n🔍 测试2: 测试API密钥认证...")
    headers = {
        "Content-Type": "application/json",
        "X-N8N-API-KEY": N8N_CONFIG["api_key"]
    }
    
    try:
        # 尝试获取工作流列表
        response = requests.get(
            f"{N8N_CONFIG['base_url']}/api/v1/workflows",
            headers=headers,
            timeout=10
        )
        
        print(f"   📡 响应状态码: {response.status_code}")
        print(f"   📄 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("   ✅ API密钥认证成功")
            workflows = response.json()
            print(f"   📊 当前工作流数量: {len(workflows)}")
            return True
        elif response.status_code == 401:
            print("   ❌ API密钥认证失败")
            print(f"   📄 错误响应: {response.text}")
            
            # 尝试不带API密钥的请求
            print("\n🔍 测试3: 尝试不带API密钥的请求...")
            response_no_auth = requests.get(
                f"{N8N_CONFIG['base_url']}/api/v1/workflows",
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            print(f"   📡 无认证响应状态码: {response_no_auth.status_code}")
            
            if response_no_auth.status_code == 401:
                print("   ℹ️ n8n需要API密钥认证")
            else:
                print("   ⚠️ n8n可能未启用API密钥认证")
            
            return False
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
            print(f"   📄 错误响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
        return False

def test_api_key_format():
    """测试API密钥格式"""
    print("\n🔍 测试4: 检查API密钥格式...")
    api_key = N8N_CONFIG["api_key"]
    
    if not api_key:
        print("   ❌ API密钥为空")
        return False
    
    print(f"   📏 API密钥长度: {len(api_key)}")
    print(f"   🔤 API密钥格式: {api_key[:20]}...")
    
    # 检查是否是JWT格式
    if api_key.count('.') == 2:
        print("   ✅ API密钥格式看起来像JWT令牌")
        try:
            import jwt
            # 尝试解码JWT（不验证签名）
            decoded = jwt.decode(api_key, options={"verify_signature": False})
            print(f"   📅 JWT过期时间: {decoded.get('exp', 'Unknown')}")
            print(f"   👤 JWT主题: {decoded.get('sub', 'Unknown')}")
            print(f"   🏢 JWT发行者: {decoded.get('iss', 'Unknown')}")
        except ImportError:
            print("   ℹ️ 无法解析JWT（需要安装PyJWT库）")
        except Exception as e:
            print(f"   ⚠️ JWT解析失败: {e}")
    else:
        print("   ⚠️ API密钥格式不是标准JWT")
    
    return True

def provide_solutions():
    """提供解决方案"""
    print("\n💡 解决方案:")
    print("1. 🔑 重新生成API密钥:")
    print("   - 登录n8n网页界面: http://localhost:5678")
    print("   - 点击右上角用户图标 → Settings → API")
    print("   - 删除旧的API密钥")
    print("   - 点击'Create New API Key'创建新密钥")
    print("   - 复制新密钥到config.py文件中")
    
    print("\n2. ⚙️ 检查n8n配置:")
    print("   - 确保n8n启用了API密钥认证")
    print("   - 检查n8n的环境变量设置")
    print("   - 重启n8n服务")
    
    print("\n3. 🔧 临时解决方案（无认证模式）:")
    print("   - 在config.py中将api_key设置为空字符串")
    print("   - 注意：这会降低安全性")

if __name__ == "__main__":
    print("🚀 n8n API认证诊断工具")
    print("=" * 50)
    
    success = test_n8n_connection()
    test_api_key_format()
    
    if not success:
        provide_solutions()
    
    print("\n" + "=" * 50)
    print("🎯 诊断完成") 