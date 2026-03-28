#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

from api.amap import AMapAPI

api = AMapAPI('690019cfbfcdd40d3cb9541f090c6c9c')

# 获取起点和终点
origin = api.geocode('五常')
dest = api.geocode('五常')

print('起点:', origin['lng'], origin['lat'])
print('终点:', dest['lng'], dest['lat'])

# 中点
mid = ((origin['lng']+dest['lng'])/2, (origin['lat']+dest['lat'])/2)
print('中点:', mid)

# 搜索中心
centers = [
    ('起点', (origin['lng'], origin['lat'])),
    ('终点', (dest['lng'], dest['lat'])),
    ('中点', mid)
]

places = ['桥根涮串总店', '麦德龙', '嵩山路4S店', '红星学府西门']

for name in places:
    print(f'\n=== 搜索 {name} ===')
    
    # 先尝试地理编码
    try:
        geo = api.geocode(name)
        print(f'  地理编码成功: {geo["formatted_address"]}')
        continue
    except Exception as e:
        pass
    
    # 在各中心点搜索
    for label, center in centers:
        for radius in [30000, 100000, 200000]:
            try:
                pois = api.search_pois(name, center, radius=radius, limit=3)
                if pois:
                    print(f'  在{label}附近{radius/1000}km找到: {pois[0]["name"]}')
                    break
            except Exception:
                pass
        else:
            continue
        break
    else:
        print(f'  未找到!')
