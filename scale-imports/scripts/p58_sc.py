"""P58: IPIP Self-Consciousness (自我意识量表)
Buss (1980), Fenigstein et al. (1975), IPIP proxy
22 items, 5-point scale.
2 dimensions: 私我意识(Private, 10 items), 公我意识(Public, 12 items).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "ipip-self-consciousness"
IMPORT_CODE = "huaxinyun-ipip-self-consciousness"

OPT_NORMAL = [
    ("非常不同意", 1), ("不同意", 2), ("不确定", 3), ("同意", 4), ("非常同意", 5)
]
OPT_REVERSE = [
    ("非常同意", 1), ("同意", 2), ("不确定", 3), ("不同意", 4), ("非常不同意", 5)
]

# 22 items from IPIP Self-Consciousness Scale (Fenigstein et al. 1975 proxy)
# Private Self-Consciousness (items 1-10): awareness of inner feelings/thoughts
# Public Self-Consciousness (items 11-22): awareness of self as seen by others
QUESTIONS_RAW = [
    # Private Self-Consciousness (10 items)
    (1,  "我总是审视自己的内心感受。", False),           # + Am always examining my feelings
    (2,  "我经常注意自己的情绪变化。", False),            # + Notice my moods as they change
    (3,  "我对自己的内在动机感到好奇。", False),          # + Am curious about my inner motives
    (4,  "我经常反思自己的行为。", False),                 # + Reflect on my actions
    (5,  "我很少关注自己的内心想法。", True),              # - Rarely think about myself (R)
    (6,  "我会花时间审视自己的优缺点。", False),           # + Take time to reflect on myself
    (7,  "我对自己的感受有很清楚的认识。", False),         # + Am aware of my feelings
    (8,  "我不太关注自己的内心世界。", True),               # - Am not very introspective (R)
    (9,  "我会分析自己的想法和行为。", False),              # + Analyze my thoughts and behavior
    (10, "我对自己有深入的了解。", False),                  # + Know myself well

    # Public Self-Consciousness (12 items)
    (11, "我很在意别人如何看待我。", False),                # + Care about how I present myself
    (12, "我通常很关注自己的外表。", False),               # + Am concerned about my appearance
    (13, "我在社交场合中会注意自己的言行举止。", False),   # + Monitor my social behavior
    (14, "我在别人面前会感到紧张。", False),                # + Feel nervous when speaking publicly
    (15, "我不太在意别人对我的看法。", True),               # - Don't care what others think (R)
    (16, "我会注意别人对我的反应。", False),                # + Notice how others react to me
    (17, "我经常担心自己给别人留下什么印象。", False),     # + Worry about what impression I make
    (18, "我知道自己在别人眼中是什么样的。", False),        # + Know how I come across to others
    (19, "我在与人交往时会注意自己的表情。", False),        # + Watch my facial expressions
    (20, "我对别人的评价不太敏感。", True),                 # - Am not sensitive to criticism (R)
    (21, "我在穿衣服时很注意形象。", False),                # + Care about how I dress
    (22, "我经常思考别人对我的看法。", False),              # + Think about how others see me
]

# Dimension assignments (0-indexed)
PRIVATE_ITEMS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]      # items 1-10
PUBLIC_ITEMS  = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]  # items 11-22

PRIVATE_ITEMS_1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
PUBLIC_ITEMS_1  = [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_REVERSE if is_rev else OPT_NORMAL
        qs.append(radio_q(order, text, opts))
    return qs

def _mean_formula(items_1indexed):
    parts = " + ".join(f"hx_t_{i}" for i in items_1indexed)
    return f"({parts}) / {len(items_1indexed)}"

def make_dimensions():
    priv_formula = _mean_formula(PRIVATE_ITEMS_1)
    pub_formula = _mean_formula(PUBLIC_ITEMS_1)

    return [
        dimension("私我意识", "private_sc", 1, priv_formula, "", [
            result_rule("hx_wd_y_1 <= 2.0", "私我意识较低",
                "您较少关注自己的内心感受和想法，更倾向于关注外部世界。这可能意味着您比较随性自然，不太会过度思考自己的状态。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.0", "私我意识中等",
                "您对自身内心世界有一定的关注，能够适度地觉察和反思自己的感受和想法。", "none"),
            result_rule("hx_wd_y_1 > 3.0 && hx_wd_y_1 <= 4.0", "私我意识较高",
                "您经常审视和反思自己的内心感受和动机，对自己有较为深入的了解。这种自我觉察有助于个人成长。", "none"),
            result_rule("hx_wd_y_1 > 4.0", "私我意识很高",
                "您非常关注自己的内心世界，经常分析和反思自己的想法与感受。这种高度的自我觉察能力有助于深入了解自己，但也要注意不要过度内省。", "none"),
        ]),
        dimension("公我意识", "public_sc", 2, pub_formula, "", [
            result_rule("hx_wd_y_2 <= 2.0", "公我意识较低",
                "您不太关注别人如何看待自己，在社交场合中比较放松自然，不会过分在意他人评价。", "none"),
            result_rule("hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.0", "公我意识中等",
                "您对他人如何看待自己有一定的关注，在社交场合中能保持适度的自我监控。", "none"),
            result_rule("hx_wd_y_2 > 3.0 && hx_wd_y_2 <= 4.0", "公我意识较高",
                "您比较在意自己的外在形象和别人对您的看法。这有助于您在社交场合中表现得体，但有时可能会感到社交压力。", "none"),
            result_rule("hx_wd_y_2 > 4.0", "公我意识很高",
                "您非常关注自己在他人眼中的形象，对社交反馈很敏感。这种特质使您善于社交管理，但也可能带来社交焦虑。建议适当放松对他人评价的关注。", "low"),
        ]),
    ]

def build():
    return build_scale(
        title="自我意识量表(IPIP-SC)",
        description="本问卷帮助了解您对自身内在感受和外在形象的关注程度。共22题，大约需要4分钟完成。",
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
