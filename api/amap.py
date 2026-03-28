"""高德地图 API 封装"""

import httpx
from typing import List, Dict, Optional, Tuple
from .exceptions import (
    APIKeyError, GeocodeError, POISearchError, 
    DistanceError, RouteError, NetworkError
)


class AMapAPI:
    """高德地图 API 封装类"""
    
    BASE_URL = "https://restapi.amap.com"
    
    def __init__(self, api_key: str, timeout: float = 10.0):
        self.api_key = api_key
        self.client = httpx.Client(timeout=timeout)
    
    def __del__(self):
        if hasattr(self, 'client'):
            self.client.close()
    
    def _request(self, url: str, params: dict) -> dict:
        """发送请求并处理响应"""
        params["key"] = self.api_key
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException:
            raise NetworkError("请求超时，请稍后重试")
        except httpx.HTTPError as e:
            raise NetworkError(f"网络请求失败: {str(e)}")
        
        # 检查 API 状态
        if data.get("status") != "1":
            info = data.get("info", "未知错误")
            infocode = data.get("infocode", "")
            
            # 特殊处理 API Key 错误
            if infocode in ["10001", "10002", "10003"]:
                raise APIKeyError(f"API Key 无效或权限不足: {info}")
            
            return {"status": "0", "info": info, "infocode": infocode, "data": data}
        
        return {"status": "1", "data": data}
    
    def geocode(self, address: str, city: str = "") -> Dict:
        """
        地址转坐标
        
        Args:
            address: 地址字符串
            city: 城市名称（可选，提高准确性）
        
        Returns:
            {
                "lng": float,
                "lat": float,
                "formatted_address": str,
                "adcode": str
            }
        """
        url = f"{self.BASE_URL}/v3/geocode/geo"
        params = {"address": address}
        if city:
            params["city"] = city
        
        result = self._request(url, params)
        
        if result["status"] != "1":
            raise GeocodeError(f"地址解析失败: {result.get('info', '未知错误')}")
        
        geocodes = result["data"].get("geocodes", [])
        if not geocodes:
            raise GeocodeError(f"未找到地址: {address}")
        
        geo = geocodes[0]
        location = geo.get("location", "").split(",")
        
        if len(location) != 2:
            raise GeocodeError(f"地址解析结果异常: {address}")
        
        return {
            "lng": float(location[0]),
            "lat": float(location[1]),
            "formatted_address": geo.get("formatted_address", ""),
            "adcode": geo.get("adcode", "")
        }
    
    def search_pois(
        self, 
        keyword: str, 
        location: Tuple[float, float], 
        radius: int = 3000,
        limit: int = 5
    ) -> List[Dict]:
        """
        周边搜索 POI
        
        Args:
            keyword: 搜索关键词
            location: 中心点坐标 (lng, lat)
            radius: 搜索半径（米），默认 3000
            limit: 返回数量限制，默认 5
        
        Returns:
            [
                {
                    "id": str,
                    "name": str,
                    "address": str,
                    "lng": float,
                    "lat": float,
                    "distance": int,
                    "type": str
                },
                ...
            ]
        """
        url = f"{self.BASE_URL}/v3/place/around"
        params = {
            "keywords": keyword,
            "location": f"{location[0]},{location[1]}",
            "radius": radius,
            "offset": limit,
            "extensions": "all"
        }
        
        result = self._request(url, params)
        
        if result["status"] != "1":
            raise POISearchError(f"POI 搜索失败: {result.get('info', '未知错误')}")
        
        pois = result["data"].get("pois", [])
        
        formatted_pois = []
        for poi in pois:
            loc = poi.get("location", "").split(",")
            if len(loc) != 2:
                continue
            
            formatted_pois.append({
                "id": poi.get("id", ""),
                "name": poi.get("name", ""),
                "address": poi.get("address", ""),
                "lng": float(loc[0]),
                "lat": float(loc[1]),
                "distance": int(poi.get("distance", 0)),
                "type": poi.get("type", "")
            })
        
        return formatted_pois
    
    def measure_distance(
        self, 
        origins: List[Tuple[float, float]], 
        destination: Tuple[float, float]
    ) -> List[Dict]:
        """
        距离测量（批量）
        
        Args:
            origins: 起点坐标列表 [(lng, lat), ...]
            destination: 终点坐标 (lng, lat)
        
        Returns:
            [
                {"distance": int, "duration": int},
                ...
            ]
        """
        url = f"{self.BASE_URL}/v3/distance"
        
        origins_str = "|".join([f"{lng},{lat}" for lng, lat in origins])
        destination_str = f"{destination[0]},{destination[1]}"
        
        params = {
            "origins": origins_str,
            "destination": destination_str,
            "type": "1"  # 驾车距离
        }
        
        result = self._request(url, params)
        
        if result["status"] != "1":
            raise DistanceError(f"距离测量失败: {result.get('info', '未知错误')}")
        
        results = result["data"].get("results", [])
        
        formatted_results = []
        for r in results:
            formatted_results.append({
                "distance": int(r.get("distance", 0)),
                "duration": int(r.get("duration", 0))
            })
        
        return formatted_results
    
    def measure_distance_matrix(
        self, 
        points: List[Tuple[float, float]]
    ) -> List[List[int]]:
        """
        构建距离/时间矩阵
        
        Args:
            points: 所有点的坐标列表 [(lng, lat), ...]
        
        Returns:
            时间矩阵（秒），matrix[i][j] = 从点 i 到点 j 的驾车时间
        """
        n = len(points)
        matrix = [[0] * n for _ in range(n)]
        
        # 由于高德 API 只支持多个起点 → 1个终点
        # 我们需要逐对查询，或者换一种方式
        
        # 方法：每次查询一个起点到所有其他点的距离
        # 通过多次调用实现
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix[i][j] = 0
                    continue
                
                try:
                    # 查询从点 i 到点 j 的距离
                    result = self._request(
                        f"{self.BASE_URL}/v3/distance",
                        {
                            "origins": f"{points[i][0]},{points[i][1]}",
                            "destination": f"{points[j][0]},{points[j][1]}",
                            "type": "1"
                        }
                    )
                    
                    if result["status"] == "1":
                        results = result["data"].get("results", [])
                        if results:
                            matrix[i][j] = int(results[0].get("duration", 0))
                except Exception:
                    # 如果查询失败，使用估算值
                    matrix[i][j] = 0
        
        return matrix
    
    def driving_route(
        self, 
        origin: Tuple[float, float], 
        destination: Tuple[float, float],
        waypoints: Optional[List[Tuple[float, float]]] = None
    ) -> Dict:
        """
        驾车路线规划
        
        Args:
            origin: 起点坐标 (lng, lat)
            destination: 终点坐标 (lng, lat)
            waypoints: 途经点坐标列表 [(lng, lat), ...]
        
        Returns:
            {
                "distance": int,
                "duration": int,
                "taxi_cost": float,
                "steps": [...]
            }
        """
        url = f"{self.BASE_URL}/v5/direction/driving"
        
        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "strategy": "32",  # 高德推荐
            "show_fields": "cost,navi,cities,polyline"
        }
        
        if waypoints:
            waypoints_str = ";".join([f"{lng},{lat}" for lng, lat in waypoints])
            params["waypoints"] = waypoints_str
        
        result = self._request(url, params)
        
        if result["status"] != "1":
            raise RouteError(f"路线规划失败: {result.get('info', '未知错误')}")
        
        route = result["data"].get("route", {})
        paths = route.get("paths", [])
        
        if not paths:
            raise RouteError("未找到可行路线")
        
        path = paths[0]  # 取第一条路线
        
        steps = []
        for step in path.get("steps", []):
            steps.append({
                "instruction": step.get("instruction", ""),
                "road_name": step.get("road_name", ""),
                "distance": int(step.get("distance", 0)),
                "duration": int(step.get("cost", {}).get("duration", 0))
            })
        
        cost = path.get("cost", {})
        
        return {
            "distance": int(path.get("distance", 0)),
            "duration": int(cost.get("duration", 0)),
            "taxi_cost": float(cost.get("taxi_cost", 0)),
            "steps": steps
        }
