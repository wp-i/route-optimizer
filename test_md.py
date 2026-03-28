#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from api.amap import AMapAPI
api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')
wuchang = api.geocode('五常')

# 麦德龙扩大范围到200km
pois = api.search_pois('麦德龙', (wuchang['lng'], wuchang['lat']), radius=200000, limit=3)
print('麦德龙 200km范围:')
for p in pois:
    print(f'  {p["name"]} 距离{p["distance"]}米')
