#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from api.amap import AMapAPI

api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')

# 五常的坐标
wuchang = api.geocode('五常')
print('五常坐标:', wuchang['lng'], wuchang['lat'])

# 在五常附近搜索"麦德龙"
print('\n在五常附近搜索麦德龙:')
pois = api.search_pois('麦德龙', (wuchang['lng'], wuchang['lat']), radius=50000, limit=5)
for p in pois:
    print(f'  {p["name"]} - {p["address"]} - 距离{p["distance"]}米')

# 搜索"4S店"
print('\n在五常附近搜索4S店:')
pois = api.search_pois('4S店', (wuchang['lng'], wuchang['lat']), radius=50000, limit=5)
for p in pois:
    print(f'  {p["name"]} - {p["address"]} - 距离{p["distance"]}米')

# 搜索"学府"
print('\n在五常附近搜索学府:')
pois = api.search_pois('学府', (wuchang['lng'], wuchang['lat']), radius=50000, limit=5)
for p in pois:
    print(f'  {p["name"]} - {p["address"]} - 距离{p["distance"]}米')
