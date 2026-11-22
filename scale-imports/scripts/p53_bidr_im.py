"""P53: 印象管理量表(BIDR-IM)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "bidr-impression-management"
IMPORT_CODE = "huaxinyun-bidr-impression-management"

OPTIONS = [
    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)
]

QUESTIONS_RAW = [
    (1, "我从来没有说过谎话"),
    (2, "我总是遵守交通规则"),
    (3, "我从来没有在背后说过别人的坏话"),
    (4, "我总是按时完成所有工作"),
    (5, "我从来没有迟到过"),
    (6, "我对每个人都很友善"),
    (7, "我从来没有有过不好的想法"),
    (8, "我总是做正确的事情"),
    (9, "我从来没有有过不道德的行为"),
    (10, "我总是诚实地回答所有问题"),
    (11, "我从来没有利用过别人"),
    (12, "我总是对自己的行为负责"),
    (13, "我从来没有违反过规则"),
    (14, "我总是考虑别人的感受"),
    (15, "我从来没有对人生过气"),
    (16, "我总是帮助有需要的人"),
    (17, "我从来没有撒过小谎"),
    (18, "我总是尊重每一个人"),
    (19, "我从来没有偷看过别人的东西"),
    (20, "我做事总是问心无愧"),
]

def make_questions():
    return [radio_q(order, text, OPTIONS) for order, text in QUESTIONS_RAW]

def make_dimensions():
    return [
        dimension("印象管理", "impression_management", 1, "(hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8 + hx_t_9 + hx_t_10 + hx_t_11 + hx_t_12 + hx_t_13 + hx_t_14 + hx_t_15 + hx_t_16 + hx_t_17 + hx_t_18 + hx_t_19 + hx_t_20) / 20", "", [
            result_rule("hx_wd_y_1 <= 2.0", "低", "您在回答问题时较为坦诚，不太刻意美化自己。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "中", "您的印象管理倾向适中。", "none"),
            result_rule("hx_wd_y_1 > 3.5", "高", "您在回答问题时倾向于呈现理想化的自我形象，可能存在美化自己的倾向。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="印象管理量表(BIDR-IM)",
        description="本问卷帮助了解您在回答问题时是否存在刻意美化自己的倾向。共20题，大约需要4分钟完成。",
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
