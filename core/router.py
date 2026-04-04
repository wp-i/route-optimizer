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

    # Step 2: 地理编码（起点 → 推断城市 → 终点/途经点）
    # 推理：用户先说起点，隐含整个行程在同一个城市/区域
    import re as re_module

    def extract_city(geo_result):
        addr = geo_result.get("formatted_address", "")
        m = re_module.search(r'(?:省|^)([^省]+?市)', addr)
        if m:
            c = m.group(1)
            return c[:-1] if c.endswith('市') else c
        return ""

    # 起点地理编码（多级降级：地理编码 → POI搜索 → 城市前缀地理编码）
    origin_geo = None
    origin_city = ""

    # 终点地理编码
    dest_geo = None
    dest_city = ""

    def try_geocode_with_fallback(name, hint_city=""):
        """多级降级地理编码：POI文字搜索优先（更精准）→ 地理编码兜底"""
        # 尝试1：POI 文字搜索（比 geocode 更智能，能匹配知名度高的结果）
        try:
            pois = amap.search_text(name, city=hint_city, limit=1)
            if pois:
                p = pois[0]
                addr = p["address"]
                if isinstance(addr, list):
                    addr = ", ".join(str(a) for a in addr)
                return {"name": p["name"], "address": addr, "lng": p["lng"], "lat": p["lat"], "formatted_address": addr}
        except Exception:
            pass
        # 尝试2：直接地理编码
        try:
            geo = amap.geocode(name)
            return geo
        except GeocodeError:
            pass
        # 尝试3：不带城市限定的地理编码兜底
        if hint_city:
            try:
                geo = amap.geocode(name)
                return geo
            except GeocodeError:
                pass
        return None

    origin_geo = try_geocode_with_fallback(origin)
    if origin_geo:
        origin_city = extract_city(origin_geo)
    else:
        return {
            "success": False,
            "error": "地理编码失败",
            "message": f"无法找到起点「{origin}」，请提供更具体的地址"
        }

    # 终点地理编码（优先用起点城市限定）
    dest_geo = try_geocode_with_fallback(destination, hint_city=origin_city)
    if not dest_geo:
        return {
            "success": False,
            "error": "地理编码失败",
            "message": f"无法找到终点「{destination}」，请提供更具体的地址"
        }

    # 明确途经点编码策略
    # 1. 优先用地理编码（带城市上下文），确保知名地点匹配准确
    # 2. 若地理编码无结果，再用 POI 周边搜索
    # 3. 最后用城市前缀兜底（循环路线场景）
    explicit_geos = []
    origin_coord = (origin_geo["lng"], origin_geo["lat"])
    dest_coord = (dest_geo["lng"], dest_geo["lat"])

    # 判断起点和终点是否相同（循环路线场景）
    same_origin_dest = (origin == destination) or (origin_coord == dest_coord)

    # 提取城市上下文（用于地理编码）
    origin_city = extract_city(origin_geo)
    dest_city = extract_city(dest_geo)

    # 计算 POI 搜索中心
    if same_origin_dest:
        search_centers = [origin_coord]
        radii = [50000, 100000, 200000, 500000]
    else:
        search_centers = [dest_coord, origin_coord]
        radii = [30000, 50000, 100000, 200000]

    for name in explicit_waypoints:
        found = False

        # 方法1: POI 文字搜索优先（比 geocode 更智能，能匹配知名度高的结果）
        # 用起终点城市限定搜索范围
        text_cities = []
        if dest_city and not same_origin_dest:
            text_cities.append(dest_city)
        if origin_city:
            text_cities.append(origin_city)
        text_cities.append("")  # 全国搜索兜底

        for city_str in text_cities:
            try:
                pois = amap.search_text(name, city=city_str, limit=3)
                if pois:
                    poi = pois[0]
                    poi_addr = poi["address"]
                    if isinstance(poi_addr, list):
                        poi_addr = ", ".join(str(a) for a in poi_addr)
                    explicit_geos.append({
                        "name": poi["name"],
                        "lng": poi["lng"],
                        "lat": poi["lat"],
                        "address": poi_addr
                    })
                    found = True
                    break
            except Exception:
                continue

        # 方法2: 地理编码兜底（POI搜索失败时）
        if not found:
            geo_attempts = []
            if dest_city and not same_origin_dest:
                geo_attempts.append((name, dest_city))
            if origin_city:
                geo_attempts.append((name, origin_city))
            geo_attempts.append((name, ""))  # 全国搜索兜底

            for addr_str, city_str in geo_attempts:
                try:
                    geo = amap.geocode(addr_str, city=city_str)
                    explicit_geos.append({
                        "name": name,
                        "lng": geo["lng"],
                        "lat": geo["lat"],
                        "address": geo["formatted_address"]
                    })
                    found = True
                    break
                except GeocodeError:
                    continue

        # 方法3: POI 周边搜索（前两者都失败时）
        if not found:
            for center in search_centers:
                for radius in radii:
                    try:
                        pois = amap.search_pois(name, center, radius=radius, limit=5)
                        if pois:
                            poi = pois[0]
                            explicit_geos.append({
                                "name": poi["name"],
                                "lng": poi["lng"],
                                "lat": poi["lat"],
                                "address": poi["address"]
                            })
                            found = True
                            break
                    except Exception:
                        continue
                if found:
                    break

        # 方法3: 循环路线用城市前缀兜底
        if not found and same_origin_dest and origin_city:
            try:
                geo = amap.geocode(f"{origin_city}{name}")
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
            # 记录跳过的途经点，继续规划其他点
            explicit_geos.append({
                "name": name,
                "lng": None,
                "lat": None,
                "address": None,
                "skipped": True,
                "reason": f"未找到「{name}」，已跳过"
            })

    # Step 3: 构建初始坐标列表（起点 + 明确途经点 + 终点）
    # 过滤掉跳过的点
    valid_explicit_geos = [g for g in explicit_geos if not g.get("skipped")]
    skipped_waypoints = [g for g in explicit_geos if g.get("skipped")]

    all_coords = [
        (origin_geo["lng"], origin_geo["lat"])
    ]
    for geo in valid_explicit_geos:
        all_coords.append((geo["lng"], geo["lat"]))
    all_coords.append((dest_geo["lng"], dest_geo["lat"]))

    # 构建名称列表
    all_names = [origin] + [geo["name"] for geo in valid_explicit_geos] + [destination]
    all_addresses = [origin_geo["formatted_address"]] + [geo["address"] for geo in valid_explicit_geos] + [dest_geo["formatted_address"]]

    # Step 4: 提前检查：起点=终点且无途经点，返回提示
    if same_origin_dest and not valid_explicit_geos and not fuzzy_waypoints:
        return {
            "success": True,
            "route": [
                {
                    "name": origin,
                    "address": origin_geo.get("formatted_address", ""),
                    "lng": origin_geo["lng"],
                    "lat": origin_geo["lat"],
                    "type": "origin"
                }
            ],
            "skipped_waypoints": [],
            "total_distance": 0,
            "total_distance_text": "0 米",
            "total_duration": 0,
            "total_duration_text": "0 分钟",
            "segments": [],
            "message": "起点与终点相同且无途经点，无需规划路线。请添加途经点。"
        }

    # Step 5: 计算距离矩阵
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
    waypoint_indices = list(range(1, len(all_coords) - 1))

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

        # 多级模糊搜索策略
        found_pois = []

        # 策略1: 在路线中点附近 10km 搜索（精确匹配）
        try:
            found_pois = amap.search_pois(keyword, midpoint, radius=10000, limit=5)
        except POISearchError:
            pass

        # 策略2: 扩大到 50km
        if not found_pois:
            try:
                found_pois = amap.search_pois(keyword, midpoint, radius=50000, limit=5)
            except POISearchError:
                pass

        # 策略3: 拆分关键词（如"珠江夜游"→"珠江"）
        if not found_pois and len(keyword) > 3:
            short_keyword = keyword[:min(4, len(keyword))]
            try:
                found_pois = amap.search_pois(short_keyword, midpoint, radius=50000, limit=5)
            except POISearchError:
                pass

        # 策略4: 在起点和终点分别搜索
        if not found_pois:
            for center in [origin_coord, dest_coord]:
                try:
                    found_pois = amap.search_pois(keyword, center, radius=30000, limit=5)
                    if found_pois:
                        break
                except POISearchError:
                    continue

        if not found_pois:
            # 降级处理：未找到时返回警告但不失败，继续规划剩余路线
            fuzzy_results.append({
                "keyword": keyword,
                "name": None,
                "address": None,
                "insert_position": None,
                "warning": f"在路线附近未找到「{keyword}」，已跳过"
            })
            continue

        # 选择第一个候选（最近的）
        best_poi = found_pois[0]

        # 简化处理：找到距离路线中点最近的位置插入
        poi_coord = (best_poi["lng"], best_poi["lat"])
        min_dist = float('inf')
        insert_after = 0

        for i, coord in enumerate(ordered_coords[:-1]):
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
        final_dist_matrix = amap.measure_distance_matrix(ordered_coords)

        total_duration = 0
        total_distance = 0
        segments = []

        for i in range(len(ordered_coords) - 1):
            duration = final_dist_matrix[i][i+1]
            total_duration += duration

            segments.append({
                "from": ordered_names[i],
                "from_address": ordered_addresses[i],
                "to": ordered_names[i+1],
                "to_address": ordered_addresses[i+1],
                "duration": duration,
                "duration_text": format_duration(duration)
            })

        # 获取详细路线（分段信息）
        total_distance = 0
        try:
            route_detail = amap.driving_route(
                ordered_coords[0],
                ordered_coords[-1],
                ordered_coords[1:-1] if len(ordered_coords) > 2 else None
            )
            total_distance = route_detail["distance"]
        except:
            # 降级：用 segments 的 driving_route 逐段累加
            for i in range(len(ordered_coords) - 1):
                try:
                    seg_route = amap.driving_route(
                        ordered_coords[i],
                        ordered_coords[i+1]
                    )
                    total_distance += seg_route["distance"]
                except:
                    # 最终降级：按平均车速 30km/h 从时间估算
                    total_distance += segments[i]["duration"] * 30 / 3.6

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
                    "reason": "在路线中点附近找到，已插入到路线中"
                }
                break

        route.append(point_info)

    # 构建消息
    message_parts = [f"已优化路线，总耗时约 {format_duration(total_duration)}"]
    
    # 合并模糊搜索跳过的点
    fuzzy_skipped = [fr for fr in fuzzy_results if fr.get("warning")]
    all_skipped = skipped_waypoints + [{"name": fr["keyword"], "reason": fr.get("warning", "")} for fr in fuzzy_skipped]
    
    if fuzzy_results and not fuzzy_skipped:
        fuzzy_names = [fr["keyword"] for fr in fuzzy_results]
        message_parts.append(f"包含 {len(fuzzy_results)} 个模糊途经点：{', '.join(fuzzy_names)}")
    if all_skipped:
        skipped_names = [sw["name"] for sw in all_skipped]
        message_parts.append(f"跳过 {len(all_skipped)} 个未找到的点：{', '.join(skipped_names)}")

    return {
        "success": True,
        "route": route,
        "skipped_waypoints": all_skipped,
        "total_distance": total_distance,
        "total_distance_text": format_distance(total_distance),
        "total_duration": total_duration,
        "total_duration_text": format_duration(total_duration),
        "segments": segments,
        "message": "。".join(message_parts)
    }


def recommend_nearby(
    route_result: Dict,
    categories: Optional[List[str]] = None,
    radius: int = 5000,
    per_point_limit: int = 3,
    api_key: Optional[str] = None
) -> Dict:
    """
    基于路线推荐附近 POI（商场/公园/景点等）
    
    Args:
        route_result: optimize_route 的返回结果
        categories: 推荐分类列表，默认 ["景点", "公园", "商场", "博物馆"]
        radius: 搜索半径（米），默认 5000
        per_point_limit: 每个路线点每个分类最多返回数量，默认 3
        api_key: 高德 API Key（可选）
    
    Returns:
        {
            "success": True,
            "recommendations": [
                {
                    "near": "天安门",
                    "category": "景点",
                    "items": [
                        {"name": "...", "address": "...", "distance_m": 1200},
                        ...
                    ]
                },
                ...
            ]
        }
    """
    if not route_result.get("success"):
        return {"success": False, "error": "路线规划失败，无法生成推荐"}
    
    route = route_result["route"]
    if not route:
        return {"success": False, "error": "路线为空，无法生成推荐"}
    
    if not api_key:
        api_key = ConfigManager.get_api_key()
    
    if not api_key:
        return {"success": False, "error": "未配置 API Key"}
    
    if categories is None:
        categories = ["旅游景点", "公园广场", "购物中心", "博物馆"]
    
    amap = AMapAPI(api_key)
    
    # 路线中已有的地点名称（避免推荐重复）
    existing_names = set()
    for p in route:
        existing_names.add(p["name"])
        # 也记录名称的核心部分（去掉括号后缀）
        core = p["name"].split("(")[0].split("-")[0].strip()
        if len(core) >= 2:
            existing_names.add(core)
    
    recommendations = []
    
    # 记录已推荐的 POI 名称（全局去重）
    recommended_names = set()
    
    # 每个路线点作为搜索中心
    for point in route:
        coord = (point["lng"], point["lat"])
        point_name = point["name"]
        
        for category in categories:
            try:
                pois = amap.search_pois(category, coord, radius=radius, limit=per_point_limit + 2)
            except Exception:
                continue
            
            items = []
            for poi in pois:
                poi_name = poi["name"]
                # 跳过已有的地点（精确匹配和包含关系）
                if poi_name in existing_names:
                    continue
                poi_core = poi_name.split("(")[0].split("-")[0].strip()
                if poi_core in existing_names or poi_core in recommended_names:
                    continue
                items.append({
                    "name": poi_name,
                    "address": poi.get("address", ""),
                    "distance_m": poi.get("distance", 0),
                    "type": poi.get("type", "")
                })
                recommended_names.add(poi_core)
                if len(items) >= per_point_limit:
                    break
            
            if items:
                recommendations.append({
                    "near": point_name,
                    "category": category,
                    "items": items
                })
    
    return {
        "success": True,
        "recommendations": recommendations
    }


def format_route_output(route_result: Dict, recommendations: Optional[Dict] = None) -> str:
    """
    格式化路线输出为用户可读文本（精简路线图 + 推荐内容组）
    
    Args:
        route_result: optimize_route 的返回结果
        recommendations: recommend_nearby 的返回结果（可选）
    
    Returns:
        格式化的文本字符串
    """
    if not route_result.get("success"):
        return f"路线规划失败: {route_result.get('message', route_result.get('error', ''))}"
    
    lines = []
    route = route_result["route"]
    segments = route_result.get("segments", [])
    
    # === 精简路线图 ===
    lines.append("=" * 40)
    lines.append("  精简路线图")
    lines.append("=" * 40)
    
    if len(route) >= 2:
        for i, point in enumerate(route):
            # 点名称
            prefix = "  "
            if i == 0:
                prefix = "起"
            elif i == len(route) - 1:
                prefix = "终"
            else:
                prefix = "%d" % (i + 1)
            
            lines.append("")
            lines.append("  [%s] %s" % (prefix, point["name"]))
            if point.get("address"):
                lines.append("      %s" % point["address"])
            
            # 到下一段的距离/时间
            if i < len(segments):
                seg = segments[i]
                dist_text = seg.get("duration_text", "")
                # 计算距离
                if i < len(route) - 1:
                    next_p = route[i + 1]
                    d = ((next_p["lng"] - point["lng"])**2 + (next_p["lat"] - point["lat"])**2) ** 0.5
                    dist_km = d * 111.32 * 1.3  # 粗略经纬度转公里
                    if dist_km >= 1:
                        lines.append("      -> 下站: %s (%s, ~%.1fkm)" % (seg["to"], dist_text, dist_km))
                    else:
                        dist_m = dist_km * 1000
                        lines.append("      -> 下站: %s (%s, ~%dm)" % (seg["to"], dist_text, int(dist_m)))
        
        lines.append("")
        lines.append("  总距离: %s | 总耗时: %s" % (
            route_result.get("total_distance_text", ""),
            route_result.get("total_duration_text", "")
        ))
    else:
        lines.append("  " + route_result.get("message", "无路线"))
    
    # 跳过的途经点
    skipped = route_result.get("skipped_waypoints", [])
    if skipped:
        lines.append("")
        lines.append("  [!] 跳过的点: " + ", ".join(
            s["name"] for s in skipped
        ))
    
    # === 推荐内容组 ===
    if recommendations and recommendations.get("success"):
        recs = recommendations.get("recommendations", [])
        if recs:
            lines.append("")
            lines.append("=" * 40)
            lines.append("  推荐内容组")
            lines.append("=" * 40)
            
            # 按分类聚合
            by_category = {}
            for rec in recs:
                cat = rec["category"]
                if cat not in by_category:
                    by_category[cat] = []
                for item in rec["items"]:
                    item["near"] = rec["near"]
                    by_category[cat].append(item)
            
            category_icons = {
                "旅游景点": "景点",
                "公园广场": "公园",
                "购物中心": "商场",
                "博物馆": "博物馆",
            }
            
            for cat, items in by_category.items():
                # 去重（同一个 POI 可能被多个路线点搜到）
                seen = set()
                unique_items = []
                for item in items:
                    if item["name"] not in seen:
                        seen.add(item["name"])
                        unique_items.append(item)
                
                if not unique_items:
                    continue
                
                icon = category_icons.get(cat, cat)
                lines.append("")
                lines.append("  [%s]" % icon)
                for item in unique_items[:5]:  # 每个分类最多5个
                    dist_str = ""
                    if item.get("distance_m"):
                        d = item["distance_m"]
                        if d >= 1000:
                            dist_str = "%.1fkm" % (d / 1000)
                        else:
                            dist_str = "%dm" % d
                    lines.append("    - %s (%s, 在%s附近)" % (
                        item["name"], dist_str, item.get("near", "")
                    ))
    
    return "\n".join(lines)


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
