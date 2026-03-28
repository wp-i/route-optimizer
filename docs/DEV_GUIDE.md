# Route Optimizer 开发指南

本文档供开发者参考，用于实现 Route Optimizer 项目。

## 项目结构

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
│   └── DEV_GUIDE.md           # 开发指南（本文档）
│
├── README.md                  # 项目说明
├── requirements.txt           # Python 依赖
└── setup.py                   # 安装配置
```

## 开发步骤

### Step 1: 创建项目骨架

```bash
cd D:/code/route-optimizer

# 创建目录结构
mkdir -p core api config skill/scripts mcp tests

# 创建 __init__.py 文件
touch core/__init__.py
touch api/__init__.py
touch config/__init__.py
```

### Step 2: 实现核心模块

按以下顺序实现：

1. **api/exceptions.py** - 定义异常类
2. **api/amap.py** - 高德 API 封装
3. **config/manager.py** - 配置管理
4. **core/parser.py** - 输入解析
5. **core/geocoder.py** - 地理编码
6. **core/fuzzy_searcher.py** - 模糊途经点搜索
7. **core/optimizer.py** - TSP 优化算法
8. **core/router.py** - 路线规划
9. **core/formatter.py** - 结果格式化
10. **core/__init__.py** - 导出主函数

### Step 3: 实现 Skill 版本

1. **skill/SKILL.md** - Skill 定义
2. **skill/scripts/run.py** - 入口脚本

### Step 4: 实现 MCP Server 版本

1. **mcp/server.py** - MCP Server 入口
2. **mcp/pyproject.toml** - 包配置

### Step 5: 测试

```bash
# 运行单元测试
pytest tests/

# 运行集成测试
pytest tests/test_integration.py
```

## 关键实现细节

### 1. TSP 暴力枚举算法

```python
import itertools

def tsp_brute_force(dist_matrix, start_idx, end_idx, waypoint_indices):
    """
    暴力枚举求解 TSP
    
    时间复杂度: O(n!)，n ≤ 8 时可接受
    """
    min_cost = float('inf')
    best_order = None
    
    for perm in itertools.permutations(waypoint_indices):
        path = [start_idx] + list(perm) + [end_idx]
        cost = sum(dist_matrix[path[i]][path[i+1]] for i in range(len(path)-1))
        
        if cost < min_cost:
            min_cost = cost
            best_order = path
    
    return best_order, min_cost
```

### 2. 模糊途经点贪心插入

```python
def insert_fuzzy_waypoint(route_coords, keyword, amap_api):
    """
    贪心策略插入模糊途经点
    
    1. 计算路线几何中点
    2. 在中点附近搜索 POI
    3. 选择绕行最少的候选和位置
    """
    # 几何中点
    midpoint = calc_midpoint(route_coords)
    
    # 搜索 POI
    candidates = amap_api.search_pois(keyword, midpoint, radius=3000)
    
    # 贪心选择最佳
    best_candidate = None
    best_pos = 0
    min_detour = float('inf')
    
    for candidate in candidates[:5]:
        for pos in range(len(route_coords) - 1):
            detour = calc_detour(route_coords, candidate, pos)
            if detour < min_detour:
                min_detour = detour
                best_candidate = candidate
                best_pos = pos
    
    return best_candidate, best_pos, min_detour
```

### 3. API 调用封装模式

```python
import httpx

class AMapAPI:
    BASE_URL = "https://restapi.amap.com"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.Client(timeout=10.0)
    
    def geocode(self, address: str) -> dict:
        url = f"{self.BASE_URL}/v3/geocode/geo"
        params = {"key": self.api_key, "address": address}
        
        response = self.client.get(url, params=params)
        data = response.json()
        
        if data.get("status") != "1":
            raise GeocodeError(f"地理编码失败: {data.get('info')}")
        
        return data["geocodes"][0]
```

## 测试要点

### 单元测试

- TSP 算法正确性（3、5、8 个途经点）
- 输入解析（明确点、模糊点、混合）
- 模糊途经点插入逻辑

### 集成测试

- 完整路线规划流程
- API Key 配置流程
- 错误处理流程

### Mock 数据

测试时需要 Mock 高德 API 响应：

```python
import pytest
from unittest.mock import patch

@pytest.fixture
def mock_amap():
    with patch('api.amap.AMapAPI') as mock:
        mock.return_value.geocode.return_value = {
            "location": "116.397428,39.90923",
            "formatted_address": "北京市东城区天安门"
        }
        yield mock
```

## 常见问题

### Q1: 高德 API 返回 status="0" 怎么办？

检查错误码：
- 10001: API Key 错误
- 10002: 服务不存在
- 10003: 权限不足
- 10004: 请求频率超限

### Q2: 如何处理地址歧义？

高德地理编码可能返回多个结果，应：
1. 取第一个结果
2. 提示用户确认（如果有多个高置信度结果）

### Q3: 模糊途经点搜索无结果怎么办？

1. 扩大搜索半径（3km → 5km）
2. 提示用户更换关键词
3. 允许用户跳过此途经点

## 发布清单

### Skill 版本

- [ ] SKILL.md 编写完成
- [ ] 入口脚本测试通过
- [ ] 打包 zip
- [ ] 发布到 ClawHub

### MCP 版本

- [ ] server.py 测试通过
- [ ] pyproject.toml 配置正确
- [ ] 发布到 npm 或 PyPI
- [ ] 编写使用文档
