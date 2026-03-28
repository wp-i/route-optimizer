#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from core import optimize_route
import json

result = optimize_route(
    origin='仙鹤门地铁站',
    destination='南京新百',
    waypoints=[{'type': 'explicit', 'name': '汉堡王'}]
)

# 只打印关键信息
print('=== 路线规划结果 ===')
print('Success:', result.get('success'))
print()
for i, p in enumerate(result.get('route', [])):
    print(f'{i+1}. {p.get("name")}')
print()
print('Total Duration:', result.get('total_duration_text'))
print('Total Distance:', result.get('total_distance_text'))
print()
print('Message:', result.get('message'))
