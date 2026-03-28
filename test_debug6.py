#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from api.amap import AMapAPI

api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')

# 获取起点坐标
origin = api.geocode('五常')
print('起点五常坐标:', origin['lng'], origin['lat'])

# 测试四个途经点
places = ['桥根涮串总店', '麦德龙', '嵩山路4S店', '红星学府西门']

for name in places:
    # 方法1: 直接地理编码
    try:
        geo = api.geocode(name)
        print(f'\n{name}: 地理编码成功 -> {geo["formatted_address"]}')
        continue
    except Exception as e:
        pass

    # 方法2: POI搜索 (20km)
    pois = api.search_pois(name, (origin['lng'], origin['lat']), radius=20000, limit=2)
    if pois:
        print(f'\n{name}: 20km内找到 -> {pois[0]["name"]} 距离{pois[0]["distance"]}米')
        continue

    # 方法3: POI搜索 (50km)
    pois = api.search_pois(name, (origin['lng'], origin['lat']), radius=50000, limit=2)
    if pois:
        print(f'\n{name}: 50km内找到 -> {pois[0]["name"]} 距离{pois[0]["distance"]}米')
        continue

    # 方法4: POI搜索 (100km)
    pois = api.search_pois(name, (origin['lng'], origin['lat']), radius=100000, limit=2)
    if pois:
        print(f'\n{name}: 100km内找到 -> {pois[0]["name"]} 距离{pois[0]["distance"]}米')
        continue

    # 找不到
    print(f'\n{name}: 找不到!')
