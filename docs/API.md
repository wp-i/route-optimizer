# Route Optimizer API 文档

本文档描述 Route Optimizer 的核心 API 接口。

## 核心函数

### optimize_route()

路线优化主函数。

**签名**：

```python
def optimize_route(
    origin: str,
    destination: str,
    waypoints: list = None,
    api_key: str = None
) -> dict
```

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| origin | str | 是 | 起点地址或 POI 名称 |
| destination | str | 是 | 终点地址或 POI 名称 |
| waypoints | list | 否 | 途经点列表，最多 8 个 |
| api_key | str | 否 | 高德 API Key，未提供则从配置读取 |

**途经点格式**：

```python
# 明确途经点
{
    "type": "explicit",
    "name": "天安门"  # 地址或 POI 名称
}

# 模糊途经点
{
    "type": "fuzzy",
    "keyword": "超市"  # POI 类型关键词
}
```

**返回值**：

```python
{
    "success": True,
    "route": [
        {
            "name": "北京西站",
            "address": "北京市丰台区莲花池东路118号",
            "lng": 116.322056,
            "lat": 39.893554,
            "type": "origin"
        },
        {
            "name": "天安门",
            "address": "北京市东城区东长安街",
            "lng": 116.397456,
            "lat": 39.909187,
            "type": "waypoint_explicit"
        },
        {
            "name": "华联超市(慧忠路店)",
            "address": "北京市朝阳区慧忠路",
            "lng": 116.391234,
            "lat": 40.001234,
            "type": "waypoint_fuzzy",
            "fuzzy_info": {
                "keyword": "超市",
                "reason": "位于鸟巢附近，绕行约 3 分钟"
            }
        },
        {
            "name": "首都机场T3航站楼",
            "address": "北京市顺义区首都国际机场",
            "lng": 116.610033,
            "lat": 40.079895,
            "type": "destination"
        }
    ],
    "total_distance": 45000,
    "total_duration": 3480,
    "total_duration_text": "58 分钟",
    "segments": [
        {
            "from": "北京西站",
            "to": "天安门",
            "distance": 8000,
            "duration": 900,
            "instruction": "从起点向正东方向出发..."
        },
        {
            "from": "天安门",
            "to": "华联超市(慧忠路店)",
            "distance": 12000,
            "duration": 1200,
            "instruction": "沿东长安街行驶..."
        },
        {
            "from": "华联超市(慧忠路店)",
            "to": "首都机场T3航站楼",
            "distance": 25000,
            "duration": 1380,
            "instruction": "沿机场高速行驶..."
        }
    ],
    "message": "已优化路线顺序，包含 1 个模糊途经点"
}
```

**异常**：

| 异常类型 | 说明 |
|---------|------|
| APIKeyError | API Key 无效或未配置 |
| GeocodeError | 地址解析失败 |
| POISearchError | POI 搜索失败或无结果 |
| RouteError | 路线规划失败 |
| InputError | 输入参数无效 |

**示例**：

```python
from route_optimizer import optimize_route

# 基础用法
result = optimize_route(
    origin="北京西站",
    destination="首都机场"
)

# 多途经点
result = optimize_route(
    origin="北京西站",
    destination="首都机场",
    waypoints=[
        {"type": "explicit", "name": "天安门"},
        {"type": "explicit", "name": "鸟巢"},
        {"type": "fuzzy", "keyword": "超市"}
    ]
)
```

---

## 配置管理 API

### ConfigManager.get_api_key()

获取已保存的 API Key。

**返回值**：

- `str`: API Key（已配置）
- `None`: 未配置

**示例**：

```python
from route_optimizer.config import ConfigManager

api_key = ConfigManager.get_api_key()
if api_key:
    print(f"已配置 API Key: {ConfigManager.mask_api_key(api_key)}")
else:
    print("未配置 API Key")
```

### ConfigManager.set_api_key()

保存 API Key。

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| api_key | str | 高德地图 API Key |

**示例**：

```python
from route_optimizer.config import ConfigManager

ConfigManager.set_api_key("your_api_key_here")
print("API Key 已保存")
```

### ConfigManager.mask_api_key()

脱敏显示 API Key。

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| api_key | str | 原始 API Key |

**返回值**：

- `str`: 脱敏后的 API Key（如 "abcd****efgh"）

**示例**：

```python
masked = ConfigManager.mask_api_key("abcdefgh12345678")
print(masked)  # 输出: abcd****5678
```

---

## 高德地图 API 封装

### AMapAPI.geocode()

地址转坐标。

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| address | str | 地址字符串 |

**返回值**：

```python
{
    "location": "116.397428,39.90923",
    "formatted_address": "北京市东城区天安门",
    "adcode": "110101"
}
```

### AMapAPI.search_pois()

周边搜索 POI。

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| keyword | str | 搜索关键词 |
| location | tuple | 中心点坐标 (lng, lat) |
| radius | int | 搜索半径（米），默认 3000 |

**返回值**：

```python
[
    {
        "id": "B000A7BD6C",
        "name": "华联超市",
        "address": "北京市朝阳区慧忠路",
        "location": "116.391234,40.001234",
        "distance": 500
    },
    ...
]
```

### AMapAPI.measure_distance()

距离测量（批量）。

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| origins | str | 起点坐标，多个用 `\|` 分隔 |
| destination | str | 终点坐标 |

**返回值**：

```python
[
    {"distance": "5000", "duration": "900"},
    {"distance": "8000", "duration": "1200"},
    ...
]
```

### AMapAPI.driving_route()

驾车路线规划。

**参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| origin | str | 起点坐标 "lng,lat" |
| destination | str | 终点坐标 "lng,lat" |
| waypoints | list | 途经点坐标列表 |

**返回值**：

```python
{
    "distance": 45000,
    "duration": 3480,
    "taxi_cost": 120.5,
    "steps": [
        {
            "instruction": "从起点向正东方向出发...",
            "road_name": "莲花池东路",
            "distance": 8000,
            "duration": 900
        },
        ...
    ]
}
```

---

## MCP Server 工具定义

### optimize_route (MCP Tool)

**工具名称**：`optimize_route`

**描述**：优化驾车路线，支持多途经点和模糊途经点（如超市、加油站）。

**输入 Schema**：

```json
{
    "type": "object",
    "properties": {
        "origin": {
            "type": "string",
            "description": "起点地址或 POI 名称"
        },
        "destination": {
            "type": "string",
            "description": "终点地址或 POI 名称"
        },
        "waypoints": {
            "type": "array",
            "description": "途经点列表",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["explicit", "fuzzy"],
                        "description": "途经点类型"
                    },
                    "name": {
                        "type": "string",
                        "description": "明确途经点的名称"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "模糊途经点的关键词"
                    }
                },
                "required": ["type"]
            }
        }
    },
    "required": ["origin", "destination"]
}
```

**配置方式**：

```json
{
    "mcpServers": {
        "route-optimizer": {
            "command": "npx",
            "args": ["-y", "route-optimizer-mcp"],
            "env": {
                "AMAP_API_KEY": "your_api_key_here"
            }
        }
    }
}
```
