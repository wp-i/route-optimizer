#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from api.amap import AMapAPI

api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')

# 直接在全国范围搜索，不限制位置
places = ['麦德龙', '嵩山路4S店', '红星学府西门']

for p in places:
    try:
        pois = api.search_pois(p, (116.397428, 39.90923), radius=200000, limit=1)
        if pois:
            print(p, '->', pois[0]['name'], pois[0]['lng'], pois[0]['lat'])
        else:
            print(p, '-> no result')
    except Exception as e:
        print(p, '-> error')
