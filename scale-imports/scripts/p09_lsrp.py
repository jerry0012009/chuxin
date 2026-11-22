"""P1-9: LSRP - Levenson Self-Report Psychopathy Scale (Levenson, Kiehl, & Fitzpatrick, 1995)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "lsrp-psychopathy"
IMPORT_CODE = "huaxinyun-lsrp-psychopathy"

# LSRP: 26 items, 4-point scale (1=disagree strongly to 4=agree strongly)
# Primary psychopathy (items 1-16), Secondary psychopathy (items 17-26)
# Reverse in primary: 1,2,5,7,12,14,16
# Reverse in secondary: none

QUESTIONS = [
    # Primary Psychopathy (1-16)
    (1, "成功对我来说比如何对待他人更重要。"),
    (2, "对我来说，对竞争对手仁慈就是对自己残忍。"),
    (3, "我冷酷无情地追求自己的目标。"),
    (4, "我有时会为了得到自己想要的东西而操纵他人。"),
    (5, "我假装关心他人来达到自己的目的。"),
    (6, "我经常感到无聊，需要刺激。"),
    (7, "我对自己行为的后果不太担心。"),
    (8, "我相信人生就是适者生存。"),
    (9, "我经常感到一种权力感和优越感。"),
    (10, "我享受掌控他人的感觉。"),
    (11, "我很容易对他人产生厌倦。"),
    (12, "我有时会说谎或欺骗来获得自己想要的东西。"),
    (13, "我倾向于冲动行事。"),
    (14, "我认为自己是一个冷酷的人。"),
    (15, "我做事情时很少感到内疚。"),
    (16, "我对他人的感受缺乏关心。"),
    # Secondary Psychopathy (17-26)
    (17, "我经常发现自己在做自己明知是错的事情。"),
    (18, "当我犯错时，我会责怪他人。"),
    (19, "我发现自己很难控制自己的愤怒。"),
    (20, "我做事情时很少考虑后果。"),
    (21, "我经常与权威人物发生冲突。"),
    (22, "我的生活方式可以被描述为'及时行乐'。"),
    (23, "我在规划未来方面有困难。"),
    (24, "我容易感到沮丧和不耐烦。"),
    (25, "我有时会做一些非常鲁莽的事情。"),
    (26, "我在控制自己行为方面有困难。"),
]

REVERSE_PRIMARY = {1, 2, 5, 7, 12, 14, 16}

LIKERT4_OPTIONS = [
    ("非常不同意", 1), ("不同意", 2), ("同意", 3), ("非常同意", 4)
]

LIKERT4_OPTIONS_REVERSE = [
    ("非常不同意", 4), ("不同意", 3), ("同意", 2), ("非常同意", 1)
]

def make_questions():
    qs = []
    for order, text in QUESTIONS:
        if order in REVERSE_PRIMARY:
            qs.append(radio_q(order, text, LIKERT4_OPTIONS_REVERSE))
        else:
            qs.append(radio_q(order, text, LIKERT4_OPTIONS))
    return qs

def make_dimensions():
    # Primary psychopathy: sum of items 1-16 (range 16-64)
    primary_items = " + ".join(f"hx_t_{i}" for i in range(1, 17))
    # Secondary psychopathy: sum of items 17-26 (range 10-40)
    secondary_items = " + ".join(f"hx_t_{i}" for i in range(17, 27))

    return [
        dimension("原发性精神病态", "primary_psychopathy", 1, primary_items, "", [
            result_rule("hx_wd_y_1 <= 24", "原发性精神病态水平较低", "您的操控性、冷酷和缺乏共情特质较低，人际关系健康。", "none"),
            result_rule("hx_wd_y_1 > 24 && hx_wd_y_1 <= 33", "原发性精神病态水平中等", "您的原发性精神病态特质处于正常范围。", "none"),
            result_rule("hx_wd_y_1 > 33 && hx_wd_y_1 <= 42", "原发性精神病态水平偏高", "您在操控性和冷酷方面得分偏高，建议关注共情能力的培养。", "low"),
            result_rule("hx_wd_y_1 > 42", "原发性精神病态水平异常偏高", "您的得分显著高于常模（男32.96，女27.67），建议寻求专业心理评估。", "high"),
        ]),
        dimension("继发性精神病态", "secondary_psychopathy", 2, secondary_items, "", [
            result_rule("hx_wd_y_2 <= 15", "继发性精神病态水平较低", "您的冲动控制和情绪调节能力良好。", "none"),
            result_rule("hx_wd_y_2 > 15 && hx_wd_y_2 <= 20", "继发性精神病态水平中等", "您的继发性精神病态特质处于正常范围。", "none"),
            result_rule("hx_wd_y_2 > 20 && hx_wd_y_2 <= 26", "继发性精神病态水平偏高", "您在冲动性和情绪不稳定方面得分偏高，建议关注情绪管理和行为控制。", "low"),
            result_rule("hx_wd_y_2 > 26", "继发性精神病态水平异常偏高", "您的得分显著高于常模（男20.04，女19.03），建议寻求专业心理评估和干预。", "high"),
        ]),
    ]

def build():
    return build_scale(
        title="莱文森自我报告精神病态量表(LSRP)",
        description="本问卷帮助了解您在人际互动和自我管理方面的某些特征。共26题，大约需要5分钟完成。",
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
