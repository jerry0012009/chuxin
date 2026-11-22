"""P56: 完美主义量表(OCD-P)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "ocd-perfectionism"
IMPORT_CODE = "huaxinyun-ocd-perfectionism"

OPTIONS = [
    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)
]

QUESTIONS_RAW = [
    (1, "我觉得事情必须做得完美才满意"),
    (2, "我很难容忍自己犯错"),
    (3, "我对自己有非常高的标准"),
    (4, "我会反复检查自己的工作直到满意"),
    (5, "我经常觉得自己做得不够好"),
    (6, "我会花很多时间确保事情做到最好"),
    (7, "我很难接受不完美的结果"),
    (8, "我会因为追求完美而拖延"),
    (9, "我对细节有近乎苛刻的要求"),
    (10, "我经常因为达不到自己的标准而沮丧"),
]

def make_questions():
    return [radio_q(order, text, OPTIONS) for order, text in QUESTIONS_RAW]

def make_dimensions():
    return [
        dimension("完美主义", "perfectionism", 1, "(hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8 + hx_t_9 + hx_t_10) / 10", "", [
            result_rule("hx_wd_y_1 <= 2.0", "低", "您的完美主义倾向较低，能接受不完美的结果。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "中", "您的完美主义倾向适中。", "none"),
            result_rule("hx_wd_y_1 > 3.5", "高", "您有较强的完美主义倾向，对自己要求很高，可能因此感到压力。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="完美主义量表(OCD-P)",
        description="本问卷帮助了解您是否存在完美主义倾向或难以控制的反复想法。共10题，大约需要2分钟完成。",
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
