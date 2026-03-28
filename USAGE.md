# Route Optimizer 使用说明

## 安装

```bash
cd D:/code/route-optimizer
pip install httpx
```

## 配置 API Key

你需要先获取高德地图 API Key：

1. 访问 https://console.amap.com 注册账号
2. 创建应用，选择「Web 服务」类型
3. 获取 Key

配置方式：

```bash
# 方式 1：命令行配置
python -c "from core import configure_api_key; configure_api_key('你的API_KEY')"

# 方式 2：运行测试脚本时输入
python test.py
```

配置文件保存位置：`~/.qclaw/route-optimizer-config.json`

## 使用方式

### 命令行使用

```bash
# 查看配置状态
python skill/scripts/run.py "{\"action\": \"status\"}"

# 简单路线规划
python skill/scripts/run.py "{\"action\": \"optimize\", \"origin\": \"北京西站\", \"destination\": \"首都机场\"}"

# 多途经点
python skill/scripts/run.py "{\"action\": \"optimize\", \"origin\": \"北京西站\", \"destination\": \"首都机场\", \"waypoints\": [{\"type\": \"explicit\", \"name\": \"天安门\"}, {\"type\": \"explicit\", \"name\": \"鸟巢\"}]}"
```

### Python 代码调用

```python
from core import optimize_route

# 简单路线
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
        {"type": "fuzzy", "keyword": "超市"}  # 模糊途经点
    ]
)

print(result)
```

### 在 OpenClaw 中使用

将 `skill/` 目录复制到你的 OpenClaw skills 目录，然后在对话中说：

> 帮我规划从北京西站到首都机场的路线，途经天安门、鸟巢，路上找个超市

## 输出示例

```json
{
  "success": true,
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
      "type": "waypoint"
    },
    {
      "name": "华联超市(慧忠路店)",
      "address": "北京市朝阳区慧忠路",
      "lng": 116.391234,
      "lat": 40.001234,
      "type": "waypoint_fuzzy",
      "fuzzy_info": {
        "keyword": "超市",
        "reason": "在路线中点附近找到，已插入到路线中"
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
  "total_duration_text": "58 分钟",
  "total_distance_text": "45.0 公里",
  "message": "已优化路线，总耗时约 58 分钟。包含 1 个模糊途经点：超市"
}
```

## 注意事项

1. **API 额度**：个人开发者免费额度为每日 5000 次调用
2. **途经点限制**：最多 8 个途经点（明确 + 模糊）
3. **模糊途经点搜索范围**：路线中点附近 5km
4. **编码**：Windows 命令行可能显示乱码，建议使用 PowerShell 或配置 UTF-8

## 故障排查

### 问题：API Key 无效

```
检查项：
1. 是否选择「Web 服务」类型
2. API Key 是否正确复制（无多余空格）
3. 账号是否已完成实名认证
```

### 问题：地址解析失败

```
建议：
1. 使用更具体的地址（如「北京市朝阳区XX路XX号」）
2. 使用 POI 名称（如「天安门」、「鸟巢」）
3. 避免使用缩写或模糊描述
```

### 问题：搜索不到模糊途经点

```
建议：
1. 换一个关键词（如「便利店」代替「超市」）
2. 使用明确的 POI 名称
3. 确认该区域确实有此类设施
```
