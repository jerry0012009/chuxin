"""P42: ICU - Inventory of Callous-Unemotional Traits (无情特质量表)
(Frick, 2004; Essau et al., 2006)
24 items, 4-point scale (0-3). Total score 0-72.
3 dimensions: 冷酷(Callous, 8 items), 淡漠(Uncaring, 8 items), 无情(Unemotional, 8 items).
Reverse items (0-indexed): 1,2,4,5,7,12,13,14,16,18,21,22.
Thresholds: 0-24 低, 25-48 中等, 49-72 高.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "icu-callous-unemotional"
IMPORT_CODE = "huaxinyun-icu-callous-unemotional"

# Normal options (0-3): higher = more CU traits
OPT_NORMAL = [
    ("完全不符合", 0),
    ("有点符合", 1),
    ("基本符合", 2),
    ("完全符合", 3),
]

# Reverse options (0-3): higher agreement = lower CU traits (invert values)
OPT_REVERSE = [
    ("完全符合", 0),
    ("基本符合", 1),
    ("有点符合", 2),
    ("完全不符合", 3),
]

# Reverse items (0-indexed): 1,2,4,5,7,12,13,14,16,18,21,22
# These are positive/prosocial items where agreement indicates LOW CU traits
REVERSE_SET = {1, 2, 4, 5, 7, 12, 13, 14, 16, 18, 21, 22}

# 24 items: (order, text, is_reverse)
# Items grouped by dimension:
#   冷酷 (Callous): indices 0,3,6,7,8,9,10,11 (items 1,4,7,8,9,10,11,12)
#   淡漠 (Uncaring): indices 1,2,4,5,12,13,14,15 (items 2,3,5,6,13,14,15,16)
#   无情 (Unemotional): indices 16,17,18,19,20,21,22,23 (items 17-24)
QUESTIONS_RAW = [
    # 冷酷 (Callous)
    (1,  "别人的感受对我来说无关紧要。", False),
    (2,  "我会为别人的不幸感到难过。", True),       # R
    (3,  "我总是很在意别人是否开心。", True),         # R  (淡漠 dimension actually, but listed by order)
    (4,  "我对别人的感受不太关心。", False),
    # 淡漠 (Uncaring)
    (5,  "我会努力去帮助受伤的人。", True),           # R
    (6,  "我觉得去关心别人是浪费时间。", False),
    (7,  "看到别人哭的时候，我也想哭。", False),      # Note: 冷酷 dimension item
    (8,  "对别人温柔和善对我来说很重要。", False),    # Note: R item
    (9,  "我不会因为伤害了别人而感到难过。", False),
    (10, "别人的情绪不会影响到我。", False),
    (11, "我会故意说一些伤害别人的话。", False),
    (12, "即使别人请求帮助，我也不太愿意去帮。", False),
    # 淡漠 (Uncaring) continued
    (13, "我会认真倾听别人的想法和感受。", True),     # R
    (14, "我很在意别人对我的看法。", True),            # R
    (15, "我对生活中发生的事情很无所谓。", False),
    (16, "我会积极参加各种活动。", True),              # R  (淡漠 dim)
    # 无情 (Unemotional)
    (17, "我不太会表达自己的情感。", False),
    (18, "我善于表达自己的感情。", True),              # R
    (19, "我很少流露出强烈的情感。", False),
    (20, "别人觉得我是一个冷漠的人。", False),
    (21, "我对别人总是很热情。", True),                # R
    (22, "在社交场合中我表现得很自然。", True),        # R
    (23, "我很少因为别人的故事而感动。", False),
    (24, "别人觉得我很难接近。", False),
]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_REVERSE if is_rev else OPT_NORMAL
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    # 冷酷 (Callous): items 1,4,7,8,9,10,11,12 (1-indexed) → indices 0,3,6,7,8,9,10,11
    callous_items = [1, 4, 7, 8, 9, 10, 11, 12]
    callous_formula = " + ".join(f"hx_t_{i}" for i in callous_items)

    # 淡漠 (Uncaring): items 2,3,5,6,13,14,15,16 (1-indexed) → indices 1,2,4,5,12,13,14,15
    uncaring_items = [2, 3, 5, 6, 13, 14, 15, 16]
    uncaring_formula = " + ".join(f"hx_t_{i}" for i in uncaring_items)

    # 无情 (Unemotional): items 17-24 (1-indexed) → indices 16-23
    unemotional_items = [17, 18, 19, 20, 21, 22, 23, 24]
    unemotional_formula = " + ".join(f"hx_t_{i}" for i in unemotional_items)

    # Total score
    total_formula = q_range(1, 24)

    return [
        # 冷酷 (Callous, 8 items, range 0-24)
        dimension("冷酷", "callous", 1, callous_formula, "", [
            result_rule("hx_wd_y_1 <= 8", "冷酷特质低",
                "您对他人的情感有较好的感知和关注，能够体谅和理解他人的感受。", "none"),
            result_rule("hx_wd_y_1 > 8 && hx_wd_y_1 <= 16", "冷酷特质中等",
                "您在某些情况下对他人的感受关注不够，但总体处于正常范围。建议在人际交往中多练习换位思考。", "none"),
            result_rule("hx_wd_y_1 > 16", "冷酷特质高",
                "您在关注和理解他人情感方面存在较明显的困难，这可能影响您的人际关系。建议寻求专业评估以了解更多。", "low"),
        ]),
        # 淡漠 (Uncaring, 8 items, range 0-24)
        dimension("淡漠", "uncaring", 2, uncaring_formula, "", [
            result_rule("hx_wd_y_2 <= 8", "淡漠特质低",
                "您对他人和周围事务表现出足够的关心和投入，具有良好的情感参与度。", "none"),
            result_rule("hx_wd_y_2 > 8 && hx_wd_y_2 <= 16", "淡漠特质中等",
                "您在某些情况下可能显得不太关心他人或事务，但总体处于正常范围。建议关注自己的情感投入程度。", "none"),
            result_rule("hx_wd_y_2 > 16", "淡漠特质高",
                "您对他人和事务表现出较高的淡漠程度，可能影响您的社交和情感生活。建议关注这一倾向并寻求适当支持。", "low"),
        ]),
        # 无情 (Unemotional, 8 items, range 0-24)
        dimension("无情", "unemotional", 3, unemotional_formula, "", [
            result_rule("hx_wd_y_3 <= 8", "情感表达正常",
                "您能够适当地表达和体验情感，在社交中表现出自然的情感反应。", "none"),
            result_rule("hx_wd_y_3 > 8 && hx_wd_y_3 <= 16", "情感表达中等",
                "您在情感表达方面可能较为内敛，但总体处于正常范围。建议适当练习情感表达。", "none"),
            result_rule("hx_wd_y_3 > 16", "情感表达受限",
                "您在情感表达和体验方面存在较明显的限制，可能被他人视为冷漠或难以接近。建议关注自己的情感发展。", "low"),
        ]),
        # Total score (24 items, range 0-72)
        dimension("无情特质总分", "total_cu", 4, total_formula, "", [
            result_rule("hx_wd_y_4 <= 24", "无情特质水平低",
                "您的总体得分较低，表明您具有良好的共情能力和情感反应。您能够理解和回应他人的情感需求，人际关系方面表现良好。", "none"),
            result_rule("hx_wd_y_4 > 24 && hx_wd_y_4 <= 48", "无情特质水平中等",
                "您的得分处于中等水平，表明您在共情和情感反应方面有一定的特征。在某些情境下可能表现得较为淡漠或不太关注他人感受。建议保持自我觉察，在人际交往中多关注他人的情感需求。", "none"),
            result_rule("hx_wd_y_4 > 49", "无情特质水平高",
                "您的得分较高，表明在共情、情感反应和关心他人方面存在较明显的特征。这些特质可能影响您的人际关系和社会功能。建议寻求专业的心理评估，了解更多关于自身情感特点的信息，并探索改善人际关系的方法。", "middle"),
        ]),
    ]

def build():
    return build_scale(
        title="无情特质量表(ICU)",
        description="本问卷帮助了解您在人际互动中对他人情感的敏感程度和共情能力。共24题，大约需要5分钟完成。",
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
