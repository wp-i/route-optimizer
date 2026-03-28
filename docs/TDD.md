# 技术设计文档 (TDD)

## 一、系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户层                                   │
├────────────────────────────┬────────────────────────────────────┤
│      OpenClaw 用户          │         MCP 客户端用户              │
│     (对话式交互)            │        (工具调用)                   │
└─────────────┬──────────────┴─────────────┬──────────────────────┘
              │                            │
              ▼                            ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│    Skill 包装层          │    │    MCP Server 包装层    │
│  (SKILL.md + 脚本调用)   │    │   (MCP 协议 + 工具定义)  │
└─────────────┬───────────┘    └─────────────┬───────────┘
              │                              │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │        核心逻辑层            │
              │  (route_optimizer.core)     │
              ├─────────────────────────────┤
              │  - 输入解析                  │
              │  - 地理编码                  │
              │  - 模糊途经点搜索            │
              │  - TSP 优化                  │
              │  - 路线规划                  │
              │  - 结果格式化                │
              └──────────────┬──────────────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │        API 适配层            │
              │  (route_optimizer.api)      │
              ├─────────────────────────────┤
              │  - 高德地图 API 封装         │
              │  - 请求/响应处理             │
              │  - 错误处理与重试            │
              └──────────────┬──────────────┘
                             │
                             ▼
              ┌─────────────────────────────┐
              │       外部服务               │
              │      高德地图 Web API        │
              └─────────────────────────────┘
```

### 1.2 模块划分

```
route-optimizer/
├── core/                      # 核心逻辑层
│   ├── __init__.py
│   ├── parser.py              # 输入解析
│   ├── geocoder.py            # 地理编码
│   ├── fuzzy_searcher.py      # 模糊途经点搜索
│   ├── optimizer.py           # TSP 优化算法
│   ├── router.py              # 路线规划
│   └── formatter.py           # 结果格式化
│
├── api/                       # API 适配层
│   ├── __init__.py
│   ├── amap.py                # 高德地图 API 封装
│   └── exceptions.py          # 自定义异常
│
├── config/                    # 配置管理
│   ├── __init__.py
│   └── manager.py             # API Key 配置管理
│
├── skill/                     # Skill 版本包装
│   ├── SKILL.md               # Skill 定义文件
│   └── scripts/
│       └── run.py             # Skill 入口脚本
│
├── mcp/                       # MCP Server 版本包装
│   ├── server.py              # MCP Server 入口
│   ├── tools.py               # MCP 工具定义
│   └── pyproject.toml         # Python 包配置
│
├── tests/                     # 测试
│   ├── test_parser.py
│   ├── test_optimizer.py
│   └── test_integration.py
│
├── docs/                      # 文档
│   ├── PRD.md                 # 产品需求文档
│   ├── TDD.md                 # 技术设计文档
│   └── API.md                 # API 文档
│
├── README.md                  # 项目说明
├── requirements.txt           # Python 依赖
└── setup.py                   # 安装配置
```

---

## 二、核心算法设计

### 2.1 整体流程

```
输入: origin, destination, waypoints[]
     waypoints[i] = { type: "explicit" | "fuzzy", name/keyword: string }

     ↓

Step 1: 解析输入
     - 分离明确途经点和模糊途经点
     - 构建途经点列表

     ↓

Step 2: 地理编码（明确点）
     - origin → coords
     - destination → coords
     - 明确途经点[] → coords[]

     ↓

Step 3: 处理模糊途经点
     FOR each 模糊途经点:
         a. 计算当前路线的几何中点
         b. 在中点附近搜索 POI (radius=3km)
         c. 选择距离路线最近的候选
         d. 找到最佳插入位置（贪心）
         e. 插入到路线中

     ↓

Step 4: TSP 优化明确途经点顺序
     - 起点、终点固定
     - 枚举所有途经点排列
     - 计算总耗时，选最优

     ↓

Step 5: 获取详细路线
     - 调用驾车路线规划 API
     - 获取分段导航信息

     ↓

输出: 优化后的路线 + 耗时 + 距离 + 说明
```

### 2.2 TSP 优化算法

**问题定义**：
- 给定起点 S、终点 E、途经点列表 [P1, P2, ..., Pn]
- 求 S → P? → P? → ... → E 的最短耗时路径
- S 和 E 固定，途经点顺序可变

**算法选择**：

| 途经点数量 | 算法 | 时间复杂度 | 说明 |
|-----------|------|-----------|------|
| n ≤ 8 | 暴力枚举 | O(n!) | 保证最优解，n=8 时 40320 种排列 |
| n = 9~10 | 动态规划 | O(n²·2ⁿ) | 可选优化 |

**暴力枚举实现**：

```python
import itertools

def tsp_brute_force(dist_matrix, start_idx, end_idx, waypoint_indices):
    """
    暴力枚举求解 TSP
    
    Args:
        dist_matrix: 距离矩阵，dist_matrix[i][j] 表示点 i 到点 j 的距离/时间
        start_idx: 起点索引
        end_idx: 终点索引
        waypoint_indices: 途经点索引列表
    
    Returns:
        best_order: 最优访问顺序（索引列表）
        min_cost: 最小总耗时
    """
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
    
    return best_order, min_cost
```

### 2.3 模糊途经点处理算法

**贪心策略**：

```
输入: current_route (明确点组成的初始路线), fuzzy_keyword

Step 1: 计算路线几何中点
        midpoint = 几何中心(current_route 所有点的坐标)

Step 2: 在中点附近搜索 POI
        candidates = search_pois(midpoint, fuzzy_keyword, radius=3000)
        # radius: 3km 范围
        
Step 3: 选择最佳候选
        best_candidate = None
        min_detour = infinity
        
        FOR each candidate in candidates[:5]:  # 只取前 5 个候选
            FOR each insertion_pos in [0, 1, ..., len(current_route)-1]:
                # 计算插入此位置的绕行成本
                detour = calc_detour(current_route, candidate, insertion_pos)
                IF detour < min_detour:
                    min_detour = detour
                    best_candidate = candidate
                    best_pos = insertion_pos

Step 4: 插入到路线
        current_route.insert(best_pos, best_candidate)

输出: 更新后的路线
```

**绕行成本计算**：

```python
def calc_detour(route, new_point, insert_pos, dist_matrix):
    """
    计算插入新点到指定位置的绕行成本
    
    Args:
        route: 当前路线（点索引列表）
        new_point: 新点索引
        insert_pos: 插入位置
        dist_matrix: 距离矩阵
    
    Returns:
        detour: 绕行成本（增加的距离/时间）
    """
    # 原始：A → B
    # 插入后：A → new_point → B
    # 绕行 = dist(A, new) + dist(new, B) - dist(A, B)
    
    A = route[insert_pos]
    B = route[insert_pos + 1]
    
    original = dist_matrix[A][B]
    new_path = dist_matrix[A][new_point] + dist_matrix[new_point][B]
    
    return new_path - original
```

### 2.4 距离矩阵构建

```python
def build_distance_matrix(points, api_key):
    """
    构建所有点之间的驾车时间矩阵
    
    Args:
        points: 所有点的坐标列表 [(lng, lat), ...]
        api_key: 高德 API Key
    
    Returns:
        dist_matrix: 时间矩阵（秒），dist_matrix[i][j] = 从点 i 到点 j 的驾车时间
    """
    n = len(points)
    dist_matrix = [[0] * n for _ in range(n)]
    
    # 调用高德距离测量 API（批量）
    # API: https://restapi.amap.com/v3/distance
    # type=1 (驾车距离), origins, destination
    
    for i in range(n):
        # 批量查询从点 i 到所有其他点的距离
        origins = points[i]
        destinations = '|'.join([f"{lng},{lat}" for lng, lat in points])
        
        response = amap_distance_api(origins, destinations, api_key)
        
        for j in range(n):
            dist_matrix[i][j] = response['results'][j]['duration']  # 秒
    
    return dist_matrix
```

---

## 三、API 接口设计

### 3.1 高德地图 API 封装

#### 3.1.1 地理编码

```python
def geocode(address: str, api_key: str) -> dict:
    """
    地址转坐标
    
    API: https://restapi.amap.com/v3/geocode/geo
    
    Args:
        address: 地址字符串
        api_key: 高德 API Key
    
    Returns:
        {
            "lng": float,  # 经度
            "lat": float,  # 纬度
            "formatted_address": str,  # 格式化地址
            "adcode": str   # 区域编码
        }
    
    Raises:
        GeocodeError: 地址解析失败
    """
```

#### 3.1.2 POI 搜索

```python
def search_pois(keyword: str, location: tuple, radius: int, api_key: str) -> list:
    """
    周边搜索 POI
    
    API: https://restapi.amap.com/v3/place/around
    
    Args:
        keyword: 搜索关键词（如"超市"、"加油站"）
        location: 中心点坐标 (lng, lat)
        radius: 搜索半径（米），最大 50000
        api_key: 高德 API Key
    
    Returns:
        [
            {
                "id": str,           # POI ID
                "name": str,         # POI 名称
                "address": str,      # 地址
                "lng": float,        # 经度
                "lat": float,        # 纬度
                "distance": int,     # 距离中心点距离（米）
                "type": str          # POI 类型
            },
            ...
        ]
    
    Raises:
        POISearchError: 搜索失败
    """
```

#### 3.1.3 距离测量

```python
def measure_distance(origins: str, destination: str, api_key: str) -> list:
    """
    距离测量（批量）
    
    API: https://restapi.amap.com/v3/distance
    
    Args:
        origins: 起点坐标，多个用 | 分隔，格式 "lng,lat|lng,lat"
        destination: 终点坐标，格式 "lng,lat"
        api_key: 高德 API Key
    
    Returns:
        [
            {
                "distance": int,  # 距离（米）
                "duration": int,  # 时间（秒）
                "status": str     # 状态
            },
            ...
        ]
    
    Raises:
        DistanceError: 测距失败
    """
```

#### 3.1.4 驾车路线规划

```python
def driving_route(origin: str, destination: str, waypoints: list, api_key: str) -> dict:
    """
    驾车路线规划
    
    API: https://restapi.amap.com/v5/direction/driving
    
    Args:
        origin: 起点坐标 "lng,lat"
        destination: 终点坐标 "lng,lat"
        waypoints: 途经点坐标列表 ["lng,lat", ...]
        api_key: 高德 API Key
    
    Returns:
        {
            "distance": int,      # 总距离（米）
            "duration": int,      # 总时间（秒）
            "taxi_cost": float,   # 预估打车费用
            "steps": [            # 分段信息
                {
                    "instruction": str,   # 导航指令
                    "road_name": str,     # 道路名称
                    "distance": int,      # 分段距离
                    "duration": int,      # 分段时间
                    "polyline": str       # 路线坐标串
                },
                ...
            ]
        }
    
    Raises:
        RouteError: 路线规划失败
    """
```

### 3.2 核心函数接口

```python
def optimize_route(
    origin: str,
    destination: str,
    waypoints: list,
    api_key: str = None
) -> dict:
    """
    路线优化主函数
    
    Args:
        origin: 起点地址或 POI 名称
        destination: 终点地址或 POI 名称
        waypoints: 途经点列表，每个元素格式：
            - 明确途经点：{"type": "explicit", "name": "天安门"}
            - 模糊途经点：{"type": "fuzzy", "keyword": "超市"}
        api_key: 高德 API Key（可选，未提供则从配置读取）
    
    Returns:
        {
            "success": bool,
            "route": [                    # 优化后的路线顺序
                {
                    "name": str,          # 地点名称
                    "address": str,       # 详细地址
                    "lng": float,
                    "lat": float,
                    "type": str,          # "origin" | "destination" | "waypoint_explicit" | "waypoint_fuzzy"
                    "fuzzy_info": {       # 仅模糊途经点有此字段
                        "keyword": str,
                        "reason": str     # 选择理由
                    }
                },
                ...
            ],
            "total_distance": int,        # 总距离（米）
            "total_duration": int,        # 总时间（秒）
            "total_duration_text": str,   # 格式化时间（如 "1小时23分钟"）
            "segments": [                 # 分段信息
                {
                    "from": str,
                    "to": str,
                    "distance": int,
                    "duration": int,
                    "instruction": str
                },
                ...
            ],
            "message": str                # 结果说明
        }
    
    Raises:
        APIKeyError: API Key 无效
        GeocodeError: 地址解析失败
        RouteError: 路线规划失败
    """
```

---

## 四、配置管理设计

### 4.1 Skill 版本配置

**配置文件位置**：`~/.qclaw/route-optimizer-config.json`

```json
{
  "amap_api_key": "xxxxxxxxxx",
  "created_at": "2026-03-28T11:00:00Z",
  "updated_at": "2026-03-28T11:00:00Z"
}
```

**配置管理类**：

```python
class ConfigManager:
    CONFIG_DIR = Path.home() / ".qclaw"
    CONFIG_FILE = CONFIG_DIR / "route-optimizer-config.json"
    
    @classmethod
    def get_api_key(cls) -> str:
        """获取 API Key，未配置返回 None"""
        if not cls.CONFIG_FILE.exists():
            return None
        with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('amap_api_key')
    
    @classmethod
    def set_api_key(cls, api_key: str):
        """保存 API Key"""
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config = {
            "amap_api_key": api_key,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        if cls.CONFIG_FILE.exists():
            with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                old = json.load(f)
                config['created_at'] = old.get('created_at', config['created_at'])
        
        with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # 设置文件权限（仅用户可读写）
        if os.name != 'nt':  # Unix 系统
            os.chmod(cls.CONFIG_FILE, 0o600)
    
    @classmethod
    def mask_api_key(cls, api_key: str) -> str:
        """脱敏显示 API Key"""
        if len(api_key) <= 8:
            return '*' * len(api_key)
        return api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:]
```

### 4.2 MCP 版本配置

MCP 版本通过环境变量配置：

```python
import os

def get_api_key():
    """获取 API Key（优先从环境变量）"""
    return os.environ.get('AMAP_API_KEY')
```

---

## 五、错误处理设计

### 5.1 自定义异常

```python
class RouteOptimizerError(Exception):
    """基础异常"""
    pass

class APIKeyError(RouteOptimizerError):
    """API Key 相关错误"""
    pass

class GeocodeError(RouteOptimizerError):
    """地理编码错误"""
    pass

class POISearchError(RouteOptimizerError):
    """POI 搜索错误"""
    pass

class DistanceError(RouteOptimizerError):
    """距离测量错误"""
    pass

class RouteError(RouteOptimizerError):
    """路线规划错误"""
    pass

class NetworkError(RouteOptimizerError):
    """网络请求错误"""
    pass

class InputError(RouteOptimizerError):
    """输入参数错误"""
    pass
```

### 5.2 错误码映射

| 错误类型 | 用户提示 | 内部处理 |
|---------|---------|---------|
| API Key 无效 | "API Key 无效，请检查或重新配置" | 记录日志，提示重新输入 |
| 地址解析失败 | "地址「{address}」无法识别，请检查或换一个地址" | 记录日志 |
| POI 搜索无结果 | "附近未找到「{keyword}」，建议更换关键词或跳过" | 返回候选列表或提示跳过 |
| 网络超时 | "网络请求超时，正在重试..." | 重试 2 次 |
| 途经点过多 | "途经点不能超过 8 个，请减少后重试" | 直接拒绝 |

---

## 六、Skill 版本实现

### 6.1 SKILL.md

```markdown
---
name: route-optimizer
description: |
  智能路线规划工具。支持多途经点优化（明确地点 + 模糊地点如"超市"）。
  
  使用场景：
  - 用户说 "规划路线"、"最优路线"、"帮我安排行程"
  - 用户提供起点、终点和途经点
  - 途经点可以是明确地点或模糊类型（超市、加油站等）
  
metadata:
  openclaw:
    emoji: "🗺️"
    requires:
      bins:
        - python3
---

# Route Optimizer - 智能路线规划

规划最优驾车路线，支持明确途经点和模糊途经点（如"找个超市"）。

## 快速开始

### 首次使用

首次使用时需要配置高德地图 API Key：

1. 访问 https://console.amap.com 注册账号
2. 创建应用，获取 Web 服务 API Key
3. 告诉我你的 API Key，我会帮你保存

### 使用示例

**基础用法**：
> 帮我规划从北京西站到首都机场的路线

**多途经点**：
> 规划路线：起点北京西站，终点首都机场，途经天安门、鸟巢

**模糊途经点**：
> 从北京西站到首都机场，路上找个超市买点东西

**混合途经点**：
> 起点：北京西站
> 终点：首都机场
> 途经：天安门、鸟巢、找个加油站

## 配置管理

- 查看当前配置：说 "查看我的路线规划配置"
- 修改 API Key：说 "修改高德地图 API Key"

## 注意事项

- 途经点总数不能超过 8 个
- 模糊途经点会在路线中点附近 3km 范围内搜索
- 建议使用具体的地址或 POI 名称以提高准确性
```

### 6.2 入口脚本

```python
#!/usr/bin/env python3
"""
Route Optimizer Skill 入口脚本
"""
import sys
import json
from core import optimize_route, ConfigManager
from api.exceptions import RouteOptimizerError

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "缺少参数"}))
        sys.exit(1)
    
    # 解析输入
    try:
        params = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        print(json.dumps({"error": "参数格式错误"}))
        sys.exit(1)
    
    # 检查配置
    action = params.get('action', 'optimize')
    
    if action == 'config':
        # 配置管理
        sub_action = params.get('sub_action')
        if sub_action == 'get':
            api_key = ConfigManager.get_api_key()
            if api_key:
                print(json.dumps({
                    "configured": True,
                    "masked_key": ConfigManager.mask_api_key(api_key)
                }))
            else:
                print(json.dumps({"configured": False}))
        elif sub_action == 'set':
            api_key = params.get('api_key')
            if api_key:
                ConfigManager.set_api_key(api_key)
                print(json.dumps({"success": True}))
            else:
                print(json.dumps({"error": "缺少 api_key 参数"}))
        return
    
    if action == 'optimize':
        # 路线优化
        api_key = ConfigManager.get_api_key()
        if not api_key:
            print(json.dumps({
                "error": "未配置 API Key",
                "need_config": True,
                "message": "请先配置高德地图 API Key。可访问 https://console.amap.com 免费申请。"
            }))
            return
        
        try:
            result = optimize_route(
                origin=params['origin'],
                destination=params['destination'],
                waypoints=params.get('waypoints', []),
                api_key=api_key
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except RouteOptimizerError as e:
            print(json.dumps({"error": str(e)}))
        except Exception as e:
            print(json.dumps({"error": f"未知错误: {str(e)}"}))

if __name__ == '__main__':
    main()
```

---

## 七、MCP Server 版本实现

### 7.1 server.py

```python
#!/usr/bin/env python3
"""
Route Optimizer MCP Server
"""
import os
import json
from mcp.server import Server
from mcp.types import Tool, TextContent
from core import optimize_route

# 创建 MCP Server 实例
server = Server("route-optimizer")

def get_api_key():
    """从环境变量获取 API Key"""
    api_key = os.environ.get('AMAP_API_KEY')
    if not api_key:
        raise ValueError("未配置 AMAP_API_KEY 环境变量")
    return api_key

@server.list_tools()
async def list_tools():
    """列出可用工具"""
    return [
        Tool(
            name="optimize_route",
            description="优化驾车路线，支持多途经点和模糊途经点（如超市、加油站）",
            inputSchema={
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
                                    "description": "途经点类型：explicit=明确地点，fuzzy=模糊类型"
                                },
                                "name": {
                                    "type": "string",
                                    "description": "明确途经点的名称（type=explicit 时必填）"
                                },
                                "keyword": {
                                    "type": "string",
                                    "description": "模糊途经点的关键词（type=fuzzy 时必填）"
                                }
                            },
                            "required": ["type"]
                        }
                    }
                },
                "required": ["origin", "destination"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """执行工具调用"""
    if name != "optimize_route":
        return [TextContent(type="text", text=f"未知工具: {name}")]
    
    try:
        api_key = get_api_key()
        result = optimize_route(
            origin=arguments['origin'],
            destination=arguments['destination'],
            waypoints=arguments.get('waypoints', []),
            api_key=api_key
        )
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
    except ValueError as e:
        return [TextContent(type="text", text=f"配置错误: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"执行错误: {str(e)}")]

if __name__ == '__main__':
    import asyncio
    asyncio.run(server.run())
```

### 7.2 pyproject.toml

```toml
[project]
name = "route-optimizer-mcp"
version = "0.1.0"
description = "智能路线规划 MCP Server，支持多途经点和模糊途经点"
readme = "README.md"
requires-python = ">=3.8"
license = { text = "MIT" }
authors = [
    { name = "Your Name", email = "your@email.com" }
]

dependencies = [
    "mcp>=0.9.0",
    "httpx>=0.24.0",
]

[project.scripts]
route-optimizer-mcp = "mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## 八、测试设计

### 8.1 单元测试

```python
# tests/test_optimizer.py

import pytest
from core.optimizer import tsp_brute_force

def test_tsp_brute_force_3_points():
    """测试 3 个途经点的 TSP"""
    # 距离矩阵
    # 索引: 0=起点, 1=终点, 2=途经点A, 3=途经点B, 4=途经点C
    dist_matrix = [
        [0, 10, 2, 5, 3],   # 从起点
        [10, 0, 8, 6, 9],   # 从终点
        [2, 8, 0, 4, 3],    # 从A
        [5, 6, 4, 0, 2],    # 从B
        [3, 9, 3, 2, 0],    # 从C
    ]
    
    best_order, min_cost = tsp_brute_force(
        dist_matrix,
        start_idx=0,
        end_idx=1,
        waypoint_indices=[2, 3, 4]
    )
    
    # 验证起点和终点
    assert best_order[0] == 0
    assert best_order[-1] == 1
    # 验证所有途经点都被访问
    assert set(best_order[1:-1]) == {2, 3, 4}

def test_tsp_single_waypoint():
    """测试单个途经点"""
    dist_matrix = [
        [0, 10, 5],
        [10, 0, 6],
        [5, 6, 0],
    ]
    
    best_order, min_cost = tsp_brute_force(
        dist_matrix,
        start_idx=0,
        end_idx=1,
        waypoint_indices=[2]
    )
    
    assert best_order == [0, 2, 1]
    assert min_cost == 5 + 6  # 起点→途经点 + 途经点→终点
```

### 8.2 集成测试

```python
# tests/test_integration.py

import pytest
from core import optimize_route
from api.exceptions import APIKeyError, GeocodeError

@pytest.fixture
def api_key():
    return "test_api_key"

def test_optimize_route_explicit_waypoints(api_key, requests_mock):
    """测试明确途经点路线优化"""
    # Mock API 响应
    requests_mock.get(
        "https://restapi.amap.com/v3/geocode/geo",
        json={"geocodes": [{"location": "116.397428,39.90923", "formatted_address": "北京市东城区天安门"}]}
    )
    requests_mock.get(
        "https://restapi.amap.com/v3/distance",
        json={"results": [{"distance": "5000", "duration": "900"}]}
    )
    requests_mock.get(
        "https://restapi.amap.com/v5/direction/driving",
        json={"route": {"paths": [{"distance": "15000", "duration": "2700"}]}}
    )
    
    result = optimize_route(
        origin="北京西站",
        destination="首都机场",
        waypoints=[
            {"type": "explicit", "name": "天安门"}
        ],
        api_key=api_key
    )
    
    assert result["success"] == True
    assert len(result["route"]) == 3  # 起点 + 途经点 + 终点

def test_optimize_route_invalid_api_key():
    """测试无效 API Key"""
    with pytest.raises(APIKeyError):
        optimize_route(
            origin="北京西站",
            destination="首都机场",
            waypoints=[],
            api_key="invalid_key"
        )
```

---

## 九、性能优化建议

### 9.1 API 调用优化

| 优化点 | 方案 |
|--------|------|
| 距离矩阵 | 批量调用距离测量 API，而非逐对调用 |
| 地理编码 | 并发请求多个地址 |
| 缓存 | 对相同地址的地理编码结果缓存 24 小时 |

### 9.2 算法优化

| 优化点 | 方案 |
|--------|------|
| TSP 求解 | n ≤ 8 暴力足够；n > 8 时考虑 2-opt 局部优化 |
| 模糊途经点 | 限制候选数量（前 5 个），减少计算量 |
| 早停 | 如果贪心解已经足够好（绕行 < 5%），跳过精确求解 |

---

## 十、部署与发布

### 10.1 Skill 发布

```bash
# 打包
cd route-optimizer
zip -r route-optimizer.zip skill/

# 发布到 ClawHub（TODO：具体流程待定）
```

### 10.2 MCP Server 发布

```bash
# 构建
cd route-optimizer/mcp
pip install build
python -m build

# 发布到 npm
npm publish

# 或发布到 PyPI
twine upload dist/*
```

---

## 附录：依赖清单

### requirements.txt

```
httpx>=0.24.0
mcp>=0.9.0
```

### 开发依赖

```
pytest>=7.0.0
pytest-asyncio>=0.21.0
requests-mock>=1.10.0
```
