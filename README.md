# Route Optimizer - 智能路线规划工具

多途经点驾车路线优化工具，支持明确途经点和模糊途经点（如"超市"、"加油站"），输出近似最短耗时路线。

## 产品形态

| 版本 | 目标用户 | 状态 |
|------|---------|------|
| **Skill 版** | OpenClaw 用户 | ✅ 已完成 |
| **MCP Server 版** | Cursor、Claude Desktop 等 | 🚧 待开发 |

## 功能特性

- ✅ 多途经点路线优化（TSP 求解，<10 点）
- ✅ 明确途经点支持（地址/POI 名称）
- ✅ 模糊途经点支持（如"超市"、"加油站"）
- ✅ 贪心算法快速生成可用方案
- ✅ 高德地图 API 支持
- ✅ 交互式 API Key 配置

## 快速开始

### 安装依赖

```bash
cd D:/code/route-optimizer
pip install -r requirements.txt
```

### 配置 API Key

```bash
python skill/scripts/run.py '{"action": "config", "api_key": "你的高德API_KEY"}'
```

### 查看配置状态

```bash
python skill/scripts/run.py '{"action": "status"}'
```

### 规划路线

```bash
# 基础路线
python skill/scripts/run.py '{"action": "optimize", "origin": "北京西站", "destination": "首都机场"}'

# 多途经点
python skill/scripts/run.py '{"action": "optimize", "origin": "北京西站", "destination": "首都机场", "waypoints": [{"type": "explicit", "name": "天安门"}, {"type": "explicit", "name": "鸟巢"}]}'

# 包含模糊途经点
python skill/scripts/run.py '{"action": "optimize", "origin": "北京西站", "destination": "首都机场", "waypoints": [{"type": "fuzzy", "keyword": "超市"}]}'
```

## 项目结构

```
route-optimizer/
├── core/                  # 核心逻辑
│   ├── optimizer.py       # TSP 优化算法
│   └── router.py          # 路线规划主流程
├── api/                   # API 适配层
│   ├── amap.py            # 高德地图 API 封装
│   └── exceptions.py      # 自定义异常
├── config/                # 配置管理
│   └── manager.py         # API Key 配置
├── skill/                 # Skill 版本
│   ├── SKILL.md           # Skill 定义
│   └── scripts/run.py     # 入口脚本
├── docs/                  # 文档
│   ├── PRD.md             # 产品需求文档
│   ├── TDD.md             # 技术设计文档
│   ├── DEV_GUIDE.md       # 开发指南
│   └── API.md             # API 文档
├── README.md
└── requirements.txt
```

## API Key 获取

1. 访问 https://console.amap.com 注册账号
2. 创建应用，选择「Web 服务」
3. 获取 Key 并配置

**免费额度**：个人开发者每日 5000 次调用，足够日常使用。

## 许可证

MIT
