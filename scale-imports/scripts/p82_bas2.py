"""P82: BAS-2 身体欣赏量表 (Body Appreciation Scale-2)
Tylka & Wood-Barcalow (2015), 中文版 Ma et al. (2022)
10 items, 5-point scale. Single dimension: 身体欣赏.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "bas2"
IMPORT_CODE = "huaxinyun-bas2"

OPT_5 = [
    ("从不", 1), ("很少", 2), ("有时", 3), ("经常", 4), ("总是", 5)
]

QUESTIONS_RAW = [
    (1,  "我尊重自己的身体。", False),
    (2,  "我对自己的身体感觉良好。", False),
    (3,  "我觉得我的身体至少有一些优点。", False),
    (4,  "我对自己的身体持积极态度。", False),
    (5,  "我关注自己身体的需求。", False),
    (6,  "我爱自己的身体。", False),
    (7,  "我欣赏自己身体的不同和独特之处。", False),
    (8,  "我的行为透露出我对自己身体的积极态度（例如，昂首挺胸、面带微笑）。", False),
    (9,  "我对自己的身体感到舒适。", False),
    (10, "我觉得自己是美丽的，即使我与媒体上的魅力人物形象不同。", False),
]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        qs.append(radio_q(order, text, OPT_5))
    return qs

def make_dimensions():
    formula = q_range(1, 10) + " / 10"
    return [
        dimension("身体欣赏", "body_appreciation", 1, formula, "", [
            result_rule("hx_wd_y_1 <= 2.0", "身体欣赏水平较低",
                "您对身体的积极感受较低，可能对自己的身体形象存在较多不满。建议尝试关注身体的功能和能力，而非外表。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "身体欣赏水平中等",
                "您对自己的身体持有一定的积极态度，但仍有提升空间。建议进一步培养对身体的感恩和欣赏。", "none"),
            result_rule("hx_wd_y_1 > 3.5", "身体欣赏水平较高",
                "您对自己的身体持有积极的态度和情感，能够欣赏和尊重自己的身体。这种积极的身体意象有助于整体心理健康。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="身体欣赏量表-2(BAS-2)",
        description="本量表帮助了解您对自己身体的积极态度和感受。共10题，大约需要2分钟完成。",
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
