"""P59: 轻躁狂特质量表(HYP)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "hypomanic-traits"
IMPORT_CODE = "huaxinyun-hypomanic-traits"

OPTIONS = [
    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)
]

QUESTIONS_RAW = [
    (1, "我喜欢成为大家关注的中心"),
    (2, "我喜欢在别人面前表现自己"),
    (3, "我常常觉得自己与众不同"),
    (4, "我觉得自己有特殊的才能"),
    (5, "我喜欢让别人印象深刻"),
    (6, "我觉得自己比大多数人更有魅力"),
    (7, "我经常有很多新的想法和计划"),
    (8, "我有时候觉得自己无所不能"),
    (9, "我喜欢冒险和尝试新事物"),
    (10, "我的精力比大多数人更充沛"),
    (11, "我经常感到特别兴奋"),
    (12, "我觉得自己比别人更有创造力"),
    (13, "我的情绪波动很大"),
    (14, "我会突然从开心变得难过"),
    (15, "有时候我会非常兴奋，有时候又会非常低落"),
    (16, "我的心情变化很快"),
    (17, "有时候我会毫无原因地感到特别开心"),
    (18, "我会突然精力旺盛到不需要睡觉"),
    (19, "有时候我说话比平时快很多"),
    (20, "我的想法有时会跳跃得很快"),
    (21, "有时候我会同时做很多事情"),
    (22, "我有时会突然做出冲动的决定"),
    (23, "有时候我会花很多钱买不需要的东西"),
    (24, "我有时会突然想去旅行或做大的改变"),
]

def make_questions():
    return [radio_q(order, text, OPTIONS) for order, text in QUESTIONS_RAW]

def make_dimensions():
    return [
        dimension("表现欲", "exhibitionism", 1, "(hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8 + hx_t_9 + hx_t_10 + hx_t_11 + hx_t_12) / 12", "", [
            result_rule("hx_wd_y_1 <= 2.0", "低", "您的表现欲较低，偏好低调。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "中", "您的表现欲适中。", "none"),
            result_rule("hx_wd_y_1 > 3.5", "高", "您有较强的表现欲，喜欢成为关注的中心，可能有夸大的自我评价。", "none"),
        ]),
        dimension("情绪强度与变化", "mood_intensity", 2, "(hx_t_13 + hx_t_14 + hx_t_15 + hx_t_16 + hx_t_17 + hx_t_18 + hx_t_19 + hx_t_20 + hx_t_21 + hx_t_22 + hx_t_23 + hx_t_24) / 12", "", [
            result_rule("hx_wd_y_2 <= 2.0", "低", "您的情绪较为稳定，波动不大。", "none"),
            result_rule("hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "中", "您的情绪波动程度适中。", "none"),
            result_rule("hx_wd_y_2 > 3.5", "高", "您的情绪波动较大，可能出现精力旺盛和冲动行为。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="轻躁狂特质量表(HYP)",
        description="本问卷帮助了解您是否存在情绪高涨、精力旺盛或冲动等方面的特质。共24题，大约需要5分钟完成。",
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
