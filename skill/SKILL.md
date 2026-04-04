---
name: route-optimizer
description: |
  智能路线规划 + 周边推荐工具。支持 TSP 自动优化、模糊地点搜索、附近景点/商场/公园推荐。
  
  使用场景：
  - 用户说"规划路线"、"最优路线"、"帮我安排行程"
  - 用户说"去XX旅游，想吃XX，看看XX"
  - 需要推荐附近景点、商场、公园、博物馆
  - 途经点可以是明确地点（餐厅名）或模糊类型（超市、公园等）
  
  关键词：路线规划, 导航, 行程, 怎么走, 从哪到哪, TSP, 推荐, 附近有什么
  
metadata:
  openclaw:
    emoji: "🗺️"
    requires:
      bins:
        - python3
---

# Route Optimizer - 智能路线规划 + 周边推荐

规划最优驾车路线，自动搜索附近景点/商场/公园/博物馆，输出精简路线图和推荐内容组。

---

## 首次使用：配置 API Key

**首次使用时若未配置 API Key，AI 会提示你申请并输入。**

### 快速申请步骤

1. 打开 [https://console.amap.com](https://console.amap.com)
2. 注册 → 登录 → 完成实名认证
3. 「应用管理」→「我的应用」→「创建新应用」
4. 应用名称填 `路线规划`，「添加 Key」
5. **服务平台选「Web服务」**（不是 Web 端/JS API），提交
6. 把 Key 发给 AI：`我的高德 API Key 是：XXXXXX`

> 个人开发者每日 **5000 次**免费调用，足够日常使用。

---

## 自然语言参数提取规则（核心）

当用户提出行程需求时，AI 必须先从输入中提取结构化参数。

### 关键原则

1. **用户说"去XX城市" = 假设已到达该城市，在市内规划路线**
2. **起点终点可以是不同地点**（支持 A→B→C 单向，也支持 A→B→C→A 环形）
3. **AI 应主动补充用户未明确但合理的途经点**（如用户给两个相邻餐厅，可提示距离）

### 参数提取

| 参数 | 提取方式 | 示例 |
|------|---------|------|
| **origin** | 行程出发点，用户说"入住XX"则 origin=XX | `周恩来纪念馆` |
| **destination** | 行程终点，未明确时 origin=destination | `王府井` |
| **waypoints** | 用户明确要去的地方 | 见下 |

### 途经点类型

| 类型 | 判断 | 格式 |
|------|------|------|
| 明确途经点 | 用户给了具体店名/地名 | `{"type": "explicit", "name": "南门涮肉"}` |
| 模糊途经点 | 用户只说了类型/品类 | `{"type": "fuzzy", "keyword": "小龙虾"}` |

### 提取示例

```
用户：我打算5.3-5.5去淮安，入住如家商旅酒店(淮安周恩来纪念馆河下古镇店)，
     打算吃点小龙虾，去趟纪念馆
```

```json
{
  "origin": "淮安周恩来纪念馆",
  "destination": "淮安周恩来纪念馆",
  "waypoints": [
    {"type": "fuzzy", "keyword": "小龙虾"}
  ],
  "recommend_categories": ["旅游景点", "公园广场", "购物中心", "博物馆"]
}
```

```
用户：陪爸妈去苏州玩，他们想去拙政园和寒山寺，我自己想吃苏帮菜
```

```json
{
  "origin": "拙政园",
  "destination": "寒山寺",
  "waypoints": [
    {"type": "fuzzy", "keyword": "苏帮菜"}
  ],
  "recommend_categories": ["旅游景点", "公园广场", "购物中心", "博物馆"]
}
```

---

## 调用方式

提取参数后，调用 Python API：

```python
import sys
sys.path.insert(0, 'skills/route-optimizer')
from core import optimize_route, recommend_nearby, format_route_output

# 1. 路线规划
result = optimize_route(
    origin="天安门",
    destination="王府井",
    waypoints=[
        {"type": "explicit", "name": "故宫"},
        {"type": "fuzzy", "keyword": "烤鸭"}
    ]
)

# 2. 生成推荐（基于路线结果）
recommendations = recommend_nearby(
    result,
    categories=["旅游景点", "公园广场", "购物中心", "博物馆"],
    radius=5000,
    per_point_limit=3
)

# 3. 格式化输出（精简路线图 + 推荐内容组）
output = format_route_output(result, recommendations)
print(output)
```

配置 API Key：

```python
from core import configure_api_key
configure_api_key("你的高德API_Key")
```

---

## 输出格式

### 精简路线图

```
========================================
  精简路线图
========================================

  [起] 天安门
      长安街北侧
      -> 下站: 北京烤鸭(南池子1号店) (11 分钟, ~904m)

  [2] 北京烤鸭(南池子1号店)
      南池子大街...
      -> 下站: 故宫博物院 (10 分钟, ~1.2km)

  [3] 故宫博物院
      景山前街4号
      -> 下站: 王府井 (41 分钟, ~2.6km)

  [终] 王府井

  总距离: 11.0 公里 | 总耗时: 1 小时 2 分钟
```

### 推荐内容组

```
========================================
  推荐内容组
========================================

  [景点]
    - 太庙街门 (83m, 在天安门附近)
    - 中国国家博物馆 (536m, 在天安门附近)

  [公园]
    - 中山公园 (126m, 在天安门附近)
    - 升旗台 (251m, 在天安门附近)

  [商场]
    - 王府中环 (1.1km, 在天安门附近)

  [博物馆]
    - 中国国家博物馆 (536m, 在天安门附近)
    - 中国警察博物馆 (704m, 在天安门附近)
```

---

## 场景示例

### 场景 1：旅游城市一日游

```
用户：周末去北京玩，天安门看升旗，故宫必去，想吃烤鸭

AI 行为：
1. 提取参数：origin=天安门, destination=王府井, waypoints=[故宫, 烤鸭(模糊)]
2. 调用 optimize_route → 获得最优路线
3. 调用 recommend_nearby → 推荐景点/公园/商场/博物馆
4. 调用 format_route_output → 输出精简路线图 + 推荐内容组
5. 用自然语言给用户行程建议（如"升旗建议早上看，先安排故宫..."
```

### 场景 2：跨城自驾（到达后规划）

```
用户：从南京开车去杭州，到西湖边上的知味观吃午饭，然后去灵隐寺

AI 行为：
1. origin=西湖, destination=灵隐寺（不规划南京→杭州段，只在杭州内规划）
2. 调用路线 + 推荐
3. 输出路线图 + 杭州周边推荐
```

### 场景 3：商务出差

```
用户：下午四点从国贸出发，去机场接人，然后去万达吃晚饭

AI 行为：
1. origin=国贸, destination=首都机场（单向路线）
2. 规划路线
3. 推荐国贸和机场附近的商场/餐厅
```

### 场景 4：环形路线

```
用户：入住如家酒店(河下古镇店)，吃小龙虾，去纪念馆

AI 行为：
1. origin=destination=周恩来纪念馆（环形路线，酒店就在旁边）
2. 调用路线 + 推荐
3. 推荐淮安周边景点（中国漕运博物馆、河下古镇等）
```

---

## API 参考

### optimize_route(origin, destination, waypoints, api_key)

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| origin | str | ✅ | 起点 |
| destination | str | ✅ | 终点（可与 origin 相同=环形） |
| waypoints | list[dict] | 否 | 途经点，最多 8 个 |
| api_key | str | 否 | 不传则从配置读取 |

返回值：`{success, route[], segments[], total_distance, total_duration, skipped_waypoints[], message}`

### recommend_nearby(route_result, categories, radius, per_point_limit, api_key)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| route_result | dict | - | optimize_route 的返回值 |
| categories | list[str] | ["旅游景点","公园广场","购物中心","博物馆"] | 推荐分类 |
| radius | int | 5000 | 搜索半径（米） |
| per_point_limit | int | 3 | 每个路线点每类最多推荐数 |

返回值：`{success, recommendations[{near, category, items[]}]}`

### format_route_output(route_result, recommendations)

格式化为用户可读文本（精简路线图 + 推荐内容组），返回 str。

---

## 限制

| 限制 | 说明 |
|------|------|
| 途经点数量 | 最多 8 个（明确 + 模糊合计） |
| 推荐范围 | 路线点周围 5km（可调） |
| API 调用 | 高德 Web 服务 API，每日 5000 次免费 |
| Python 版本 | 3.8+ |
| 网络 | 需要互联网连接 |
| 路线类型 | 单城市路线规划（跨城市长距离可能失败） |
