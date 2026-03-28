#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from core import optimize_route
import json

result = optimize_route(
    origin='五常',
    destination='哈尔滨',
    waypoints=[
        {'type': 'explicit', 'name': '桥根涮串总店'},
        {'type': 'explicit', 'name': '麦德龙'},
        {'type': 'explicit', 'name': '嵩山路4S店'},
        {'type': 'explicit', 'name': '红星学府'}
    ]
)

# 输出 JSON（避免中文乱码问题）
print(json.dumps(result, ensure_ascii=False, indent=2))
