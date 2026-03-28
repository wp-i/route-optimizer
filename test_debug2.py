#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import time
sys.path.insert(0, '.')

from api.amap import AMapAPI

api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')

# 先获取五常的坐标
origin = api.geocode('五常')
print('起点坐标:', origin['lng'], origin['lat'])

# 测试用这个坐标搜索
places = ['麦德龙', '嵩山路4S店', '红星学府西门']
for p in places:
    try:
        pois = api.search_pois(p, (origin['lng'], origin['lat']), radius=20000, limit=2)
        if pois:
            print(f'{p}: 找到 -> {pois[0]["name"]}')
        else:
            print(f'{p}: 无结果')
    except Exception as e:
        print(f'{p}: 错误 - {e}')
    time.sleep(0.5)
