#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from api.amap import AMapAPI
import time

api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')

# 五常坐标
wuchang = api.geocode('五常')
print('五常:', wuchang['lng'], wuchang['lat'])

# 测试不同半径搜索麦德龙
for radius in [50000, 100000, 200000, 300000]:
    try:
        pois = api.search_pois('麦德龙', (wuchang['lng'], wuchang['lat']), radius=radius, limit=3)
        if pois:
            print(f'{radius/1000}km: 找到 {pois[0]["name"]} 距离{pois[0]["distance"]}米')
            break
        else:
            print(f'{radius/1000}km: 无')
    except Exception as e:
        print(f'{radius/1000}km: error')
    time.sleep(0.3)
