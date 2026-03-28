#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from api.amap import AMapAPI
api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')

# 先获取哈尔滨的坐标
harbin = api.geocode('哈尔滨')
print('哈尔滨坐标:', harbin['lng'], harbin['lat'])

# 在哈尔滨附近搜索这些地点
places = ['麦德龙', '嵩山路4S店', '红星学府西门', '桥根涮串总店']

print('\n在哈尔滨附近搜索:')
for name in places:
    pois = api.search_pois(name, (harbin['lng'], harbin['lat']), radius=50000, limit=3)
    if pois:
        print(f'\n{name}:')
        for p in pois:
            print(f'  - {p["name"]} ({p["address"]}) 距离{p["distance"]}米')
    else:
        print(f'\n{name}: 无结果')
