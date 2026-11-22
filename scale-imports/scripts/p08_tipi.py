"""P0-8: TIPI - Ten Item Personality Inventory (Gosling, Rentfrow, & Swann, 2003)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "tipi-personality"
IMPORT_CODE = "huaxinyun-tipi-personality"

# TIPI: 10 items, pairs of Big Five adjectives, 7-point scale
# Dimensions: Extraversion (1,6R), Agreeableness (2R,7), Conscientiousness (3,8R),
#             Emotional Stability (4R,9), Openness (5,10R)
# R = reverse scored (8→1, 7→2, 6→3, 5→4, 4→5, 3→6, 2→7)

QUESTIONS = [
    (1, "外向的、热情的"),
    (2, "爱挑剔的、好争论的"),
    (3, "可靠的、自律的"),
    (4, "焦虑的、容易心烦的"),
    (5, "对新体验开放的、复杂的"),
    (6, "安静的、保守的"),
    (7, "有同情心的、温暖的"),
    (8, "无条理的、粗心的"),
    (9, "冷静的、情绪稳定的"),
    (10, "传统的、缺乏想象力的"),
]

REVERSE_ITEMS = {2, 4, 6, 8, 10}

LIKERT7_OPTIONS = [
    ("非常不同意", 1), ("不同意", 2), ("有点不同意", 3),
    ("不确定", 4), ("有点同意", 5), ("同意", 6), ("非常同意", 7)
]

LIKERT7_OPTIONS_REVERSE = [
    ("非常不同意", 7), ("不同意", 6), ("有点不同意", 5),
    ("不确定", 4), ("有点同意", 3), ("同意", 2), ("非常同意", 1)
]

def make_questions():
    qs = []
    for order, text in QUESTIONS:
        if order in REVERSE_ITEMS:
            qs.append(radio_q(order, text, LIKERT7_OPTIONS_REVERSE))
        else:
            qs.append(radio_q(order, text, LIKERT7_OPTIONS))
    return qs

def make_dimensions():
    # Extraversion: items 1,6 (6 reverse scored) → mean
    extrav = "(hx_t_1 + hx_t_6) / 2"
    # Agreeableness: items 2(reverse),7 → mean
    agree = "(hx_t_2 + hx_t_7) / 2"
    # Conscientiousness: items 3,8(reverse) → mean
    consc = "(hx_t_3 + hx_t_8) / 2"
    # Emotional Stability: items 4(reverse),9 → mean
    estab = "(hx_t_4 + hx_t_9) / 2"
    # Openness: items 5,10(reverse) → mean
    openn = "(hx_t_5 + hx_t_10) / 2"

    return [
        dimension("外向性", "extraversion", 1, extrav, "", [
            result_rule("hx_wd_y_1 <= 2.5", "外向性较低", "您倾向于内向安静，更喜欢独处或小范围社交。", "none"),
            result_rule("hx_wd_y_1 > 2.5 && hx_wd_y_1 <= 4.5", "外向性中等", "您的社交倾向处于正常范围，能灵活适应不同社交场景。", "none"),
            result_rule("hx_wd_y_1 > 4.5 && hx_wd_y_1 <= 5.5", "外向性偏高", "您倾向外向活跃，喜欢社交和刺激。", "none"),
            result_rule("hx_wd_y_1 > 5.5", "外向性很高", "您非常外向热情，社交能量充沛。", "none"),
        ]),
        dimension("宜人性", "agreeableness", 2, agree, "", [
            result_rule("hx_wd_y_2 <= 2.5", "宜人性较低", "您可能倾向于批判性和竞争性。", "low"),
            result_rule("hx_wd_y_2 > 2.5 && hx_wd_y_2 <= 4.5", "宜人性中等", "您在合作与竞争之间保持平衡。", "none"),
            result_rule("hx_wd_y_2 > 4.5 && hx_wd_y_2 <= 5.5", "宜人性偏高", "您倾向于友善和富有同情心。", "none"),
            result_rule("hx_wd_y_2 > 5.5", "宜人性很高", "您非常富有同情心和温暖。", "none"),
        ]),
        dimension("尽责性", "conscientiousness", 3, consc, "", [
            result_rule("hx_wd_y_3 <= 2.5", "尽责性较低", "您可能更随性灵活，但有时缺乏条理。", "low"),
            result_rule("hx_wd_y_3 > 2.5 && hx_wd_y_3 <= 4.5", "尽责性中等", "您的自律和条理处于正常范围。", "none"),
            result_rule("hx_wd_y_3 > 4.5 && hx_wd_y_3 <= 5.5", "尽责性偏高", "您倾向于可靠和自律。", "none"),
            result_rule("hx_wd_y_3 > 5.5", "尽责性很高", "您非常可靠、自律和有条理。", "none"),
        ]),
        dimension("情绪稳定性", "emotional_stability", 4, estab, "", [
            result_rule("hx_wd_y_4 <= 2.5", "情绪稳定性较低", "您可能容易焦虑和情绪波动，建议关注情绪管理。", "low"),
            result_rule("hx_wd_y_4 > 2.5 && hx_wd_y_4 <= 4.5", "情绪稳定性中等", "您的情绪调节能力处于正常范围。", "none"),
            result_rule("hx_wd_y_4 > 4.5 && hx_wd_y_4 <= 5.5", "情绪稳定性偏高", "您倾向于冷静和情绪稳定。", "none"),
            result_rule("hx_wd_y_4 > 5.5", "情绪稳定性很高", "您非常冷静和情绪稳定。", "none"),
        ]),
        dimension("开放性", "openness", 5, openn, "", [
            result_rule("hx_wd_y_5 <= 2.5", "开放性较低", "您可能更偏好传统和熟悉的事物。", "none"),
            result_rule("hx_wd_y_5 > 2.5 && hx_wd_y_5 <= 4.5", "开放性中等", "您对新体验的接受度处于正常范围。", "none"),
            result_rule("hx_wd_y_5 > 4.5 && hx_wd_y_5 <= 5.5", "开放性偏高", "您对新体验和想法持开放态度。", "none"),
            result_rule("hx_wd_y_5 > 5.5", "开放性很高", "您非常开放，富有想象力和好奇心。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="十项人格问卷(TIPI)",
        description="本问卷用简短的10个题目快速了解您的大五人格特征，包括外向性、宜人性等方面。大约需要2分钟完成。",
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
