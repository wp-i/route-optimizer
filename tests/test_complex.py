"""
复杂用户口语化输入测试 - 修正版
正确构造参数：环形起点=终点，途经点在中间
"""
import sys
import json
import time
sys.path.insert(0, 'D:/code/route-optimizer')
from core import optimize_route, recommend_nearby

# 修正测试用例：明确起点终点和途经点
TEST_CASES = [
    {
        "id": "COMPLEX-01",
        "user_input": "我5月3号到5月5号去淮安玩，入住如家商旅酒店（淮安周恩来纪念馆河下古镇店），想吃小龙虾，还想去周恩来纪念馆逛逛",
        # 酒店就是纪念馆附近，所以起点=终点=纪念馆，途经点是小龙虾
        "origin": "淮安周恩来纪念馆",
        "destination": "淮安周恩来纪念馆", 
        "waypoints": [{"type": "fuzzy", "keyword": "小龙虾"}],
    },
    {
        "id": "COMPLEX-02", 
        "user_input": "周末两天北京游，第一天早上看天安门升旗，然后去故宫，中午想吃北京烤鸭，下午去天坛",
        # 第一天：天安门看升旗，然后故宫，然后烤鸭，然后天坛，最后回天安门（假设住附近）
        "origin": "天安门",
        "destination": "天安门",
        "waypoints": [
            {"type": "explicit", "name": "故宫"},
            {"type": "fuzzy", "keyword": "烤鸭"},
            {"type": "explicit", "name": "天坛"}
        ],
    },
    {
        "id": "COMPLEX-03",
        "user_input": "陪爸妈去苏州玩，他们说必须去拙政园和寒山寺，我自己想吃顿好的，求推荐正宗的苏帮菜，环境要好点",
        "origin": "拙政园",
        "destination": "寒山寺",
        "waypoints": [{"type": "fuzzy", "keyword": "苏帮菜"}],
    },
    {
        "id": "COMPLEX-04",
        "user_input": "五一去成都三天，想看大熊猫基地、武侯祠，还要吃火锅，最好是那种本地人常去的正宗火锅，不要网红店",
        "origin": "大熊猫繁育研究基地",
        "destination": "武侯祠",
        "waypoints": [{"type": "fuzzy", "keyword": "火锅"}],
    },
    {
        "id": "COMPLEX-05",
        "user_input": "下午四点半从公司（国贸）出发，去首都机场接个人，然后去万达吃个晚饭，最后回家",
        # 简化：国贸→机场→万达（暂不考虑回家，因为需要用户补充家的地址）
        "origin": "国贸",
        "destination": "万达",
        "waypoints": [{"type": "explicit", "name": "首都机场"}],
    },
    {
        "id": "COMPLEX-06",
        "user_input": "早上八点从家出发，去奥森跑步，跑完回家洗个澡，然后去公司开会",
        # 简化：奥森→公司（暂不考虑回家那段）
        "origin": "奥林匹克公园",
        "destination": "国贸",
        "waypoints": [],
    },
    {
        "id": "COMPLEX-07",
        "user_input": "去西安玩三天，主要去兵马俑、华清池，还有回民街吃小吃，晚上想看长恨歌演出",
        "origin": "秦始皇兵马俑博物馆",
        "destination": "钟楼",
        "waypoints": [
            {"type": "fuzzy", "keyword": "华清池"},
            {"type": "fuzzy", "keyword": "回民街"},
            {"type": "fuzzy", "keyword": "长恨歌"}
        ],
    },
    {
        "id": "COMPLEX-08",
        "user_input": "下午到广州白云机场，晚上想去珠江夜游，第二天去长隆野生动物世界玩一整天",
        "origin": "广州白云国际机场",
        "destination": "长隆野生动物世界",
        "waypoints": [{"type": "fuzzy", "keyword": "珠江夜游"}],
    },
    {
        "id": "COMPLEX-09",
        "user_input": "我从南京开车去杭州，路上想在服务区休息一下，到了之后去西湖边上的知味观吃午饭，然后去灵隐寺",
        # 用户已到杭州，西湖→灵隐寺
        "origin": "西湖",
        "destination": "灵隐寺",
        "waypoints": [{"type": "fuzzy", "keyword": "知味观"}],
    },
    {
        "id": "COMPLEX-10",
        "user_input": "三天两夜上海游，想去外滩、田子坊，还要看东方明珠，晚上去酒吧街逛逛，再找个正宗本帮菜吃吃",
        # 外滩开始，最后回到外滩
        "origin": "外滩",
        "destination": "外滩",
        "waypoints": [
            {"type": "explicit", "name": "东方明珠"},
            {"type": "explicit", "name": "田子坊"},
            {"type": "fuzzy", "keyword": "酒吧街"},
            {"type": "fuzzy", "keyword": "本帮菜"}
        ],
    }
]

results = []

for tc in TEST_CASES:
    print("\n" + "="*60)
    print(f"[{tc['id']}] {tc['user_input'][:45]}...")
    t0 = time.time()
    
    try:
        result = optimize_route(
            origin=tc["origin"],
            destination=tc["destination"],
            waypoints=tc["waypoints"]
        )
        elapsed = time.time() - t0
        
        if result.get("success"):
            route = result["route"]
            n_points = len(route)
            names = [p["name"] for p in route]
            dist = result.get("total_distance", 0)  # 米
            dist_km = dist / 1000
            dur = result.get("total_duration_text", "")
            skipped = result.get("skipped_waypoints", [])
            
            # 生成推荐
            recs = recommend_nearby(result) if n_points >= 2 else None
            rec_count = len(recs.get("recommendations", [])) if recs and recs.get("success") else 0
            
            print(f"  [OK] {n_points}点, {dist_km:.1f}km, {dur}, {rec_count}推荐")
            print(f"  路线: {' -> '.join(names[:6])}")
            if skipped:
                print(f"  跳过: {', '.join(s['name'] for s in skipped)}")
            
            # 检查距离是否合理（北京上海同城应该<50km）
            is_reasonable = True
            if dist_km > 200 and n_points <= 5:
                is_reasonable = False
                print(f"  [WARN] 距离异常: {dist_km:.1f}km")
            
            status = "PASS" if is_reasonable else "FAIL"
            actual = f"success=True, {n_points}点, {dist_km:.1f}km, {dur}, {rec_count}推荐"
        else:
            print(f"  [FAIL] {result.get('error')}")
            status = "FAIL"
            actual = f"fail: {result.get('error')}"
            dist_km = 0
            rec_count = 0
        
        results.append({
            "id": tc["id"],
            "user_input": tc["user_input"],
            "origin": tc["origin"],
            "destination": tc["destination"],
            "waypoints": ", ".join(w.get("keyword", w.get("name")) for w in tc["waypoints"]),
            "actual": actual,
            "status": status,
            "elapsed_s": round(elapsed, 1),
            "distance_km": round(dist_km, 1),
            "rec_count": rec_count
        })
        
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  [ERROR] {e}")
        results.append({
            "id": tc["id"],
            "user_input": tc["user_input"],
            "status": "ERROR",
            "actual": f"exception: {str(e)}",
            "elapsed_s": round(elapsed, 1)
        })

# 保存结果
with open("D:/code/route-optimizer/tests/complex_test_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

passed = sum(1 for r in results if r.get("status") == "PASS")
print("\n" + "="*60)
print(f"总计: {passed}/{len(results)} 通过")
print("结果已保存")