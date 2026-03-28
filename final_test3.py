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

# 输出详细结果
if result.get('success'):
    print('=' * 60)
    print('路线规划结果')
    print('=' * 60)
    print()
    
    # 起点终点
    print('[起点]', result['route'][0]['name'])
    print('地址:', result['route'][0]['address'])
    print()
    print('[终点]', result['route'][-1]['name'])
    print('地址:', result['route'][-1]['address'])
    print()
    print('-' * 60)
    print('途经点优化顺序:')
    print('-' * 60)
    
    for i, p in enumerate(result['route'][1:-1], 1):
        print(f'{i}. {p["name"]}')
        print(f'   地址: {p["address"]}')
        print(f'   坐标: {p["lng"]}, {p["lat"]}')
        print()
    
    print('-' * 60)
    print('路线统计:')
    print('-' * 60)
    print(f'总耗时: {result["total_duration_text"]}')
    print(f'总距离: {result["total_distance_text"]}')
    print()
    print('-' * 60)
    print('分段导航:')
    print('-' * 60)
    
    for seg in result['segments']:
        from_name = seg['from']
        to_name = seg['to']
        duration = seg['duration_text']
        
        # 找到对应的地址
        from_addr = ''
        to_addr = ''
        for p in result['route']:
            if p['name'] == from_name:
                from_addr = p.get('address', '')
            if p['name'] == to_name:
                to_addr = p.get('address', '')
        
        print(f'{from_name}')
        if from_addr:
            print(f'  -> {from_addr}')
        print(f'  ↓')
        print(f'{to_name}')
        if to_addr:
            print(f'  -> {to_addr}')
        print(f'  耗时: {duration}')
        print()
    
    print('=' * 60)
    print(result.get('message', ''))
    print('=' * 60)
    
else:
    print('规划失败:', result.get('message'))
