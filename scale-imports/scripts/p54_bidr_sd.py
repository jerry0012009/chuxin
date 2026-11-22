"""P54: 自我欺骗量表(BIDR-SD)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "bidr-self-deception"
IMPORT_CODE = "huaxinyun-bidr-self-deception"

OPTIONS = [
    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)
]

QUESTIONS_RAW = [
    (1, "我对自己的判断力很有信心"),
    (2, "我从不后悔自己做过的决定"),
    (3, "我总是能客观地看待自己"),
    (4, "我的第一直觉总是正确的"),
    (5, "我很少对自己的能力产生怀疑"),
    (6, "我对自己的未来充满信心"),
    (7, "我总是能正确地评估形势"),
    (8, "我很少犯判断上的错误"),
    (9, "我的决定总是正确的"),
    (10, "我对自己很满意"),
]

def make_questions():
    return [radio_q(order, text, OPTIONS) for order, text in QUESTIONS_RAW]

def make_dimensions():
    return [
        dimension("自我欺骗", "self_deception", 1, "(hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8 + hx_t_9 + hx_t_10) / 10", "", [
            result_rule("hx_wd_y_1 <= 2.0", "低", "您的自我认知较为客观，较少无意识的正性偏差。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "中", "您的自我欺骗倾向适中。", "none"),
            result_rule("hx_wd_y_1 > 3.5", "高", "您可能存在无意识地过高评价自己的倾向。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="自我欺骗量表(BIDR-SD)",
        description="本问卷帮助了解您是否存在无意识地过高评价自己的倾向。共10题，大约需要2分钟完成。",
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
