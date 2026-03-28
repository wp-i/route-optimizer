#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from core import optimize_route

# 测试南京的路线
result = optimize_route(
    origin='南京站',
    destination='新街口',
    waypoints=[
        {'type': 'explicit', 'name': '汉堡王'},
        {'type': 'explicit', 'name': '麦当劳'},
        {'type': 'explicit', 'name': '新百'}
    ]
)

print('Success:', result.get('success'))
if result.get('success'):
    print('Route:')
    for i, p in enumerate(result.get('route', [])):
        print(f'  {i+1}. {p.get("name")}')
    print(f'Total: {result.get("total_duration_text")} / {result.get("total_distance_text")}')
else:
    print('Error:', result.get('message'))
