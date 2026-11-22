"""P1-11: VAST - Varieties of Sadistic Tendencies (Paulhus & Jones, 2015)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "vast-sadistic"
IMPORT_CODE = "huaxinyun-vast-sadistic"

# VAST: 27 items (9 Direct sadism, 7 Vicarious sadism, 11 filler)
# 5-point Likert
# Direct items: 1,3,5,8,10,13,16,18,20
# Vicarious items: 2,7,12,15,19,22,25
# Filler items: 4,6,9,11,14,17,21,23,24,26,27

DIRECT_ITEMS = {1, 3, 5, 8, 10, 13, 16, 18, 20}
VICARIOUS_ITEMS = {2, 7, 12, 15, 19, 22, 25}
FILLER_ITEMS = {4, 6, 9, 11, 14, 17, 21, 23, 24, 26, 27}

QUESTIONS = [
    # Items organized by number
    (1, "看到别人受苦时我会感到愉悦。"),  # Direct
    (2, "我喜欢观看暴力电影或视频中的血腥场面。"),  # Vicarious
    (3, "我曾经享受过让他人感到痛苦的过程。"),  # Direct
    (4, "我通常能很好地控制自己的情绪。"),  # Filler
    (5, "伤害别人让我感到兴奋。"),  # Direct
    (6, "我喜欢结交新朋友。"),  # Filler
    (7, "我喜欢观看打架或格斗的视频。"),  # Vicarious
    (8, "如果能不受惩罚，我愿意伤害别人。"),  # Direct
    (9, "我喜欢在户外活动。"),  # Filler
    (10, "折磨别人的想法让我感到兴奋。"),  # Direct
    (11, "我觉得笑话通常是有趣的。"),  # Filler
    (12, "我喜欢看恐怖电影中角色遭受痛苦的情节。"),  # Vicarious
    (13, "我曾故意在身体上伤害过他人。"),  # Direct
    (14, "我很容易感到无聊。"),  # Filler
    (15, "我喜欢在网上观看真实的暴力事件视频。"),  # Vicarious
    (16, "我会享受对他人施加身体痛苦的过程。"),  # Direct
    (17, "我更喜欢和别人一起工作。"),  # Filler
    (18, "我曾经为了好玩而残忍地对待过别人。"),  # Direct
    (19, "看到有人被欺负时，我会感到一种快感。"),  # Vicarious
    (20, "如果可以不受惩罚，我愿意用暴力对待别人。"),  # Direct
    (21, "我喜欢听音乐。"),  # Filler
    (22, "我喜欢看别人经历尴尬或屈辱的场面。"),  # Vicarious
    (23, "我喜欢阅读。"),  # Filler
    (24, "我通常遵守规则。"),  # Filler
    (25, "我喜欢看灾难片中人们遭受痛苦的画面。"),  # Vicarious
    (26, "我喜欢户外运动。"),  # Filler
    (27, "我很容易和别人交朋友。"),  # Filler
]

LIKERT5_OPTIONS = [
    ("非常不同意", 1), ("不同意", 2), ("不确定", 3), ("同意", 4), ("非常同意", 5)
]

def make_questions():
    return [radio_q(order, text, LIKERT5_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    # Direct sadism: mean of items 1,3,5,8,10,13,16,18,20 (9 items)
    direct_items = " + ".join(f"hx_t_{i}" for i in sorted(DIRECT_ITEMS))
    direct_formula = f"({direct_items}) / 9"

    # Vicarious sadism: mean of items 2,7,12,15,19,22,25 (7 items)
    vicarious_items = " + ".join(f"hx_t_{i}" for i in sorted(VICARIOUS_ITEMS))
    vicarious_formula = f"({vicarious_items}) / 7"

    return [
        dimension("直接施虐倾向", "direct_sadism", 1, direct_formula, "", [
            result_rule("hx_wd_y_1 <= 1.36", "直接施虐倾向较低", "您的直接施虐倾向低于女性平均水平，人际行为良好。", "none"),
            result_rule("hx_wd_y_1 > 1.36 && hx_wd_y_1 <= 1.95", "直接施虐倾向中等", "您的直接施虐倾向处于常模范围（女1.36，男1.95）。", "none"),
            result_rule("hx_wd_y_1 > 1.95 && hx_wd_y_1 <= 2.67", "直接施虐倾向偏高", "您的得分高于男性平均（1.95），建议关注对他人痛苦的态度。", "low"),
            result_rule("hx_wd_y_1 > 2.67", "直接施虐倾向异常偏高", "您的得分显著高于常模（男1.95±0.72），建议寻求专业心理评估。", "middle"),
        ]),
        dimension("替代施虐倾向", "vicarious_sadism", 2, vicarious_formula, "", [
            result_rule("hx_wd_y_2 <= 2.34", "替代施虐倾向较低", "您的替代施虐倾向低于女性平均水平。", "none"),
            result_rule("hx_wd_y_2 > 2.34 && hx_wd_y_2 <= 2.90", "替代施虐倾向中等", "您的替代施虐倾向处于常模范围（女2.34，男2.90）。", "none"),
            result_rule("hx_wd_y_2 > 2.90 && hx_wd_y_2 <= 3.70", "替代施虐倾向偏高", "您的得分高于男性平均（2.90），建议关注观看暴力内容的倾向。", "low"),
            result_rule("hx_wd_y_2 > 3.70", "替代施虐倾向异常偏高", "您的得分显著高于常模（男2.90±0.80），建议寻求专业心理评估。", "middle"),
        ]),
    ]

def build():
    return build_scale(
        title="施虐倾向多样性量表(VAST)",
        description="本问卷用于了解您对他人痛苦的态度和行为倾向。共18题，大约需要3分钟完成。",
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
