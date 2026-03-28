"""TSP 优化算法"""

import itertools
from typing import List, Tuple


def tsp_brute_force(
    dist_matrix: List[List[int]], 
    start_idx: int, 
    end_idx: int, 
    waypoint_indices: List[int]
) -> Tuple[List[int], int]:
    """
    暴力枚举求解 TSP（途经点 ≤ 8 时使用）
    
    Args:
        dist_matrix: 距离/时间矩阵，dist_matrix[i][j] = 从点 i 到点 j 的距离/时间
        start_idx: 起点索引
        end_idx: 终点索引
        waypoint_indices: 途经点索引列表
    
    Returns:
        (best_order, min_cost)
        - best_order: 最优访问顺序（索引列表）
        - min_cost: 最小总耗时
    """
    if not waypoint_indices:
        # 没有途经点，直接返回 起点 → 终点
        return [start_idx, end_idx], dist_matrix[start_idx][end_idx]
    
    min_cost = float('inf')
    best_order = None
    
    # 枚举所有途经点排列
    for perm in itertools.permutations(waypoint_indices):
        # 构建完整路径：起点 → 途经点排列 → 终点
        path = [start_idx] + list(perm) + [end_idx]
        
        # 计算总耗时
        cost = 0
        for i in range(len(path) - 1):
            cost += dist_matrix[path[i]][path[i + 1]]
        
        if cost < min_cost:
            min_cost = cost
            best_order = path
    
    return best_order, int(min_cost)


def calc_midpoint(coords: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    计算坐标点的几何中心
    
    Args:
        coords: 坐标列表 [(lng, lat), ...]
    
    Returns:
        几何中心坐标 (lng, lat)
    """
    if not coords:
        return (0.0, 0.0)
    
    total_lng = sum(c[0] for c in coords)
    total_lat = sum(c[1] for c in coords)
    
    return (total_lng / len(coords), total_lat / len(coords))


def calc_detour(
    route_coords: List[Tuple[float, float]], 
    new_point: Tuple[float, float], 
    insert_pos: int,
    dist_matrix: List[List[int]],
    point_index_map: dict
) -> int:
    """
    计算插入新点到指定位置的绕行成本
    
    Args:
        route_coords: 当前路线坐标列表
        new_point: 新点坐标
        insert_pos: 插入位置（在此位置之后插入）
        dist_matrix: 距离矩阵
        point_index_map: 坐标到矩阵索引的映射
    
    Returns:
        绕行成本（增加的时间，秒）
    """
    if insert_pos >= len(route_coords) - 1:
        return float('inf')
    
    # 获取插入点前后的索引
    A_idx = point_index_map.get(route_coords[insert_pos])
    B_idx = point_index_map.get(route_coords[insert_pos + 1])
    new_idx = point_index_map.get(new_point)
    
    if A_idx is None or B_idx is None or new_idx is None:
        return float('inf')
    
    # 原始：A → B
    original = dist_matrix[A_idx][B]
    
    # 插入后：A → new_point → B
    new_path = dist_matrix[A_idx][new_idx] + dist_matrix[new_idx][B_idx]
    
    return new_path - original


def find_best_insert_position(
    route_coords: List[Tuple[float, float]],
    new_point: Tuple[float, float],
    dist_matrix: List[List[int]],
    point_index_map: dict
) -> Tuple[int, int]:
    """
    找到最佳插入位置
    
    Args:
        route_coords: 当前路线坐标列表
        new_point: 新点坐标
        dist_matrix: 距离矩阵
        point_index_map: 坐标到矩阵索引的映射
    
    Returns:
        (best_pos, min_detour)
        - best_pos: 最佳插入位置
        - min_detour: 最小绕行成本
    """
    best_pos = 0
    min_detour = float('inf')
    
    # 尝试插入到每个位置
    for pos in range(len(route_coords) - 1):
        detour = calc_detour(route_coords, new_point, pos, dist_matrix, point_index_map)
        if detour < min_detour:
            min_detour = detour
            best_pos = pos
    
    return best_pos, int(min_detour)
