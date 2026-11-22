"""P65: Brief COPE 简明应对方式问卷
Carver (1997), 中文版
28 items, 4-point scale. 14 dimensions (2 items each).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "brief-cope"
IMPORT_CODE = "huaxinyun-brief-cope"

OPT4 = [
    ("从不这样做", 1), ("偶尔这样做", 2), ("有时这样做", 3), ("常常这样做", 4)
]

# 28 items: (order, text)
# 14 dimensions x 2 items each
QUESTIONS_RAW = [
    (1,  "通过工作或参与其他活动令自己不要想太多。", False),
    (2,  "专注努力去解决眼前的困难。", False),
    (3,  "告诉自己：这不是真的。", False),
    (4,  "使用酒精或其他药物令自己好过一点。", False),
    (5,  "从他人获得情绪支援。", False),
    (6,  "放弃处理问题。", False),
    (7,  "采取实际行动去改善现况。", False),
    (8,  "拒绝相信问题已经发生。", False),
    (9,  "以说话释放不愉快的感觉。", False),
    (10, "从他人获得帮助和意见。", False),
    (11, "使用酒精或其他药物去渡过艰难的时刻。", False),
    (12, "尝试换角度去看事情，令它更正面。", False),
    (13, "批评自己。", False),
    (14, "尝试思考一个策略去解决问题。", False),
    (15, "从他人获得安慰和谅解。", False),
    (16, "放弃尝试应付困境。", False),
    (17, "在发生了的问题里寻找正面的东西。", False),
    (18, "拿问题开玩笑。", False),
    (19, "透过某些活动（如阅读、睡觉、看电影、买东西）令自己不要想太多。", False),
    (20, "接受问题已经发生的事实。", False),
    (21, "抒发负面情绪。", False),
    (22, "在宗教信仰里寻找安慰。", False),
    (23, "尝试寻求他人的帮助或建议去解决问题。", False),
    (24, "学习与问题共存。", False),
    (25, "努力思考接下来采取哪些步骤。", False),
    (26, "为已发生的事情责怪自己。", False),
    (27, "祈祷或沉思。", False),
    (28, "嘲笑现况。", False),
]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        qs.append(radio_q(order, text, OPT4))
    return qs

def make_dimensions():
    # 14 dimensions, each with 2 items
    dims = [
        ("自我分心", "self_distraction", 1, [1, 19]),
        ("积极应对", "active_coping", 2, [2, 7]),
        ("否认", "denial", 3, [3, 8]),
        ("物质使用", "substance_use", 4, [4, 11]),
        ("情感支持", "emotional_support", 5, [5, 15]),
        ("行为脱离", "behavioral_disengagement", 6, [6, 16]),
        ("工具性支持", "instrumental_support", 7, [10, 23]),
        ("积极重构", "positive_reframing", 8, [12, 17]),
        ("自我责备", "self_blame", 9, [13, 26]),
        ("计划", "planning", 10, [14, 25]),
        ("幽默", "humor", 11, [18, 28]),
        ("接纳", "acceptance", 12, [20, 24]),
        ("情绪宣泄", "venting", 13, [9, 21]),
        ("宗教", "religion", 14, [22, 27]),
    ]
    result = []
    for name, code, num, items in dims:
        formula = f"(hx_t_{items[0]} + hx_t_{items[1]}) / 2"
        result.append(dimension(name, code, num, formula, "", [
            result_rule(f"hx_wd_y_{num} <= 1.5", "使用频率很低",
                f"您在压力情境下很少使用「{name}」这一应对策略。", "none"),
            result_rule(f"hx_wd_y_{num} > 1.5 && hx_wd_y_{num} <= 2.5", "使用频率较低",
                f"您偶尔会使用「{name}」这一应对策略。", "none"),
            result_rule(f"hx_wd_y_{num} > 2.5 && hx_wd_y_{num} <= 3.5", "使用频率中等",
                f"您有时会使用「{name}」这一应对策略。", "none"),
            result_rule(f"hx_wd_y_{num} > 3.5", "使用频率较高",
                f"您经常使用「{name}」这一应对策略。", "none"),
        ]))
    return result

def build():
    return build_scale(
        title="简明应对方式问卷(Brief COPE)",
        description="本问卷帮助了解您在面对压力时常用的应对方式。共28题，大约需要10分钟完成。",
        code=SCALE_CODE,
        questions=make_questions(),
        dimensions=make_dimensions(),
    )

if __name__ == "__main__":
    scale = build()
    json_path = os.path.join(os.path.dirname(__file__), "..", "json", f"{SCALE_CODE}.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(scale, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON saved: {json_path}")
    print(f"   Questions: {len(scale['questions'])}")
    print(f"   Dimensions: {len(scale['dimensions'])}")

    print("\n--- Dry Run ---")
    result = import_scale(scale, dry_run=True, publish=True)
    print(f"   Importable: {result.get('importable', 0)}")
    print(f"   Publishable: {result.get('publishable', 0)}")
    for item in result.get("items", []):
        print(f"   {item.get('title')}: {item.get('action')} | issues={item.get('issues')} | warnings={item.get('warnings')}")

    print("\n--- Importing ---")
    result = import_scale(scale, dry_run=False, publish=True, overwrite=True)
    print(f"   Imported: {result.get('imported', 0)}")
    print(f"   Updated: {result.get('updated', 0)}")
    for item in result.get("items", []):
        print(f"   {item.get('title')}: {item.get('action')} | id={item.get('survey_id', 'N/A')}")

    print("\n--- DB Verify ---")
    print(verify_in_db(IMPORT_CODE))
