#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""路线规划格式化输出"""
import sys
sys.path.insert(0, '.')

from core import optimize_route

def format_route_result(result):
    """格式化路线规划结果"""
    if not result.get('success'):
        return f"规划失败: {result.get('message', '未知错误')}"
    
    lines = []
    lines.append("路线规划结果")
    lines.append("=" * 60)
    
    route = result['route']
    
    # 起点终点
    origin = route[0]
    dest = route[-1]
    lines.append(f"起点：{origin['name']}（{origin['address']}）")
    lines.append(f"终点：{dest['name']}（{dest['address']}）")
    lines.append("")
    
    # 途经点
    if len(route) > 2:
        lines.append("途经点：")
        for i, p in enumerate(route[1:-1], 1):
            lines.append(f"  {i}. {p['name']}（{p['address']}）")
        lines.append("")
    
    lines.append("=" * 60)
    lines.append("路线分段")
    lines.append("=" * 60)
    lines.append("")
    
    # 分段详情
    for i, seg in enumerate(result['segments'], 1):
        lines.append(f"{i}. {seg['from']} → {seg['to']}")
        lines.append("")
        lines.append(f"   起点 → 终点：{seg['from_address']} → {seg['to_address']}")
        lines.append(f"   耗时：{seg['duration_text']}")
        lines.append("")
    
    lines.append("=" * 60)
    lines.append(f"总耗时：{result['total_duration_text']}")
    lines.append(f"总距离：{result['total_distance_text']}")
    lines.append("=" * 60)
    
    return "\n".join(lines)


if __name__ == '__main__':
    # 测试1: 普通路线
    print("\n" + "=" * 60)
    print("测试1: 上海站 → 外滩，途经肯德基、星巴克")
    print("=" * 60 + "\n")
    
    result = optimize_route(
        origin="上海站",
        destination="外滩",
        waypoints=[
            {"type": "explicit", "name": "肯德基"},
            {"type": "explicit", "name": "星巴克"}
        ]
    )
    
    print(format_route_result(result))
