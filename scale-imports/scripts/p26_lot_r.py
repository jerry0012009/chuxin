"""P2-26: LOT-R - Life Orientation Test-Revised (Scheier, Carver & Bridges, 1994)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "lotr-optimism"
IMPORT_CODE = "huaxinyun-lotr-optimism"

# LOT-R: 10 items, 5-point (0=strongly disagree to 4=strongly agree)
# Optimism items: 3, 7, 9 (direct scoring, NOT reversed)
# Pessimism items: 4, 5, 6, 8 (reverse scored: 4 - value)
# Fillers: 1, 2, 10 (do not count)
# Score = optimism(3+7+9) + reverse_pessimism(4+5+6+8). Range 0-24.
# Thresholds: 0-10 pessimistic, 11-15 moderate, 16-24 optimistic.
P_REVERSE = {4, 5, 6, 8}
SCORED_ITEMS = {3, 4, 5, 6, 7, 8, 9}

QUESTIONS = [
    # Fillers (1, 2, 10) - not scored
    (1, "在不确定的时候，我通常会期望最好的结果。"),
    (2, "对我来说，保持忙碌是很重要的。"),
    # Optimism items (3, 7, 9) - direct scoring
    (3, "我总是对自己的未来持乐观态度。"),
    # Pessimism items (4, 5, 6, 8) - reverse coded
    (4, "如果我认为某件事情会出错，那它通常确实会出错。"),
    (5, "我很少指望好事会发生在我身上。"),
    (6, "我总是预期最坏的结果。"),
    (7, "总的来说，我期望更多好事而不是坏事发生在我身上。"),
    (8, "事情很少按照我的意愿发展。"),
    (9, "在大多数情况下，事情的结果都比我预期的好。"),
    # Filler
    (10, "我很容易放松。"),
]

def make_questions():
    qs = []
    for order, text in QUESTIONS:
        if order in P_REVERSE:
            # Pessimism items: reverse coded (4-original)
            opts = [
                ("非常不同意", 4), ("不同意", 3), ("不确定", 2), ("同意", 1), ("非常同意", 0)
            ]
        else:
            # Direct scoring (optimism items and fillers)
            opts = [
                ("非常不同意", 0), ("不同意", 1), ("不确定", 2), ("同意", 3), ("非常同意", 4)
            ]
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    # After reverse coding in options, sum all scored items
    scored_formula = " + ".join(f"hx_t_{i}" for i in sorted(SCORED_ITEMS))
    optimism_items = " + ".join(f"hx_t_{i}" for i in [3, 7, 9])
    pessimism_items = " + ".join(f"hx_t_{i}" for i in [4, 5, 6, 8])

    return [
        dimension("乐观", "optimism", 1, f"{optimism_items}", "", [
            result_rule("hx_wd_y_1 <= 4", "乐观倾向较低", "您的乐观得分较低，对未来积极事件的期望偏低。", "none"),
            result_rule("hx_wd_y_1 > 4 && hx_wd_y_1 <= 8", "乐观倾向中等", "您的乐观得分处于中等水平。", "none"),
            result_rule("hx_wd_y_1 > 8 && hx_wd_y_1 <= 12", "乐观倾向较高", "您的乐观得分较高，对未来抱有积极期望。", "none"),
        ]),
        dimension("悲观", "pessimism", 2, f"{pessimism_items}", "", [
            result_rule("hx_wd_y_2 <= 4", "悲观倾向较低", "您的悲观得分较低，较少预期消极结果。", "none"),
            result_rule("hx_wd_y_2 > 4 && hx_wd_y_2 <= 8", "悲观倾向中等", "您的悲观得分处于中等水平。", "none"),
            result_rule("hx_wd_y_2 > 8", "悲观倾向较高", "您的悲观得分较高，倾向于预期消极结果，建议关注心理健康。", "low"),
        ]),
        dimension("总分", "total", 3, scored_formula, "", [
            result_rule("hx_wd_y_3 <= 10", "悲观倾向", "您的LOT-R总分较低（0-10），整体倾向于悲观。建议关注自身心态，培养积极的思维方式。", "low"),
            result_rule("hx_wd_y_3 > 10 && hx_wd_y_3 <= 15", "中等水平", "您的LOT-R总分处于中等范围（11-15），乐观与悲观倾向较为平衡。", "none"),
            result_rule("hx_wd_y_3 > 15 && hx_wd_y_3 <= 24", "乐观倾向", "您的LOT-R总分较高（16-24），整体倾向于乐观，对未来持积极态度。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="生活取向测验修订版(LOT-R)",
        description="本问卷帮助了解您对未来的态度是倾向于乐观还是悲观。共10题，大约需要2分钟完成。",
        code=SCALE_CODE,
        questions=make_questions(),
        dimensions=make_dimensions(),
        survey_type="basic",
    )

if __name__ == "__main__":
    scale = build()
    json_path = os.path.join(os.path.dirname(__file__), "..", "json", f"{SCALE_CODE}.json")
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
