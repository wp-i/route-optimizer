#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from api.amap import AMapAPI
import time

api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')

# 在哈尔滨搜索麦德龙
harbin = api.geocode('哈尔滨')
print('哈尔滨:', harbin['lng'], harbin['lat'])

# 测试搜索
for radius in [30000, 100000, 200000]:
    try:
        pois = api.search_pois('麦德龙', (harbin['lng'], harbin['lat']), radius=radius, limit=3)
        if pois:
            print(f'{radius/1000}km: 找到 {pois[0]["name"]}')
            break
        else:
            print(f'{radius/1000}km: 无结果')
    except Exception as e:
        print(f'{radius}: error')
    time.sleep(0.3)
