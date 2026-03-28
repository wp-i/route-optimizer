#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from core import optimize_route

# 测试你给的场景
result = optimize_route(
    origin='五常',
    destination='五常',
    waypoints=[
        {'type': 'explicit', 'name': '桥根涮串总店'},
        {'type': 'explicit', 'name': '麦德龙'},
        {'type': 'explicit', 'name': '嵩山路4S店'},
        {'type': 'explicit', 'name': '红星学府西门'}
    ]
)

print('Success:', result.get('success'))
if result.get('success'):
    print('Route:')
    for i, p in enumerate(result.get('route', [])):
        print(f'  {i+1}. {p.get("name")}')
    print(f'Total: {result.get("total_duration_text")} / {result.get("total_distance_text")}')
else:
    print('Error:', result.get('error'))
    print('Message:', result.get('message'))
