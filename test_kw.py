#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from api.amap import AMapAPI

api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')

# 测试：用"哈尔滨+麦德龙"作为关键词搜索
keywords = ['哈尔滨麦德龙', '麦德龙']
wuchang = api.geocode('五常')

print('五常坐标:', wuchang['lng'], wuchang['lat'])

for kw in keywords:
    print(f'\n搜索关键词: {kw}')
    # 使用keywords参数搜索
    pois = api.search_pois(kw, (wuchang['lng'], wuchang['lat']), radius=300000, limit=3)
    if pois:
        for p in pois:
            print(f'  找到: {p["name"]} ({p["address"]})')
    else:
        print('  无结果')
