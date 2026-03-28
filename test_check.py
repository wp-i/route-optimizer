#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from api.amap import AMapAPI

api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')

# 检查各点的地理编码
places = ['桥根涮串总店', '嵩山路4S店', '红星学府', '麦德龙']
harbin = api.geocode('哈尔滨')

print('哈尔滨坐标:', harbin['lng'], harbin['lat'])
print()

for p in places:
    try:
        geo = api.geocode(p)
        print(p, '->')
        print('  坐标:', geo['lng'], geo['lat'])
        print('  地址:', geo['formatted_address'])
    except Exception as e:
        print(p, '-> 失败')
