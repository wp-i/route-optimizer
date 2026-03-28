#!/usr/bin/env python3
"""
Route Optimizer Skill 入口脚本

用法：
    python run.py <JSON参数>

参数格式：
    {"action": "optimize", "origin": "北京西站", "destination": "首都机场", "waypoints": [...]}
    {"action": "config", "api_key": "xxx"}
    {"action": "status"}
"""

import sys
import os
import json

# 添加项目根目录到 Python 路径
# 脚本位置: skill/scripts/run.py
# 项目根目录: 向上两级
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, project_root)

from core import optimize_route, configure_api_key, get_config_status


def main():
    if len(sys.argv) < 2:
        result = {
            "success": False,
            "error": "缺少参数",
            "usage": 'python run.py \'{"action": "optimize", "origin": "北京西站", "destination": "首都机场"}\''
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    # 解析输入
    try:
        params = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        result = {
            "success": False,
            "error": f"参数格式错误: {str(e)}"
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    action = params.get('action', 'optimize')
    
    # 执行操作
    try:
        if action == 'config':
            # 配置 API Key
            api_key = params.get('api_key')
            if not api_key:
                result = {
                    "success": False,
                    "error": "缺少 api_key 参数"
                }
            else:
                result = configure_api_key(api_key)
        
        elif action == 'status':
            # 获取配置状态
            result = get_config_status()
            result["success"] = True
        
        elif action == 'optimize':
            # 路线优化
            result = optimize_route(
                origin=params.get('origin'),
                destination=params.get('destination'),
                waypoints=params.get('waypoints', [])
            )
        
        else:
            result = {
                "success": False,
                "error": f"未知操作: {action}"
            }
    
    except Exception as e:
        result = {
            "success": False,
            "error": f"执行错误: {str(e)}"
        }
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
