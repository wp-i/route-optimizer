#!/usr/bin/env python3
"""
测试脚本 - 验证 Route Optimizer 功能
"""

import sys
import os

# 添加项目根目录到 Python 路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

import json
from core import optimize_route, configure_api_key, get_config_status

def test_config_status():
    """测试配置状态"""
    print("=" * 50)
    print("测试 1: 获取配置状态")
    print("=" * 50)
    
    result = get_config_status()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()
    
    return result.get("configured", False)

def test_configure():
    """测试配置 API Key"""
    print("=" * 50)
    print("测试 2: 配置 API Key")
    print("=" * 50)
    
    # 请替换为你的实际 API Key
    api_key = input("请输入高德地图 API Key（或按回车跳过）: ").strip()
    
    if not api_key:
        print("跳过配置测试")
        return False
    
    result = configure_api_key(api_key)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()
    
    return result.get("success", False)

def test_optimize_simple():
    """测试简单路线规划"""
    print("=" * 50)
    print("测试 3: 简单路线规划")
    print("=" * 50)
    
    result = optimize_route(
        origin="北京西站",
        destination="首都机场"
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()
    
    return result.get("success", False)

def test_optimize_with_waypoints():
    """测试多途经点路线规划"""
    print("=" * 50)
    print("测试 4: 多途经点路线规划")
    print("=" * 50)
    
    result = optimize_route(
        origin="北京西站",
        destination="首都机场",
        waypoints=[
            {"type": "explicit", "name": "天安门"},
            {"type": "explicit", "name": "鸟巢"}
        ]
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()
    
    return result.get("success", False)

def test_optimize_with_fuzzy():
    """测试模糊途经点路线规划"""
    print("=" * 50)
    print("测试 5: 模糊途经点路线规划")
    print("=" * 50)
    
    result = optimize_route(
        origin="北京西站",
        destination="首都机场",
        waypoints=[
            {"type": "fuzzy", "keyword": "超市"}
        ]
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()
    
    return result.get("success", False)

def main():
    print("\n" + "=" * 50)
    print("Route Optimizer 测试套件")
    print("=" * 50 + "\n")
    
    # 测试 1: 配置状态
    configured = test_config_status()
    
    if not configured:
        print("\n[!] 未配置 API Key，部分测试将失败")
        print("请先运行 test.py 并输入 API Key")
        print()
    
    # 测试 2: 配置（可选）
    # test_configure()
    
    # 测试 3-5: 路线规划（需要 API Key）
    if configured:
        test_optimize_simple()
        test_optimize_with_waypoints()
        test_optimize_with_fuzzy()
    else:
        print("\n跳过路线规划测试（未配置 API Key）")
        print("要运行完整测试，请先配置 API Key：")
        print("  python -c \"from core import configure_api_key; configure_api_key('你的API_KEY')\"")

if __name__ == '__main__':
    main()
