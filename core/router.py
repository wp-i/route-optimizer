"""路线规划核心模块"""

import json
from typing import List, Dict, Optional, Tuple
from api.amap import AMapAPI
from api.exceptions import (
    RouteOptimizerError, APIKeyError, GeocodeError, 
    POISearchError, RouteError, InputError
)
from config.manager import ConfigManager
from core.optimizer import (
    tsp_brute_force, calc_midpoint, find_best_insert_position
)


def format_duration(seconds: int) -> str:
    """格式化时间显示"""
    if seconds < 60:
        return f"{seconds} 秒"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} 分钟"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} 小时 {minutes} 分钟"


def format_distance(meters: int) -> str:
    """格式化距离显示"""
    if meters < 1000:
        return f"{meters} 米"
    else:
        km = meters / 1000
        return f"{km:.1f} 公里"


def optimize_route(
    origin: str,
    destination: str,
    waypoints: Optional[List[Dict]] = None,
    api_key: Optional[str] = None
) -> Dict:
    """
    路线优化主函数
    
    Args:
        origin: 起点地址或 POI 名称
        destination: 终点地址或 POI 名称
        waypoints: 途经点列表，格式：
            - 明确途经点：{"type": "explicit", "name": "天安门"}
            - 模糊途经点：{"type": "fuzzy", "keyword": "超市"}
        api_key: 高德 API Key（可选，未提供则从配置读取）
    
    Returns:
        优化结果字典
    """
    # 获取 API Key
    if not api_key:
        api_key = ConfigManager.get_api_key()
    
    if not api_key:
        return {
            "success": False,
            "error": "未配置 API Key",
            "need_config": True,
            "message": "请先配置高德地图 API Key。可访问 https://console.amap.com 免费申请。"
        }
    
    # 验证输入
    if not origin or not destination:
        raise InputError("起点和终点不能为空")
    
    # 允许起点和终点相同（绕一圈的情况）
    
    if waypoints is None:
        waypoints = []
    
    if len(waypoints) > 8:
        raise InputError("途经点不能超过 8 个")
    
    # 初始化 API
    amap = AMapAPI(api_key)
    
    # Step 1: 分离明确途经点和模糊途经点
    explicit_waypoints = []
    fuzzy_waypoints = []
    
    for wp in waypoints:
        wp_type = wp.get("type", "explicit")
        if wp_type == "fuzzy":
            fuzzy_waypoints.append(wp.get("keyword", ""))
        else:
            explicit_waypoints.append(wp.get("name", ""))
    
    # Step 2: 地理编码（起点、终点、明确途经点）
    try:
        origin_geo = amap.geocode(origin)
        dest_geo = amap.geocode(destination)
    except GeocodeError as e:
        return {
            "success": False,
            "error": "地理编码失败",
            "message": str(e)
        }
    
    except GeocodeError as e:
        return {
            "success": False,
            "error": "地理编码失败",
            "message": str(e)
        }
    
    # 明确途经点地理编码
    # 优化策略：先在终点附近搜索POI，再在起点附近搜索，最后才是地理编码
    # 这样"五常到哈尔滨，途经XX"能正确找到哈尔滨的地点
    explicit_geos = []
    origin_coord = (origin_geo["lng"], origin_geo["lat"])
    dest_coord = (dest_geo["lng"], dest_geo["lat"])
    
    # 判断起点和终点是否相同
    same_origin_dest = (origin_coord == dest_coord)
    
    # 计算搜索中心（优先终点，其次起点）
    if same_origin_dest:
        search_centers = [origin_coord]
        radii = [50000, 100000, 200000, 300000]
    else:
        # 优先在终点附近搜索，然后是起点，最后是中点
        search_centers = [
            dest_coord,      # 终点附近（最高优先级）
            origin_coord,   # 起点附近
        ]
        radii = [30000, 50000, 100000, 200000]
    
    for name in explicit_waypoints:
        found = False
        result_name = name  # 最终使用的名称
        
        # 方法1: 先在终点附近搜索POI（最重要的改进！）
        for center in search_centers:
            for radius in radii:
                try:
                    pois = amap.search_pois(name, center, radius=radius, limit=5)
                    if pois:
                        poi = pois[0]
                        explicit_geos.append({
                            "name": poi["name"],  # 使用POI的实际名称
                            "lng": poi["lng"],
                            "lat": poi["lat"],
                            "address": poi["address"]
                        })
                        found = True
                        result_name = poi["name"]
                        break
                except Exception:
                    continue
            if found:
                break
        
        # 方法2: 如果POI搜索没找到，尝试地理编码
        if not found:
            try:
                geo = amap.geocode(name)
                explicit_geos.append({
                    "name": name,
                    "lng": geo["lng"],
                    "lat": geo["lat"],
                    "address": geo["formatted_address"]
                })
                found = True
            except GeocodeError:
                pass
        
        if not found:
            return {
                "success": False,
                "error": f"途经点「{name}」未找到",
                "message": f"在起点、终点及沿线附近未找到「{name}」，请使用更具体的名称或地址"
            }
    
    # Step 3: 构建初始坐标列表（起点 + 明确途经点 + 终点）
    all_coords = [
        (origin_geo["lng"], origin_geo["lat"])
    ]
    for geo in explicit_geos:
        all_coords.append((geo["lng"], geo["lat"]))
    all_coords.append((dest_geo["lng"], dest_geo["lat"]))
    
    # 构建名称列表
    all_names = [origin] + [geo["name"] for geo in explicit_geos] + [destination]
    all_addresses = [origin_geo["formatted_address"]] + [geo["address"] for geo in explicit_geos] + [dest_geo["formatted_address"]]
    
    # Step 4: 计算距离矩阵
    try:
        dist_matrix = amap.measure_distance_matrix(all_coords)
    except Exception as e:
        return {
            "success": False,
            "error": "距离计算失败",
            "message": str(e)
        }
    
    # Step 5: TSP 优化明确途经点顺序
    start_idx = 0
    end_idx = len(all_coords) - 1
    waypoint_indices = list(range(1, len(all_coords) - 1))  # 起点和终点之间的索引
    
    best_order, _ = tsp_brute_force(dist_matrix, start_idx, end_idx, waypoint_indices)
    
    # 更新坐标和名称顺序
    ordered_coords = [all_coords[i] for i in best_order]
    ordered_names = [all_names[i] for i in best_order]
    ordered_addresses = [all_addresses[i] for i in best_order]
    
    # Step 6: 处理模糊途经点
    fuzzy_results = []
    
    for keyword in fuzzy_waypoints:
        # 计算路线中点
        midpoint = calc_midpoint(ordered_coords)
        
        # 搜索 POI
        try:
            pois = amap.search_pois(keyword, midpoint, radius=5000, limit=5)
        except POISearchError as e:
            return {
                "success": False,
                "error": f"搜索「{keyword}」失败",
                "message": str(e)
            }
        
        if not pois:
            return {
                "success": False,
                "error": f"未找到「{keyword}」",
                "message": f"在路线附近未找到「{keyword}」，建议更换关键词或跳过此途经点"
            }
        
        # 构建新的坐标列表（包含候选 POI）
        # 为了计算插入位置，需要构建新的距离矩阵
        
        # 选择第一个候选（最近的）
        best_poi = pois[0]
        
        # 简化处理：找到距离路线中点最近的位置插入
        # 实际应该计算每个插入位置的绕行成本
        
        # 计算到每个路线点的距离
        poi_coord = (best_poi["lng"], best_poi["lat"])
        min_dist = float('inf')
        insert_after = 0
        
        for i, coord in enumerate(ordered_coords[:-1]):  # 不包括终点
            # 简单欧氏距离
            dist = (coord[0] - poi_coord[0])**2 + (coord[1] - poi_coord[1])**2
            if dist < min_dist:
                min_dist = dist
                insert_after = i
        
        # 插入到路线中
        insert_pos = insert_after + 1
        ordered_coords.insert(insert_pos, poi_coord)
        ordered_names.insert(insert_pos, best_poi["name"])
        ordered_addresses.insert(insert_pos, best_poi["address"])
        
        fuzzy_results.append({
            "keyword": keyword,
            "name": best_poi["name"],
            "address": best_poi["address"],
            "insert_position": insert_pos
        })
    
    # Step 7: 获取最终路线详情
    try:
        # 重新计算距离矩阵（包含模糊途经点）
        final_dist_matrix = amap.measure_distance_matrix(ordered_coords)
        
        # 计算总耗时
        total_duration = 0
        total_distance = 0
        segments = []
        
        for i in range(len(ordered_coords) - 1):
            duration = final_dist_matrix[i][i+1]
            # 需要重新获取距离（时间矩阵只有时间）
            # 简化：用路线规划 API 获取详细信息
            
            total_duration += duration
            
            segments.append({
                "from": ordered_names[i],
                "to": ordered_names[i+1],
                "duration": duration,
                "duration_text": format_duration(duration)
            })
        
        # 获取详细路线（分段信息）
        try:
            route_detail = amap.driving_route(
                ordered_coords[0],
                ordered_coords[-1],
                ordered_coords[1:-1] if len(ordered_coords) > 2 else None
            )
            total_distance = route_detail["distance"]
        except:
            # 如果获取详细路线失败，估算距离
            total_distance = total_duration * 10  # 假设平均速度 10m/s
        
    except Exception as e:
        return {
            "success": False,
            "error": "路线计算失败",
            "message": str(e)
        }
    
    # Step 8: 构建返回结果
    route = []
    for i, (name, addr, coord) in enumerate(zip(ordered_names, ordered_addresses, ordered_coords)):
        point_type = "waypoint"
        if i == 0:
            point_type = "origin"
        elif i == len(ordered_coords) - 1:
            point_type = "destination"
        
        point_info = {
            "name": name,
            "address": addr,
            "lng": coord[0],
            "lat": coord[1],
            "type": point_type
        }
        
        # 检查是否是模糊途经点
        for fr in fuzzy_results:
            if name == fr["name"]:
                point_info["type"] = "waypoint_fuzzy"
                point_info["fuzzy_info"] = {
                    "keyword": fr["keyword"],
                    "reason": f"在路线中点附近找到，已插入到路线中"
                }
                break
        
        route.append(point_info)
    
    # 构建消息
    message_parts = [f"已优化路线，总耗时约 {format_duration(total_duration)}"]
    if fuzzy_results:
        fuzzy_names = [fr["keyword"] for fr in fuzzy_results]
        message_parts.append(f"包含 {len(fuzzy_results)} 个模糊途经点：{', '.join(fuzzy_names)}")
    
    return {
        "success": True,
        "route": route,
        "total_distance": total_distance,
        "total_distance_text": format_distance(total_distance),
        "total_duration": total_duration,
        "total_duration_text": format_duration(total_duration),
        "segments": segments,
        "message": "。".join(message_parts)
    }


def configure_api_key(api_key: str) -> Dict:
    """
    配置 API Key
    
    Args:
        api_key: 高德地图 API Key
    
    Returns:
        结果字典
    """
    if not api_key or len(api_key) < 10:
        return {
            "success": False,
            "error": "API Key 格式不正确",
            "message": "请输入有效的高德地图 API Key"
        }
    
    ConfigManager.set_api_key(api_key)
    
    return {
        "success": True,
        "message": f"API Key 已保存: {ConfigManager.mask_api_key(api_key)}"
    }


def get_config_status() -> Dict:
    """
    获取配置状态
    
    Returns:
        配置状态字典
    """
    api_key = ConfigManager.get_api_key()
    
    if api_key:
        return {
            "configured": True,
            "masked_key": ConfigManager.mask_api_key(api_key),
            "message": "已配置高德地图 API Key"
        }
    else:
        return {
            "configured": False,
            "message": "未配置 API Key，请先配置高德地图 API Key"
        }
