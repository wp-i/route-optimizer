#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from core import optimize_route

# 测试循环路线：从家出发，去三个地点后回家
result = optimize_route(
    origin='五常',
    destination='五常',  # 回家
    waypoints=[
        {'type': 'explicit', 'name': '桥根涮串总店'},
        {'type': 'explicit', 'name': '麦德龙'},
        {'type': 'explicit', 'name': '嵩山路4S店'},
        {'type': 'explicit', 'name': '红星学府'}
    ]
)

if result.get('success'):
    route_points = []
    for p in result['route']:
        route_points.append({
            'name': p['name'],
            'address': p['address']
        })
    
    print('=' * 60)
    print('循环路线规划结果')
    print('=' * 60)
    print()
    print(f'起点/终点: {route_points[0]["name"]}')
    print()
    print('-' * 60)
    
    for i in range(len(route_points) - 1):
        from_p = route_points[i]
        to_p = route_points[i + 1]
        seg = result['segments'][i]
        
        print(f'{i+1}. {from_p["name"]} -> {to_p["name"]}')
        print(f'   耗时: {seg["duration_text"]}')
        print()
    
    print('-' * 60)
    print(f'总耗时: {result["total_duration_text"]}')
    print(f'总距离: {result["total_distance_text"]}')
    print('=' * 60)
else:
    print('规划失败:', result.get('error'))
    print('详情:', result.get('message'))
