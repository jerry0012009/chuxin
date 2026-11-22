"""P0-1: SD3 - Short Dark Triad (Jones & Paulhus, 2014)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

# SD3 items with Chinese translations
# Subscales: Machiavellianism (1-9), Narcissism (10-18), Psychopathy (19-27)
# Reverse items: 11, 15, 17, 20, 25

SCALE_CODE = "sd3-dark-triad"
IMPORT_CODE = "huaxinyun-sd3-dark-triad"

QUESTIONS = [
    # Machiavellianism (1-9)
    (1, "把自己的秘密告诉别人是不明智的。"),
    (2, "我喜欢用巧妙的操控来达到自己的目的。"),
    (3, "无论如何，你必须让重要的人站在你这边。"),
    (4, "避免与他人直接冲突，因为他们将来可能有用。"),
    (5, "保留日后可以用来对付他人的信息是明智的。"),
    (6, "你应该等待合适的时机来报复他人。"),
    (7, "有些事情你应该对别人隐瞒，因为他们不需要知道。"),
    (8, "确保你的计划让自己受益，而不是让他人受益。"),
    (9, "大多数人都可以被操控。"),
    # Narcissism (10-18)
    (10, "别人认为我是天生的领导者。"),
    (11, "我讨厌成为关注的焦点。"),
    (12, "没有我，很多团体活动都会变得无聊。"),
    (13, "我知道自己很特别，因为大家都这么说。"),
    (14, "我喜欢结识重要人物。"),
    (15, "如果有人称赞我，我会感到尴尬。"),
    (16, "我曾被拿来和名人作比较。"),
    (17, "我是一个普通人。"),
    (18, "我坚持获得自己应得的尊重。"),
    # Psychopathy (19-27)
    (19, "我喜欢报复权威人士。"),
    (20, "我会避免危险的情况。"),
    (21, "报复需要迅速而狠辣。"),
    (22, "别人经常说我失控了。"),
    (23, "我确实会对他人刻薄。"),
    (24, "惹我的人总是会后悔的。"),
    (25, "我从来没有惹上过法律麻烦。"),
    (26, "我喜欢和不太认识的人发生性关系。"),
    (27, "为了得到我想要的，我什么话都说得出来。"),
]

REVERSE_ITEMS = {11, 15, 17, 20, 25}

def make_questions():
    qs = []
    for order, text_zh in QUESTIONS:
        if order in REVERSE_ITEMS:
            opts = [("非常不同意", 5), ("不同意", 4), ("不确定", 3), ("同意", 2), ("非常同意", 1)]
        else:
            opts = [("非常不同意", 1), ("不同意", 2), ("不确定", 3), ("同意", 4), ("非常同意", 5)]
        qs.append(radio_q(order, text_zh, opts))
    return qs

def make_dimensions():
    # Machiavellianism: mean of items 1-9
    mach_mean = " + ".join(f"hx_t_{i}" for i in range(1, 10))
    mach_formula = f"({mach_mean}) / 9"
    
    # Narcissism: mean of items 10-18
    narc_mean = " + ".join(f"hx_t_{i}" for i in range(10, 19))
    narc_formula = f"({narc_mean}) / 9"
    
    # Psychopathy: mean of items 19-27
    psy_mean = " + ".join(f"hx_t_{i}" for i in range(19, 28))
    psy_formula = f"({psy_mean}) / 9"
    
    return [
        dimension("马基雅维利主义", "machiavellianism", 1, mach_formula, "", [
            result_rule("hx_wd_y_1 <= 2.34", "马基雅维利主义水平较低", "您在人际交往中倾向于真诚和直接，操控性较低。", "none"),
            result_rule("hx_wd_y_1 > 2.34 && hx_wd_y_1 <= 3.10", "马基雅维利主义水平中等", "您在必要时会使用一些策略性手段，但整体处于正常范围。", "none"),
            result_rule("hx_wd_y_1 > 3.10 && hx_wd_y_1 <= 3.86", "马基雅维利主义水平偏高", "您倾向于策略性思考和人际操控，建议关注人际关系中的诚信建设。", "low"),
            result_rule("hx_wd_y_1 > 3.86", "马基雅维利主义水平异常偏高", "您的得分显著高于常模（均值3.1，标准差0.76），建议关注人际互动中的道德意识和诚信行为。", "middle"),
        ]),
        dimension("自恋", "narcissism", 2, narc_formula, "", [
            result_rule("hx_wd_y_2 <= 1.92", "自恋水平较低", "您的自我评价较为谦逊和务实。", "none"),
            result_rule("hx_wd_y_2 > 1.92 && hx_wd_y_2 <= 2.80", "自恋水平中等", "您的自我评价处于正常范围，具有适度的自信。", "none"),
            result_rule("hx_wd_y_2 > 2.80 && hx_wd_y_2 <= 3.68", "自恋水平偏高", "您对自我重要性有较强的感受，建议保持自我觉察。", "low"),
            result_rule("hx_wd_y_2 > 3.68", "自恋水平异常偏高", "您的得分显著高于常模（均值2.8，标准差0.88），建议关注共情能力和人际关系的平衡发展。", "middle"),
        ]),
        dimension("精神病态", "psychopathy", 3, psy_formula, "", [
            result_rule("hx_wd_y_3 <= 1.40", "精神病态水平较低", "您的冲动控制和情感共鸣能力良好。", "none"),
            result_rule("hx_wd_y_3 > 1.40 && hx_wd_y_3 <= 2.40", "精神病态水平中等", "您的冲动性和冷酷特质处于正常范围。", "none"),
            result_rule("hx_wd_y_3 > 2.40 && hx_wd_y_3 <= 3.40", "精神病态水平偏高", "您在冲动控制和情感共鸣方面可能需要更多关注，建议进行自我反思。", "low"),
            result_rule("hx_wd_y_3 > 3.40", "精神病态水平异常偏高", "您的得分显著高于常模（均值2.4，标准差1.0），建议寻求专业心理咨询评估。", "high"),
        ]),
    ]

def build():
    return build_scale(
        title="暗黑三角人格量表(SD3)",
        description="本问卷帮助了解您在人际交往中可能存在的某些人格特征，包括倾向于操控他人、自我中心或情感淡漠等方面。共27题，大约需要5分钟完成。",
        code=SCALE_CODE,  # id field, import service will prepend "huaxinyun-"
        questions=make_questions(),
        dimensions=make_dimensions(),
    )

if __name__ == "__main__":
    scale = build()
    # Save JSON
    json_path = os.path.join(os.path.dirname(__file__), "..", "json", f"{SCALE_CODE}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(scale, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON saved: {json_path}")
    print(f"   Questions: {len(scale['questions'])}")
    print(f"   Dimensions: {len(scale['dimensions'])}")
    
    # Dry run first
    print("\n--- Dry Run ---")
    result = import_scale(scale, dry_run=True, publish=True)
    print(f"   Importable: {result.get('importable', 0)}")
    print(f"   Publishable: {result.get('publishable', 0)}")
    for item in result.get("items", []):
        print(f"   {item.get('title')}: {item.get('action')} | issues={item.get('issues')} | warnings={item.get('warnings')}")
    
    # Actually import
    print("\n--- Importing ---")
    result = import_scale(scale, dry_run=False, publish=True, overwrite=True)
    print(f"   Imported: {result.get('imported', 0)}")
    print(f"   Updated: {result.get('updated', 0)}")
    for item in result.get("items", []):
        print(f"   {item.get('title')}: {item.get('action')} | id={item.get('survey_id', 'N/A')}")
    
    # Verify
    print("\n--- DB Verify ---")
    print(verify_in_db(IMPORT_CODE))
