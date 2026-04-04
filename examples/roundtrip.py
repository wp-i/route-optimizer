#!/usr/bin/env python3
"""示例：往返路线 - 起点=终点"""
import sys
sys.path.insert(0, '..')

from core import optimize_route

# 用户：从家出发逛完回家
result = optimize_route(
    origin='北京市朝阳区国贸',
    destination='北京市朝阳区国贸',  # 同一起终点
    waypoints=[
        {'type': 'explicit', 'name': '天安门'},
        {'type': 'explicit', 'name': '王府井'},
        {'type': 'fuzzy', 'keyword': '停车场'},
    ]
)

if result.get('success'):
    print('起点/终点:', result['route'][0]['name'])
    print()
    print('最优路线顺序:')
    for i, p in enumerate(result['route']):
        if p['type'] == 'origin':
            tag = '(起点)'
        elif p['type'] == 'destination':
            tag = '(终点/回家)'
        elif p['type'] == 'waypoint_fuzzy':
            tag = '(附近搜索)'
        else:
            tag = ''
        print(f'  {i+1}. {p["name"]} {tag}')
    print()
    print('总耗时:', result['total_duration_text'])
    print('总距离:', result['total_distance_text'])
else:
    print('错误:', result.get('message'))
