"""P2-25: NCS-6 - Need for Cognition Scale, short (Cacioppo, Petty & Kao, 1984; 6-item short form)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "ncs6-cognition"
IMPORT_CODE = "huaxinyun-ncs6-cognition"

# NCS-6: 6 items, 5-point Likert (1=strongly disagree to 5=strongly agree)
# Reverse items: 2, 4, 6
# Score: mean of all 6 items (range 1-5). Norms: ~3.5 general population.
REVERSE_ITEMS = {2, 4, 6}

QUESTIONS = [
    (1, "比起简单的问题，我更喜欢复杂的问题。"),
    (2, "我喜欢不需要太多思考的任务。"),
    (3, "思考对我来说是一种乐趣。"),
    (4, "我倾向于避免需要深入思考的活动。"),
    (5, "我喜欢思考用新的方式来解决问题。"),
    (6, "完成一项需要思考的任务后，我会感到如释重负。"),
]

def make_questions():
    qs = []
    for order, text in QUESTIONS:
        if order in REVERSE_ITEMS:
            opts = [("非常不同意", 5), ("不同意", 4), ("不确定", 3), ("同意", 2), ("非常同意", 1)]
        else:
            opts = [("非常不同意", 1), ("不同意", 2), ("不确定", 3), ("同意", 4), ("非常同意", 5)]
        qs.append(radio_q(order, text, opts))
    return qs

def make_dimensions():
    total_items = " + ".join(f"hx_t_{i}" for i in range(1, 7))
    return [
        dimension("认知需求", "ncs_total", 1, f"({total_items}) / 6", "", [
            result_rule("hx_wd_y_1 <= 2.0", "认知需求较低", "您的认知需求得分较低，表明您不太倾向于主动寻求和享受需要思考的活动。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.0", "认知需求中等偏低", "您的认知需求处于中等偏低水平，对需要思考的活动态度一般。", "none"),
            result_rule("hx_wd_y_1 > 3.0 && hx_wd_y_1 <= 4.0", "认知需求中等", "您的认知需求处于中等水平，表明您在一定程度上享受思考和解决复杂问题。", "none"),
            result_rule("hx_wd_y_1 > 4.0 && hx_wd_y_1 <= 5.0", "认知需求较高", "您的认知需求得分较高，表明您喜欢思考，享受解决复杂问题的过程。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="认知需求量表短版(NCS-6)",
        description="本问卷帮助了解您对需要思考的活动的态度和偏好。共6题，大约需要2分钟完成。",
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
