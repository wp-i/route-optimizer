#!/usr/bin/env python3
"""示例：模糊途经点 - 在路线附近自动搜索"""
import sys
sys.path.insert(0, '..')

from core import optimize_route

# 用户：从北京西站到首都机场，途经天安门、找个超市
result = optimize_route(
    origin='北京西站',
    destination='首都机场',
    waypoints=[
        {'type': 'explicit', 'name': '天安门'},
        {'type': 'fuzzy', 'keyword': '超市'},  # 模糊途经点
    ]
)

if result.get('success'):
    print('起点:', result['route'][0]['name'])
    print('终点:', result['route'][-1]['name'])
    print()
    print('路线顺序:')
    for i, p in enumerate(result['route']):
        tag = {'origin': '(起点)', 'destination': '(终点)', 'waypoint_fuzzy': '(附近搜索)'}.get(p['type'], '')
        print(f'  {i+1}. {p["name"]} {tag}')
    print()
    print('总耗时:', result['total_duration_text'])
else:
    print('错误:', result.get('message'))
