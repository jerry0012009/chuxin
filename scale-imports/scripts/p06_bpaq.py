"""P0-6: BPAQ - Buss-Perry Aggression Questionnaire (Buss & Perry, 1992)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "bpaq-aggression"
IMPORT_CODE = "huaxinyun-bpaq-aggression"

# 29 items, 5-point scale (1-5)
# No reverse items
# Subscales:
#   Physical Aggression (PA): 1,5,9,13,17,21,25,27,29 (9 items)
#   Verbal Aggression (VA): 2,6,10,14,18 (5 items)
#   Anger (A): 3,7,11,15,19,23,26 (7 items)
#   Hostility (H): 4,8,12,16,20,22,24,28 (8 items)

QUESTIONS = [
    # Physical Aggression
    (1,  "在受到足够的挑衅时，我可能会动手打人。"),
    (2,  "当我不同意朋友的看法时，我会坦率地告诉他们。"),
    (3,  "我很容易突然发火，但消气也很快。"),
    (4,  "我有时觉得自己像一个即将爆炸的火药桶。"),
    (5,  "我偶尔无法控制打人的冲动。"),
    (6,  "我的朋友说我有些好辩。"),
    (7,  "我有时会毫无缘由地突然发火。"),
    (8,  "我有时觉得生活中我遭受了不公正的对待。"),
    (9,  "如果有人先动手打我，我会反击。"),
    (10, "当别人与我意见不一致时，我忍不住要和他们争论。"),
    (11, "我有时觉得自己脾气非常暴躁。"),
    (12, "别人似乎总是比我走运。"),
    (13, "我想不出有什么正当理由可以打人。"),
    (14, "我曾经气得摔碎了东西。"),
    (15, "有时我会因为一些小事情而感到非常恼火。"),
    (16, "我对过于友好的陌生人保持戒心。"),
    (17, "有时候我控制不住自己打人的冲动。"),
    (18, "当别人不同意我的看法时，我忍不住要与之争辩。"),
    (19, "我的朋友们认为我是一个容易激动的人。"),
    (20, "有时候我会被强烈的嫉妒所困扰。"),
    (21, "我曾威胁过我认识的人。"),
    (22, "我有时觉得自己像一个随时要爆发的火药桶。"),
    (23, "有时候我因为一点小差错就会大发脾气。"),
    (24, "我觉得别人总是在背后议论我。"),
    (25, "如果有人先打了我，我一定要还击。"),
    (26, "我很容易失去控制。"),
    (27, "当朋友借了我的东西不还时，我会非常愤怒。"),
    (28, "我有时候觉得别人在利用我。"),
    (29, "我的朋友们说我有点好争吵。"),
]

PA_ITEMS = {1, 5, 9, 13, 17, 21, 25, 27, 29}
VA_ITEMS = {2, 6, 10, 14, 18}
A_ITEMS  = {3, 7, 11, 15, 19, 23, 26}
H_ITEMS  = {4, 8, 12, 16, 20, 22, 24, 28}

def make_questions():
    qs = []
    for order, text_zh in QUESTIONS:
        opts = [("完全不像我", 1), ("比较不像我", 2), ("不确定", 3), ("比较像我", 4), ("完全像我", 5)]
        qs.append(radio_q(order, text_zh, opts))
    return qs

def items_formula(items):
    return " + ".join(f"hx_t_{i}" for i in sorted(items))

def make_dimensions():
    pa_formula  = items_formula(PA_ITEMS)
    va_formula  = items_formula(VA_ITEMS)
    anger_formula = items_formula(A_ITEMS)
    host_formula  = items_formula(H_ITEMS)
    total_formula = q_range(1, 29)

    return [
        # Dimension 1: Physical Aggression (9 items, range 9-45)
        dimension("身体攻击性", "physical_aggression", 1, pa_formula, "", [
            result_rule("hx_wd_y_1 <= 15", "身体攻击性较低",
                "您的身体攻击性倾向较低，在面对冲突时能够保持冷静和克制。", "none"),
            result_rule("hx_wd_y_1 > 15 && hx_wd_y_1 <= 27", "身体攻击性中等",
                "您的身体攻击性倾向处于正常范围，在受到强烈刺激时可能表现出一定的攻击性反应。", "none"),
            result_rule("hx_wd_y_1 > 27 && hx_wd_y_1 <= 36", "身体攻击性偏高",
                "您的身体攻击性倾向偏高，建议学习更多非暴力的冲突解决方式，培养情绪管理能力。", "low"),
            result_rule("hx_wd_y_1 > 36", "身体攻击性异常偏高",
                "您的身体攻击性倾向显著偏高，建议寻求专业心理咨询，学习愤怒管理和冲突应对技巧。", "high"),
        ]),
        # Dimension 2: Verbal Aggression (5 items, range 5-25)
        dimension("言语攻击性", "verbal_aggression", 2, va_formula, "", [
            result_rule("hx_wd_y_2 <= 9", "言语攻击性较低",
                "您的言语攻击性倾向较低，在沟通中较为平和理性。", "none"),
            result_rule("hx_wd_y_2 > 9 && hx_wd_y_2 <= 15", "言语攻击性中等",
                "您的言语攻击性倾向处于正常范围，在观点不一致时可能表现出争论倾向。", "none"),
            result_rule("hx_wd_y_2 > 15 && hx_wd_y_2 <= 20", "言语攻击性偏高",
                "您的言语攻击性倾向偏高，建议在沟通中注意措辞，学会倾听和换位思考。", "low"),
            result_rule("hx_wd_y_2 > 20", "言语攻击性异常偏高",
                "您的言语攻击性倾向显著偏高，建议关注沟通方式，学习非暴力沟通技巧。", "middle"),
        ]),
        # Dimension 3: Anger (7 items, range 7-35)
        dimension("愤怒", "anger", 3, anger_formula, "", [
            result_rule("hx_wd_y_3 <= 13", "愤怒水平较低",
                "您的愤怒情绪水平较低，情绪调节能力较好。", "none"),
            result_rule("hx_wd_y_3 > 13 && hx_wd_y_3 <= 21", "愤怒水平中等",
                "您的愤怒情绪水平处于正常范围，偶尔会因特定事件感到愤怒。", "none"),
            result_rule("hx_wd_y_3 > 21 && hx_wd_y_3 <= 28", "愤怒水平偏高",
                "您的愤怒情绪水平偏高，建议学习情绪调节技巧，如深呼吸、正念冥想等。", "low"),
            result_rule("hx_wd_y_3 > 28", "愤怒水平异常偏高",
                "您的愤怒情绪水平显著偏高，建议寻求专业帮助，学习有效的情绪管理策略。", "high"),
        ]),
        # Dimension 4: Hostility (8 items, range 8-40)
        dimension("敌意", "hostility", 4, host_formula, "", [
            result_rule("hx_wd_y_4 <= 15", "敌意水平较低",
                "您的敌意水平较低，对他人持较为信任和友善的态度。", "none"),
            result_rule("hx_wd_y_4 > 15 && hx_wd_y_4 <= 24", "敌意水平中等",
                "您的敌意水平处于正常范围，偶尔会对他人产生怀疑或不满。", "none"),
            result_rule("hx_wd_y_4 > 24 && hx_wd_y_4 <= 32", "敌意水平偏高",
                "您的敌意水平偏高，建议审视自己的认知模式，减少对他人的负面归因。", "low"),
            result_rule("hx_wd_y_4 > 32", "敌意水平异常偏高",
                "您的敌意水平显著偏高，建议寻求专业心理咨询，改善人际认知和社交技能。", "high"),
        ]),
        # Total dimension (29 items, range 29-145)
        dimension("攻击性总分", "total_aggression", 5, total_formula, "", [
            result_rule("hx_wd_y_5 <= 55", "攻击性水平较低",
                "您的总体攻击性水平较低，在人际交往中较为平和友善。", "none"),
            result_rule("hx_wd_y_5 > 55 && hx_wd_y_5 <= 77", "攻击性水平中等（男性常模均值约77）",
                "您的总体攻击性水平处于正常范围，与一般男性常模水平相当。", "none"),
            result_rule("hx_wd_y_5 > 77 && hx_wd_y_5 <= 100", "攻击性水平偏高",
                "您的总体攻击性水平偏高，建议关注自身情绪管理和人际冲突处理方式。", "low"),
            result_rule("hx_wd_y_5 > 100", "攻击性水平异常偏高",
                "您的总体攻击性水平显著高于常模（男性均值约77，女性均值约69），建议寻求专业心理咨询评估。", "high"),
        ]),
    ]

def build():
    return build_scale(
        title="巴斯-佩里攻击性问卷(BPAQ)",
        description="本问卷帮助了解您在身体攻击、言语表达、愤怒情绪和敌意认知等方面的特点。共29题，大约需要5分钟完成。",
        code=SCALE_CODE,
        questions=make_questions(),
        dimensions=make_dimensions(),
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
