#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from api.amap import AMapAPI

api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')

wuchang = api.geocode('五常')
harbin = api.geocode('哈尔滨')

# 简化直线距离
lng1, lat1 = wuchang['lng'], wuchang['lat']
lng2, lat2 = harbin['lng'], harbin['lat']
dist = ((lng2-lng1)**2 + (lat2-lat1)**2)**0.5 * 111
print(f'五常到哈尔滨直线距离: 约 {dist:.0f} km')

# 从哈尔滨搜麦德龙
print('\n从哈尔滨搜索麦德龙:')
pois = api.search_pois('麦德龙', (lng2, lat2), radius=30000, limit=3)
for p in pois:
    print(f'  {p["name"]} 距离{p["distance"]}米')
