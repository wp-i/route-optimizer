# 🗺️ Route Optimizer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org)

智能路线规划工具。基于高德地图 API，支持多途经点 TSP 自动优化——无论是明确的目的地还是模糊的搜索词（"找个超市"），都能自动算出最优路线顺序。

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **TSP 自动优化** | 多途经点自动枚举排列，选耗时最短顺序 |
| **模糊途经点** | "找个超市" → 自动在路线附近匹配最合适的门店 |
| **城市上下文** | 知名地点（如"故宫"）自动限定城市，避免匹配到同名异地 |
| **往返路线** | 起点=终点，自动识别并规划环形路线 |
| **多端可用** | Python SDK / OpenClaw Skill / MCP Server |

---

## 快速开始

```bash
# 安装依赖
pip install httpx

# Python 调用
python examples/basic.py
```

## 快速调用示例

```python
from core import optimize_route

result = optimize_route(
    origin='天安门',
    destination='天坛',
    waypoints=[
        {'type': 'explicit', 'name': '故宫'},
        {'type': 'fuzzy', 'keyword': '超市'},
    ]
)

if result['success']:
    for p in result['route']:
        print(p['name'], p['address'][:20])
    print('总耗时:', result['total_duration_text'])
```

---

## 算法说明

- **明确途经点**：TSP 暴力枚举（≤8 个途经点 → ≤40320 种排列，毫秒级）
- **模糊途经点**：路线几何中点 → POI 搜索 → 贪心最小绕行位置插入
- **地理编码**：带城市上下文的高德地理编码 API，提高知名地点准确率

---

## 项目结构

```
route-optimizer/
├── core/               # 核心算法
│   ├── optimizer.py    # TSP 暴力枚举 + 几何中点
│   └── router.py       # 路线规划主流程
├── api/               # 高德 API 封装
│   └── amap.py
├── config/            # API Key 配置
│   └── manager.py
├── skill/             # OpenClaw Skill
│   ├── SKILL.md
│   └── scripts/run.py
├── examples/          # 示例代码
│   ├── basic.py       # 基础路线规划
│   ├── fuzzy.py        # 模糊途经点
│   └── roundtrip.py    # 往返路线
├── tests/             # 单元测试（pytest）
│   ├── test_optimizer.py
│   └── test_config.py
└── docs/              # 需求文档
    ├── PRD.md
    └── DEV_GUIDE.md
```

---

## 运行测试

```bash
pytest tests/ -v
```

---

## 申请高德 API Key

1. 打开 [https://console.amap.com](https://console.amap.com)
2. 注册 → 登录 → 完成实名认证
3. 「应用管理」→「我的应用」→「创建新应用」
4. 添加 Key，**服务平台选「Web服务」**
5. 每日免费额度：5000 次调用

---

## License

MIT
