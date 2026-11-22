"""P51: 解离体验量表(Dissociation)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "dissociation"
IMPORT_CODE = "huaxinyun-dissociation"

OPTIONS = [
    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)
]

QUESTIONS_RAW = [
    (1, "有时候我感觉自己的身体好像不是自己的"),
    (2, "我有时会感觉自己像在做梦一样"),
    (3, "我有时会觉得自己在从远处观察自己"),
    (4, "有时候我感觉自己和周围的世界之间有一层隔膜"),
    (5, "我有时会经历一种不真实的感觉"),
    (6, "有时候我感觉自己像是一个旁观者在看自己的生活"),
    (7, "我会完全沉浸在白日梦中以至于忘记周围的一切"),
    (8, "我经常陷入自己的想象中"),
    (9, "我会沉浸在电影或书中以至于完全意识不到周围发生的事"),
    (10, "听音乐时我会完全忘记自己的存在"),
    (11, "有时我会完全沉浸在自己的思绪中"),
    (12, "我会被自己的幻想深深吸引"),
    (13, "我有时会忘记自己刚才说了什么"),
    (14, "我有时想不起自己是否做过某件事"),
    (15, "我有时会忘记最近发生的事的细节"),
    (16, "我会忘记自己是否告诉过别人某件事"),
    (17, "我有时会忘记自己把东西放在哪里了"),
]

def make_questions():
    return [radio_q(order, text, OPTIONS) for order, text in QUESTIONS_RAW]

def make_dimensions():
    return [
        dimension("去人格化", "depersonalization", 1, "(hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6) / 6", "", [
            result_rule("hx_wd_y_1 <= 2.0", "低", "您很少有不真实的自我体验。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "中", "您偶尔会有轻微的不真实感。", "none"),
            result_rule("hx_wd_y_1 > 3.5", "高", "您经常体验到不真实感或与自身分离的感觉。", "none"),
        ]),
        dimension("吸收", "absorption", 2, "(hx_t_7 + hx_t_8 + hx_t_9 + hx_t_10 + hx_t_11 + hx_t_12) / 6", "", [
            result_rule("hx_wd_y_2 <= 2.0", "低", "您较少沉浸在想象或幻想中。", "none"),
            result_rule("hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "中", "您的想象力和沉浸程度适中。", "none"),
            result_rule("hx_wd_y_2 > 3.5", "高", "您容易完全沉浸在想象、幻想或体验中。", "none"),
        ]),
        dimension("遗忘", "amnesia", 3, "(hx_t_13 + hx_t_14 + hx_t_15 + hx_t_16 + hx_t_17) / 5", "", [
            result_rule("hx_wd_y_3 <= 2.0", "低", "您的日常记忆力正常。", "none"),
            result_rule("hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.5", "中", "您偶尔会出现记忆空白。", "none"),
            result_rule("hx_wd_y_3 > 3.5", "高", "您经常出现记忆空白或遗忘近期事件的情况。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="解离体验量表(Dissociation)",
        description="本问卷帮助了解您是否存在解离体验，如感觉不真实、记忆空白或过度沉浸。共17题，大约需要4分钟完成。",
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
