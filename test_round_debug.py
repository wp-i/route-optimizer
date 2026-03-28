#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from api.amap import AMapAPI
import time

api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')

# 五常坐标
wuchang = api.geocode('五常')
print('五常坐标:', wuchang['lng'], wuchang['lat'])

# 测试在不同半径下搜索麦德龙
places = ['麦德龙', '嵩山路4S店', '红星学府', '桥根涮串总店']

print('\n在五常附近搜索（扩大到500km）:')
for p in places:
    print(f'\n搜索 {p}:')
    for radius in [50000, 100000, 200000, 500000]:
        try:
            pois = api.search_pois(p, (wuchang['lng'], wuchang['lat']), radius=radius, limit=3)
            if pois:
                print(f'  {radius/1000}km: 找到 {pois[0]["name"]} 距离{pois[0]["distance"]}米')
                break
            else:
                print(f'  {radius/1000}km: 无结果')
        except Exception as e:
            print(f'  {radius/1000}km: 错误')
        time.sleep(0.3)
