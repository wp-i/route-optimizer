#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from api.amap import AMapAPI

api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')

# 测试用"哈尔滨麦德龙"搜索
wuchang = api.geocode('五常')
print('五常坐标:', wuchang['lng'], wuchang['lat'])

# 五常属于哈尔滨市
# 测试用城市名作为前缀搜索
places = ['麦德龙', '嵩山路4S店', '红星学府', '桥根涮串总店']

print('\n方法1: 加城市前缀"哈尔滨":')
for p in places:
    try:
        # 加城市前缀
        geo = api.geocode(f'哈尔滨{p}')
        print(f'  {p}: {geo["formatted_address"]}')
    except Exception as e:
        print(f'  {p}: 失败')
