#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from api.amap import AMapAPI

api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')

# 桥根涮串总店
name = '桥根涮串总店'
wuchang = api.geocode('五常')

print('五常坐标:', wuchang['lng'], wuchang['lat'])

# 测试1: 直接地理编码
print('\n测试1: 直接地理编码')
try:
    r = api.geocode(name)
    print('  成功:', r['lng'], r['lat'], r['formatted_address'])
except Exception as e:
    print('  失败')

# 测试2: 20km搜索
print('\n测试2: 20km搜索')
try:
    pois = api.search_pois(name, (wuchang['lng'], wuchang['lat']), radius=20000, limit=3)
    if pois:
        for p in pois:
            print(f'  找到: {p["name"]} 距离{p["distance"]}米')
    else:
        print('  无结果')
except Exception as e:
    print('  错误:', e)

# 测试3: 100km搜索
print('\n测试3: 100km搜索')
try:
    pois = api.search_pois(name, (wuchang['lng'], wuchang['lat']), radius=100000, limit=3)
    if pois:
        for p in pois:
            print(f'  找到: {p["name"]} 距离{p["distance"]}米')
    else:
        print('  无结果')
except Exception as e:
    print('  错误:', e)
