"""P81: HSQ 幽默风格量表 (Humor Styles Questionnaire)
Martin et al. (2003), 中文版
32 items, 7-point scale. 4 dimensions: 亲和型幽默/自我提升型幽默/攻击型幽默/自我贬低型幽默.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "hsq"
IMPORT_CODE = "huaxinyun-hsq"

OPT_7 = [
    ("完全不同意", 1), ("比较不同意", 2), ("稍微不同意", 3),
    ("不确定", 4), ("稍微同意", 5), ("比较同意", 6), ("完全同意", 7)
]

# 32 items: (order, text, dimension)
# 亲和型幽默: 1,5,9,13,17,21,25,28
# 自我提升型幽默: 2,6,10,14,18,22,26,30
# 攻击型幽默: 3,7,11,15,19,23,27,31
# 自我贬低型幽默: 4,8,12,16,20,24,28R(28是正向),32
# Note: items 9,15,16,25,29 are reverse-scored in some versions
QUESTIONS_RAW = [
    (1,  "我通常不会和别人开玩笑。", True),
    (2,  "如果我感到难过或不开心，我通常会试着想一些有趣的事情来让自己高兴起来。", False),
    (3,  "如果有人犯了错误，我常常会取笑他们。", False),
    (4,  "我经常让自己成为别人取笑的对象来逗大家开心。", False),
    (5,  "我和周围的人开的玩笑不会伤害到任何人。", False),
    (6,  "当我独自一人感到不开心时，我通常会想一些有趣的事情来让自己感觉好一些。", False),
    (7,  "有时我在讲笑话或说一些有趣的事情时，会不由自主地取笑别人。", False),
    (8,  "我经常用自我贬低的方式来逗大家笑。", False),
    (9,  "我很少讲关于自己好玩的事情来逗大家笑。", True),
    (10, "如果我感到沮丧，我通常会试着想一些有趣的事情来让自己高兴起来。", False),
    (11, "我的幽默常常会让别人感到不舒服或被冒犯。", False),
    (12, "我经常拿自己的弱点、错误或过失开玩笑。", False),
    (13, "我喜欢和别人开玩笑来促进彼此之间的友谊。", False),
    (14, "我善于发现生活中有趣的一面。", False),
    (15, "我不喜欢批评或贬低别人的幽默方式。", True),
    (16, "我很少讲有关自己生活中的趣事。", True),
    (17, "我通常不讲笑话或取笑别人。", True),
    (18, "如果我感到紧张或焦虑，我通常会试着想一些有趣的事情来让自己放松。", False),
    (19, "我常常讲一些笑话来取笑我认识的人。", False),
    (20, "我经常自嘲来让大家觉得好笑。", False),
    (21, "我能用自己的幽默来让大家开心。", False),
    (22, "我从不缺乏幽默感。", False),
    (23, "我从不用幽默来贬低或攻击别人。", True),
    (24, "我经常让别人拿我开玩笑或取笑我。", False),
    (25, "我不怎么开玩笑。", True),
    (26, "如果我感到紧张或焦虑，我会用幽默来让自己开心。", False),
    (27, "我经常用幽默来调侃或取笑别人。", False),
    (28, "当我遇到问题时，我通常不会用幽默来应对。", True),
    (29, "我通常想不到诙谐幽默的事情来说。", True),
    (30, "我经常用幽默来使自己走出低落的情绪。", False),
    (31, "我有时候会拿别人的缺点来开玩笑。", False),
    (32, "我愿意让别人拿我开玩笑，只要能让大家开心。", False),
]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = list(reversed([(l, v) for l, v in OPT_7])) if is_rev else OPT_7
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    # 亲和型幽默: items 1,5,9,13,17,21,25 (reverse: 1,9,17,25)
    aff_items = [1, 5, 9, 13, 17, 21, 25]
    aff_formula = f"({q_range_list(aff_items)}) / {len(aff_items)}"
    # 自我提升型幽默: items 2,6,10,14,18,22,26,30
    sel_items = [2, 6, 10, 14, 18, 22, 26, 30]
    sel_formula = f"({q_range_list(sel_items)}) / {len(sel_items)}"
    # 攻击型幽默: items 3,7,11,15,19,23,27,31 (reverse: 15,23)
    agg_items = [3, 7, 11, 15, 19, 23, 27, 31]
    agg_formula = f"({q_range_list(agg_items)}) / {len(agg_items)}"
    # 自我贬低型幽默: items 4,8,12,16,20,24,28,32 (reverse: 16,28)
    selfd_items = [4, 8, 12, 16, 20, 24, 28, 32]
    selfd_formula = f"({q_range_list(selfd_items)}) / {len(selfd_items)}"

    return [
        dimension("亲和型幽默", "affiliative", 1, aff_formula, "", [
            result_rule("hx_wd_y_1 <= 3.0", "亲和型幽默较低",
                "您较少使用幽默来增进人际关系，在社交场合中不太倾向于用玩笑来拉近与他人的距离。", "none"),
            result_rule("hx_wd_y_1 > 3.0 && hx_wd_y_1 <= 5.0", "亲和型幽默中等",
                "您在社交中适度使用幽默来增进关系，能够在一定程度上用幽默拉近与他人的距离。", "none"),
            result_rule("hx_wd_y_1 > 5.0", "亲和型幽默较高",
                "您善于在社交中使用友善的幽默来增进人际关系，能以温和可接受的方式与他人开玩笑。", "none"),
        ]),
        dimension("自我提升型幽默", "self_enhancing", 2, sel_formula, "", [
            result_rule("hx_wd_y_2 <= 3.0", "自我提升型幽默较低",
                "您较少使用幽默来调节自己的情绪，在面对压力和困境时不太倾向于用幽默来应对。", "none"),
            result_rule("hx_wd_y_2 > 3.0 && hx_wd_y_2 <= 5.0", "自我提升型幽默中等",
                "您在一定程度上能够用幽默来调节自己的情绪，面对困境时偶尔会用幽默来缓解压力。", "none"),
            result_rule("hx_wd_y_2 > 5.0", "自我提升型幽默较高",
                "您善于用幽默来调节情绪和应对压力，面对困境时能以幽默的态度看待生活。", "none"),
        ]),
        dimension("攻击型幽默", "aggressive", 3, agg_formula, "", [
            result_rule("hx_wd_y_3 <= 2.5", "攻击型幽默较低",
                "您很少使用攻击性或讽刺性的幽默来对待他人，人际交往中的幽默方式较为友善。", "none"),
            result_rule("hx_wd_y_3 > 2.5 && hx_wd_y_3 <= 4.5", "攻击型幽默中等",
                "您有时会使用带有攻击性或讽刺性的幽默，需要注意不要无意中伤害到他人。", "none"),
            result_rule("hx_wd_y_3 > 4.5", "攻击型幽默较高",
                "您经常使用攻击性或讽刺性的幽默来对待他人，这种幽默方式可能会影响人际关系。建议适当调整幽默方式。", "none"),
        ]),
        dimension("自我贬低型幽默", "self_defeating", 4, selfd_formula, "", [
            result_rule("hx_wd_y_4 <= 2.5", "自我贬低型幽默较低",
                "您很少通过贬低自己来取悦他人，在人际交往中保持较为积极的自我形象。", "none"),
            result_rule("hx_wd_y_4 > 2.5 && hx_wd_y_4 <= 4.5", "自我贬低型幽默中等",
                "您有时会通过自嘲来逗大家开心，适度的自嘲有助于社交，但需注意不要过度贬低自己。", "none"),
            result_rule("hx_wd_y_4 > 4.5", "自我贬低型幽默较高",
                "您经常通过贬低自己来让别人发笑，这种幽默方式可能反映出较低的自尊水平。建议关注自我价值感的提升。", "none"),
        ]),
    ]

def q_range_list(items):
    return " + ".join(f"hx_t_{i}" for i in items)

def build():
    return build_scale(
        title="幽默风格问卷(HSQ)",
        description="本问卷帮助了解您使用幽默的方式和风格。共32题，大约需要8分钟完成。",
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
