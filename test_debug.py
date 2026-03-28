#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from api.amap import AMapAPI

api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')

places = ['五常', '桥根涮串总店', '麦德龙', '嵩山路4S店', '红星学府西门']

for p in places:
    try:
        result = api.geocode(p)
        print(f'{p}: OK -> {result.get("lng")}, {result.get("lat")}')
    except Exception as e:
        print(f'{p}: FAILED -> {e}')
