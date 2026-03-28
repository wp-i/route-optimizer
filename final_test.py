#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from core import optimize_route

# 模拟用户输入的解析
# 用户：从五常到哈尔滨，途径桥根涮串总店 麦德龙 嵩山路4S店 红星学府
origin = '五常'
destination = '哈尔滨'
waypoints = [
    {'type': 'explicit', 'name': '桥根涮串总店'},
    {'type': 'explicit', 'name': '麦德龙'},
    {'type': 'explicit', 'name': '嵩山路4S店'},
    {'type': 'explicit', 'name': '红星学府'}
]

result = optimize_route(origin, destination, waypoints)

# 输出结果
if result.get('success'):
    print('=== 路线规划结果 ===')
    print()
    print('起点:', result['route'][0]['name'])
    print('终点:', result['route'][-1]['name'])
    print()
    print('途经点优化顺序:')
    for i, p in enumerate(result['route'][1:-1], 1):
        print(f'  {i}. {p["name"]}')
    print()
    print('总耗时:', result['total_duration_text'])
    print('总距离:', result['total_distance_text'])
    print()
    print('分段路线:')
    for seg in result['segments']:
        print(f'  {seg["from"]} -> {seg["to"]}: {seg["duration_text"]}')
else:
    print('错误:', result.get('message'))
