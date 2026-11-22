"""P1-18: GRIT-S - Short Grit Scale (Duckworth & Quinn, 2009)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "grit-s-short-grit"
IMPORT_CODE = "huaxinyun-grit-s-short-grit"

# GRIT-S: 8 items, 5-point (1=not at all like me to 5=very much like me)
# Consistency of interest: items 2,4,6,8 (reverse: 2,4,6,8)
# Perseverance of effort: items 1,3,5,7 (reverse: none)

GRIT_5_OPTIONS = [
    ("一点也不像我", 1), ("不太像我", 2), ("有些像我", 3), ("比较像我", 4), ("非常像我", 5)
]

QUESTIONS = [
    (1, "新的想法和项目有时会让我从之前的项目中分心。"),
    (2, "挫折不会让我气馁。"),
    (3, "我在一段时间内会对某个想法或项目感兴趣，但随后会失去兴趣。"),
    (4, "我是一个努力工作的人。"),
    (5, "我经常设定一个目标，但后来又选择追求不同的目标。"),
    (6, "在完成任务时，我注重细节。"),
    (7, "我的兴趣每年都在变化。"),
    (8, "我做事有始有终。"),
]

# Consistency of interest: items 2,4,6,8 (reverse scored)
CONSISTENCY_ITEMS = [2, 4, 6, 8]
# Perseverance of effort: items 1,3,5,7
PERSEVERANCE_ITEMS = [1, 3, 5, 7]

def make_questions():
    return [radio_q(order, text, GRIT_5_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    all_formula = " + ".join(f"hx_t_{i}" for i in range(1, 9))
    consistency_formula = " + ".join(f"hx_t_{i}" for i in CONSISTENCY_ITEMS)
    perseverance_formula = " + ".join(f"hx_t_{i}" for i in PERSEVERANCE_ITEMS)

    return [
        dimension("毅力总分", "grit_total", 1, f"({all_formula}) / 8", "", [
            result_rule("hx_wd_y_1 <= 2.5", "毅力水平较低", "您的毅力得分较低，在面对困难时可能容易放弃，建议培养坚持的习惯。", "low"),
            result_rule("hx_wd_y_1 > 2.5 && hx_wd_y_1 <= 3.4", "毅力水平中等", "您的毅力处于中等水平，与一般人群平均水平相当。", "none"),
            result_rule("hx_wd_y_1 > 3.4 && hx_wd_y_1 <= 4.2", "毅力水平较高", "您的毅力得分较高，能够较好地坚持长期目标。", "none"),
            result_rule("hx_wd_y_1 > 4.2", "毅力水平很高", "您的毅力得分非常高，表现出很强的坚持和专注能力。", "none"),
        ]),
        dimension("兴趣一致性", "consistency", 2, f"({consistency_formula}) / 4", "", [
            result_rule("hx_wd_y_2 <= 2.5", "兴趣一致性较低", "您的兴趣容易转移，可能需要练习专注于长期目标。", "none"),
            result_rule("hx_wd_y_2 > 2.5 && hx_wd_y_2 <= 3.5", "兴趣一致性中等", "您的兴趣一致性处于中等水平。", "none"),
            result_rule("hx_wd_y_2 > 3.5", "兴趣一致性较高", "您能够较好地保持对长期目标的兴趣。", "none"),
        ]),
        dimension("努力坚持性", "perseverance", 3, f"({perseverance_formula}) / 4", "", [
            result_rule("hx_wd_y_3 <= 2.5", "努力坚持性较低", "您在面对挫折时坚持努力的能力有待提高。", "none"),
            result_rule("hx_wd_y_3 > 2.5 && hx_wd_y_3 <= 3.5", "努力坚持性中等", "您的努力坚持性处于中等水平。", "none"),
            result_rule("hx_wd_y_3 > 3.5", "努力坚持性较高", "您在面对困难时能够持续努力，不轻易放弃。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="短版毅力量表(GRIT-S)",
        description="本问卷帮助了解您在追求长期目标时的毅力和坚持程度。共8题，大约需要2分钟完成。",
        code=SCALE_CODE,
        questions=make_questions(),
        dimensions=make_dimensions(),
        survey_type="basic",
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
