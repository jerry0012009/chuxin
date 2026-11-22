"""P60: 人格障碍筛查量表(CAT-PD-SF)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "catpd-personality-disorder"
IMPORT_CODE = "huaxinyun-catpd-personality-disorder"

OPTIONS = [
    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)
]

QUESTIONS_RAW = [
    (1, "我善于说服别人做我想要的事"),
    (2, "我知道如何利用别人来达到自己的目的"),
    (3, "我会用奉承来获得好处"),
    (4, "我能轻易地操纵他人的感受"),
    (5, "我擅长假装关心别人"),
    (6, "我对别人的痛苦无动于衷"),
    (7, "我很少感到内疚"),
    (8, "我不太关心他人的感受"),
    (9, "看到别人哭我不会有什么感觉"),
    (10, "我对别人的困难漠不关心"),
    (11, "我容易被激怒并采取行动"),
    (12, "当别人惹我时我会报复"),
    (13, "我有时会用暴力解决问题"),
    (14, "我经常和别人发生冲突"),
    (15, "我会因为小事大发雷霆"),
    (16, "我认为自己比别人优秀"),
    (17, "我觉得自己应该得到特殊待遇"),
    (18, "我相信自己注定会成功"),
    (19, "我觉得自己比大多数人更有能力"),
    (20, "我期待别人崇拜我"),
    (21, "我很难信任别人"),
    (22, "我总觉得别人在背后议论我"),
    (23, "我怀疑别人的动机"),
    (24, "我觉得别人对我有敌意"),
    (25, "我经常觉得别人想害我"),
    (26, "我很难拒绝别人的要求"),
    (27, "我会为了取悦别人而委屈自己"),
    (28, "我害怕得罪别人"),
    (29, "我经常为了维持关系而妥协"),
    (30, "我很难表达不同意见"),
    (31, "我很难从工作中抽身"),
    (32, "我把工作看得比什么都重要"),
    (33, "我即使很累也会继续工作"),
]

def make_questions():
    return [radio_q(order, text, OPTIONS) for order, text in QUESTIONS_RAW]

def make_dimensions():
    return [
        dimension("操控性", "manipulativeness", 1, "(hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5) / 5", "", [
            result_rule("hx_wd_y_1 <= 2.0", "低", "您的操控倾向较低，为人坦诚。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "中", "您的操控倾向适中。", "none"),
            result_rule("hx_wd_y_1 > 3.5", "高", "您可能善于利用和操纵他人来达到自己的目的。", "none"),
        ]),
        dimension("冷酷无情", "callousness", 2, "(hx_t_6 + hx_t_7 + hx_t_8 + hx_t_9 + hx_t_10) / 5", "", [
            result_rule("hx_wd_y_2 <= 2.0", "低", "您对他人的感受很敏感，富有同理心。", "none"),
            result_rule("hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "中", "您的共情程度适中。", "none"),
            result_rule("hx_wd_y_2 > 3.5", "高", "您可能对他人的痛苦较为冷漠，缺乏共情。", "none"),
        ]),
        dimension("敌意攻击", "hostile_aggression", 3, "(hx_t_11 + hx_t_12 + hx_t_13 + hx_t_14 + hx_t_15) / 5", "", [
            result_rule("hx_wd_y_3 <= 2.0", "低", "您的攻击性较低，善于控制情绪。", "none"),
            result_rule("hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.5", "中", "您的攻击性适中。", "none"),
            result_rule("hx_wd_y_3 > 3.5", "高", "您可能有较强的攻击性倾向，容易与人发生冲突。", "none"),
        ]),
        dimension("自大", "grandiosity", 4, "(hx_t_16 + hx_t_17 + hx_t_18 + hx_t_19 + hx_t_20) / 5", "", [
            result_rule("hx_wd_y_4 <= 2.0", "低", "您的自我评价较为谦虚。", "none"),
            result_rule("hx_wd_y_4 > 2.0 && hx_wd_y_4 <= 3.5", "中", "您的自大倾向适中。", "none"),
            result_rule("hx_wd_y_4 > 3.5", "高", "您可能有夸大的自我评价和优越感。", "none"),
        ]),
        dimension("猜疑", "mistrust", 5, "(hx_t_21 + hx_t_22 + hx_t_23 + hx_t_24 + hx_t_25) / 5", "", [
            result_rule("hx_wd_y_5 <= 2.0", "低", "您对他人的信任度较高。", "none"),
            result_rule("hx_wd_y_5 > 2.0 && hx_wd_y_5 <= 3.5", "中", "您的猜疑程度适中。", "none"),
            result_rule("hx_wd_y_5 > 3.5", "高", "您可能对他人有较强的不信任感。", "none"),
        ]),
        dimension("顺从", "submissiveness", 6, "(hx_t_26 + hx_t_27 + hx_t_28 + hx_t_29 + hx_t_30) / 5", "", [
            result_rule("hx_wd_y_6 <= 2.0", "低", "您较为独立，不太容易屈从他人。", "none"),
            result_rule("hx_wd_y_6 > 2.0 && hx_wd_y_6 <= 3.5", "中", "您的顺从程度适中。", "none"),
            result_rule("hx_wd_y_6 > 3.5", "高", "您可能过于顺从他人，难以表达自己的需求。", "none"),
        ]),
        dimension("工作狂", "workaholism", 7, "(hx_t_31 + hx_t_32 + hx_t_33) / 3", "", [
            result_rule("hx_wd_y_7 <= 2.0", "低", "您能较好地平衡工作与生活。", "none"),
            result_rule("hx_wd_y_7 > 2.0 && hx_wd_y_7 <= 3.5", "中", "您的工作投入程度适中。", "none"),
            result_rule("hx_wd_y_7 > 3.5", "高", "您可能过度投入工作，需要注意劳逸结合。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="人格障碍筛查量表(CAT-PD-SF)",
        description="本问卷帮助了解您在人际互动和行为模式方面的特点，用于人格特征的初步筛查。共33题，大约需要6分钟完成。",
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
