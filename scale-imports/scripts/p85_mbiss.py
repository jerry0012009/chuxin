"""P85: MBI-SS 学生学业倦怠量表 (Maslach Burnout Inventory-Student Survey)
Schaufeli et al. (2002), 中文版
15 items, 7-point scale. 3 dimensions: 犬儒主义/耗竭/效能感.
效能感 dimension is reverse-scored.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "mbiss"
IMPORT_CODE = "huaxinyun-mbiss"

OPT_7 = [
    ("从不", 0), ("极少(一年几次或更少)", 1), ("偶尔(一个月一次或更少)", 2),
    ("经常(一个月几次)", 3), ("频繁(每星期一次)", 4),
    ("非常频繁(一星期几次)", 5), ("每天", 6)
]

# 犬儒主义(cynicism): 1,2,3,4,5
# 耗竭(exhaustion): 6,7,8,9,10
# 效能感(efficacy): 11,12,13,14,15 (reverse)
QUESTIONS_RAW = [
    # 犬儒主义
    (1,  "我对学习感到厌倦。", False),
    (2,  "我对学习的热情减少了。", False),
    (3,  "我对所学的东西越来越不感兴趣。", False),
    (4,  "我对自己所学的内容持怀疑态度。", False),
    (5,  "我觉得学习对我而言毫无意义。", False),
    # 耗竭
    (6,  "学习让我感到身心俱疲。", False),
    (7,  "一天的学习结束后，我感到精疲力竭。", False),
    (8,  "早上起床后又要面对一整天的学习，我感到很累。", False),
    (9,  "持续学习一整天对我来说压力很大。", False),
    (10, "学习让我有快要崩溃的感觉。", False),
    # 效能感 (reverse scored)
    (11, "在学习中，我能有效地解决问题。", True),
    (12, "我觉得我的学习是有价值的。", True),
    (13, "我对学习感兴趣。", True),
    (14, "在学习时，我感到精力充沛。", True),
    (15, "在学习中，我感到自信。", True),
]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = list(reversed([(l, v) for l, v in OPT_7])) if is_rev else OPT_7
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    cyn_items = [1, 2, 3, 4, 5]
    cyn_formula = f"({q_range_list(cyn_items)}) / {len(cyn_items)}"
    exh_items = [6, 7, 8, 9, 10]
    exh_formula = f"({q_range_list(exh_items)}) / {len(exh_items)}"
    eff_items = [11, 12, 13, 14, 15]
    eff_formula = f"({q_range_list(eff_items)}) / {len(eff_items)}"

    return [
        dimension("犬儒主义", "cynicism", 1, cyn_formula, "", [
            result_rule("hx_wd_y_1 <= 2.0", "犬儒主义较低",
                "您对学习保持较好的热情和兴趣，较少出现消极和冷漠的态度。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 4.0", "犬儒主义中等",
                "您对学习出现一定程度的消极和疏离感，可能会感到学习缺乏意义。建议寻找学习中的乐趣和意义。", "none"),
            result_rule("hx_wd_y_1 > 4.0", "犬儒主义较高",
                "您对学习表现出较强的冷漠和消极态度，可能会感到学习毫无意义。建议与老师或辅导员交流，重新激发学习热情。", "none"),
        ]),
        dimension("耗竭", "exhaustion", 2, exh_formula, "", [
            result_rule("hx_wd_y_2 <= 2.0", "耗竭感较低",
                "您在学习中较少感到疲惫和精力耗尽，能够保持较好的身心状态。", "none"),
            result_rule("hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 4.0", "耗竭感中等",
                "您在学习中会出现一定程度的疲惫感，建议注意劳逸结合，合理安排学习和休息时间。", "none"),
            result_rule("hx_wd_y_2 > 4.0", "耗竭感较高",
                "您在学习中感到严重的身心疲惫和精力耗尽。建议适当减轻学习负担，增加休息和放松活动。", "none"),
        ]),
        dimension("效能感", "efficacy", 3, eff_formula, "", [
            result_rule("hx_wd_y_3 <= 2.0", "效能感较低",
                "您对自己在学习中的能力和价值感到较低，可能缺乏学习的信心。建议设定小目标，逐步建立学习自信。", "none"),
            result_rule("hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 4.0", "效能感中等",
                "您对自己在学习中的能力和价值有一定的认识，但仍有提升空间。", "none"),
            result_rule("hx_wd_y_3 > 4.0", "效能感较高",
                "您对自己的学习能力有较高的信心，认为学习是有价值和意义的。这有助于保持良好的学习动力。", "none"),
        ]),
    ]

def q_range_list(items):
    return " + ".join(f"hx_t_{i}" for i in items)

def build():
    return build_scale(
        title="学生学业倦怠量表(MBI-SS)",
        description="本量表帮助了解您在学习中的身心状态。共15题，大约需要3分钟完成。",
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
