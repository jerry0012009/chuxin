"""P1-16: ELS - Ethical Leadership Scale (Brown, 2005)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "els-ethical-leadership"
IMPORT_CODE = "huaxinyun-els-ethical-leadership"

# ELS: 10 items, 5-point Likert (1=strongly disagree to 5=strongly agree)
# Single dimension, mean 1-5

QUESTIONS = [
    (1, "我的上级会倾听员工的意见和建议。"),
    (2, "我的上级会惩罚违反道德标准的员工。"),
    (3, "我的上级在日常生活中会树立道德行为的榜样。"),
    (4, "我的上级会将员工的最大利益放在心上。"),
    (5, "我的上级会做出公平公正的决策。"),
    (6, "我的上级在做业务决策时会考虑道德规范。"),
    (7, "我的上级会明确说明哪些行为被视为违反道德。"),
    (8, "我的上级在与员工沟通时会表现出诚实和正直。"),
    (9, "我的上级会重新定义成功，不仅包括结果，还包括实现结果的方式。"),
    (10, "我的上级在做决定时会认真考虑道德方面的后果。"),
]

LIKERT_5_OPTIONS = [
    ("非常不同意", 1), ("不同意", 2), ("不确定", 3), ("同意", 4), ("非常同意", 5)
]

def make_questions():
    return [radio_q(order, text, LIKERT_5_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    # Single dimension: mean of all 10 items
    all_items = " + ".join(f"hx_t_{i}" for i in range(1, 11))
    total_formula = f"({all_items}) / 10"

    return [
        dimension("道德领导", "ethical_leadership", 1, total_formula, "", [
            result_rule("hx_wd_y_1 <= 2.0", "道德领导感知较低", "您对上级道德领导的感知较低，建议关注领导与员工之间的沟通和信任建设。", "low"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.0", "道德领导感知中等", "您对上级道德领导的感知处于中等水平。", "none"),
            result_rule("hx_wd_y_1 > 3.0 && hx_wd_y_1 <= 4.0", "道德领导感知较高", "您认为上级在道德领导方面表现较好。", "none"),
            result_rule("hx_wd_y_1 > 4.0", "道德领导感知很高", "您对上级的道德领导有很高的评价，表明上级在道德方面树立了良好榜样。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="道德领导量表(ELS)",
        description="本问卷帮助了解您对上级领导行为的感受，包括领导者的道德示范和公平对待等方面。共10题，大约需要3分钟完成。",
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
