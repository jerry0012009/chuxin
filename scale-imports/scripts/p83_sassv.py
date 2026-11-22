"""P83: SAS-SV 智能手机成瘾量表简版 (Smartphone Addiction Scale-Short Version)
Kwon et al. (2013), 中文版
10 items, 6-point scale. Single dimension: 智能手机成瘾倾向.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "sassv"
IMPORT_CODE = "huaxinyun-sassv"

OPT_6 = [
    ("非常不符合", 1), ("不符合", 2), ("有点不符合", 3),
    ("有点符合", 4), ("符合", 5), ("非常符合", 6)
]

QUESTIONS_RAW = [
    (1,  "玩智能手机的时间比原计划的要长。", False),
    (2,  "经常把智能手机放在触手可及的地方。", False),
    (3,  "因为使用智能手机而导致学习或工作效率下降。", False),
    (4,  "周围的人曾对我说我花了太多时间在智能手机上。", False),
    (5,  "有人打扰你使用智能手机时你会不耐烦。", False),
    (6,  "总觉得少了智能手机会坐立不安。", False),
    (7,  "当手机没带在身边时，会感到焦虑不安。", False),
    (8,  "使用智能手机影响了你的人际关系。", False),
    (9,  "即使没有通知也忍不住想要查看智能手机。", False),
    (10, "因为使用智能手机而影响了睡眠。", False),
]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        qs.append(radio_q(order, text, OPT_6))
    return qs

def make_dimensions():
    formula = q_range(1, 10) + " / 10"
    return [
        dimension("智能手机成瘾倾向", "smartphone_addiction", 1, formula, "", [
            result_rule("hx_wd_y_1 <= 2.5", "智能手机成瘾倾向较低",
                "您使用智能手机的程度较为适度，未表现出明显的成瘾特征。建议继续保持良好的手机使用习惯。", "none"),
            result_rule("hx_wd_y_1 > 2.5 && hx_wd_y_1 <= 4.0", "智能手机成瘾倾向中等",
                "您存在一定程度的智能手机过度使用现象，可能已经影响到日常生活。建议设定使用时间限制，培养其他兴趣爱好。", "none"),
            result_rule("hx_wd_y_1 > 4.0", "智能手机成瘾倾向较高",
                "您表现出较强的智能手机成瘾倾向，过度使用可能已严重影响学习、工作和人际关系。建议寻求专业帮助，制定戒断计划。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="智能手机成瘾量表-简版(SAS-SV)",
        description="本量表帮助评估您使用智能手机的习惯和可能的成瘾倾向。共10题，大约需要2分钟完成。",
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
