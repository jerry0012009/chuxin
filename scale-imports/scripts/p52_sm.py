"""P52: 自我监控量表(SM)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "self-monitoring"
IMPORT_CODE = "huaxinyun-self-monitoring"

OPTIONS = [
    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)
]

QUESTIONS_RAW = [
    (1, "我善于根据不同的社交场合调整自己的行为"),
    (2, "在不同的人面前我会表现得不一样"),
    (3, "我能够根据场合改变自己的形象"),
    (4, "我在社交中善于察言观色"),
    (5, "我会根据对方的反应调整自己的言行"),
    (6, "我善于在不同场合展现不同的自己"),
    (7, "我能够很好地掩饰自己的真实感受"),
    (8, "我善于读懂社交情境中的潜规则"),
    (9, "我会根据周围人的期望来调整自己"),
    (10, "我在与不同类型的人交往时表现不同"),
]

def make_questions():
    return [radio_q(order, text, OPTIONS) for order, text in QUESTIONS_RAW]

def make_dimensions():
    return [
        dimension("自我监控", "self_monitoring", 1, "(hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8 + hx_t_9 + hx_t_10) / 10", "", [
            result_rule("hx_wd_y_1 <= 2.0", "低", "您的自我监控能力较低，倾向于在不同场合保持一致的自我表现。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "中", "您的自我监控能力适中。", "none"),
            result_rule("hx_wd_y_1 > 3.5", "高", "您善于根据社交场合调整自己的言行举止，社交适应能力强。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="自我监控量表(SM)",
        description="本问卷帮助了解您在社交场合中调整自己言行举止的能力。共10题，大约需要2分钟完成。",
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
