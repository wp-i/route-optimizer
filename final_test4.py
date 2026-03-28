#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from core import optimize_route

# 用户输入
origin = '五常'
destination = '哈尔滨'
waypoints = [
    {'type': 'explicit', 'name': '桥根涮串总店'},
    {'type': 'explicit', 'name': '麦德龙'},
    {'type': 'explicit', 'name': '嵩山路4S店'},
    {'type': 'explicit', 'name': '红星学府'}
]

result = optimize_route(origin, destination, waypoints)

if result.get('success'):
    # 构建完整路线列表
    route_points = []
    for p in result['route']:
        route_points.append({
            'name': p['name'],
            'address': p['address']
        })
    
    print('=' * 60)
    print('路线规划结果')
    print('=' * 60)
    print()
    print(f'起点: {route_points[0]["name"]}')
    print(f'      {route_points[0]["address"]}')
    print()
    print(f'终点: {route_points[-1]["name"]}')
    print(f'      {route_points[-1]["address"]}')
    print()
    print('-' * 60)
    
    # 分段导航：路线点 + 时间
    for i in range(len(route_points) - 1):
        from_p = route_points[i]
        to_p = route_points[i + 1]
        seg = result['segments'][i]
        
        # 简化地址显示
        from_addr = from_p['address'].replace('黑龙江省哈尔滨市', '')
        to_addr = to_p['address'].replace('黑龙江省哈尔滨市', '')
        
        print(f'{i+1}. {from_p["name"]} → {to_p["name"]}')
        print(f'   {from_addr} → {to_addr}')
        print(f'   耗时: {seg["duration_text"]}')
        print()
    
    print('-' * 60)
    print(f'总耗时: {result["total_duration_text"]}')
    print(f'总距离: {result["total_distance_text"]}')
    print('=' * 60)
else:
    print('规划失败:', result.get('message'))
