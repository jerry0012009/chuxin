"""P31: AQ - Autism-Spectrum Quotient
(Baron-Cohen et al., 2001)
50 items, 4-point scale. Binary scoring (0 or 1).
5 dimensions: Social Skills, Attention Switching, Attention to Detail, Communication, Imagination.
Thresholds: <26 unlikely, 26-31 possible, >=32 suggests ASD.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "aq-autism"
IMPORT_CODE = "huaxinyun-aq-autism"

# AQ scoring: each item has a specific "autism-direction" response that scores 1.
# Options are always: 同意(autism) / 同意(not) / 不同意(not) / 不同意(autism)
# We encode the score directly in each option's value.

def _agrees_score1():
    """For items where AGREEING indicates autism (score 1 for 同意)."""
    return [("完全同意", 1), ("稍微同意", 1), ("稍微不同意", 0), ("完全不同意", 0)]

def _disagrees_score1():
    """For items where DISAGREEING indicates autism (score 1 for 不同意)."""
    return [("完全同意", 0), ("稍微同意", 0), ("稍微不同意", 1), ("完全不同意", 1)]

# 50 items: (order, Chinese text, scoring_function)
# A = agrees_score1, D = disagrees_score1
A = _agrees_score1
D = _disagrees_score1

QUESTIONS = [
    # Social Skills (items 1, 11, 13, 15, 22, 36, 44, 45, 47, 48)
    (1,  "比起和人在一起，我更喜欢和事物打交道。", A),
    (11, "我觉得社交活动很容易。", D),
    (13, "比起自己编故事，我更喜欢编事实。", A),
    (15, "我觉得自己自然而然地就了解了别人在想什么或感受什么。", D),
    (22, "我觉得交新朋友很容易。", D),
    (36, "我喜欢和别人在一起。", D),
    (44, "我喜欢假装自己是别人，即使只是在想象中。", D),
    (45, "我对别人的故事很感兴趣。", D),
    (47, "我喜欢不按常规办事。", A),
    (48, "我在社交场合不知道该怎么表现。", A),

    # Attention Switching (items 2, 4, 10, 16, 25, 32, 34, 37, 43, 46)
    (2,  "我更喜欢反复做同样的事情，而不是尝试新的体验。", A),
    (4,  "我会努力把一件事情做好，即使不太实际。", A),
    (10, "在社交聚会上，我可以很容易地融入不同的人群中。", D),
    (16, "我倾向于注意别人注意不到的细节。", A),
    (25, "我觉得很难判断别人是否对我所说的话感到无聊。", A),
    (32, "我觉得同时做两件以上的事情很困难。", A),
    (34, "我比较喜欢按部就班地做事。", A),
    (37, "当别人改变计划时，我会感到不安。", A),
    (43, "我喜欢按固定的路线去熟悉的地方。", A),
    (46, "当我在做日常事务时，我讨厌被打断。", A),

    # Attention to Detail (items 5, 6, 9, 12, 19, 23, 28, 29, 30, 49)
    (5,  "我经常注意到别人没有注意到的声音或气味。", A),
    (6,  "我通常关注车牌号或类似的序列信息。", A),
    (9,  "我对日期很着迷。", A),
    (12, "我对数字很感兴趣。", A),
    (19, "我对电话号码之类的数字信息很感兴趣。", A),
    (23, "我在阅读故事时很难弄清楚人物的意图。", A),
    (28, "阅读时，我很难从字里行间读出别人的真正意图。", A),
    (29, "我善于在社交场合中读懂别人的心思。", D),
    (30, "我更愿意去图书馆或博物馆，而不是去聚会。", A),
    (49, "我喜欢收集关于事物分类的信息（如各种汽车型号、鸟类种类等）。", A),

    # Communication (items 3, 7, 17, 18, 26, 27, 31, 35, 38, 39)
    (3,  "如果我试着想象什么东西，对我来说这很容易形成一个画面。", D),
    (7, "别人经常说我做事的方式有些特别。", A),
    (17, "我喜欢参加社交活动。", D),
    (18, "我说话的方式经常被别人说太正式或太刻板。", A),
    (26, "我喜欢做有固定规则的活动。", A),
    (27, "在和别人交谈时，我很难判断对方是否感兴趣。", A),
    (31, "我不太善于记住别人的生日。", A),
    (35, "别人经常觉得我的言行让他们感到不舒服。", A),
    (38, "当我在和别人交谈时，我很难同时注意对方的面部表情。", A),
    (39, "我倾向于对别人的话进行非常字面的理解。", A),

    # Imagination (items 8, 14, 20, 21, 24, 33, 40, 41, 42, 50)
    (8,  "当我阅读故事时，我很难想象故事中人物的样子。", A),
    (14, "我喜欢阅读小说。", D),
    (20, "当我读故事时，我很难理解人物之间的关系。", A),
    (21, "我不太善于记住电话号码。", D),
    (24, "我不太善于记住别人的长相。", A),
    (33, "别人经常告诉我我说了不礼貌的话，但我自己并不觉得。", A),
    (40, "小时候，我喜欢和其他小朋友一起玩假装游戏。", D),
    (41, "我喜欢收集信息，按类别整理。", A),
    (42, "我觉得想象自己成为别人会很困难。", A),
    (50, "小时候，我喜欢玩假装游戏（如过家家）。", D),
]

def make_questions():
    return [radio_q(order, text, score_fn()) for order, text, score_fn in QUESTIONS]

def make_dimensions():
    # Social Skills: items 1,11,13,15,22,36,44,45,47,48
    ss_formula = "hx_t_1 + hx_t_11 + hx_t_13 + hx_t_15 + hx_t_22 + hx_t_36 + hx_t_44 + hx_t_45 + hx_t_47 + hx_t_48"
    # Attention Switching: items 2,4,10,16,25,32,34,37,43,46
    as_formula = "hx_t_2 + hx_t_4 + hx_t_10 + hx_t_16 + hx_t_25 + hx_t_32 + hx_t_34 + hx_t_37 + hx_t_43 + hx_t_46"
    # Attention to Detail: items 5,6,9,12,19,23,28,29,30,49
    ad_formula = "hx_t_5 + hx_t_6 + hx_t_9 + hx_t_12 + hx_t_19 + hx_t_23 + hx_t_28 + hx_t_29 + hx_t_30 + hx_t_49"
    # Communication: items 3,7,17,18,26,27,31,35,38,39
    com_formula = "hx_t_3 + hx_t_7 + hx_t_17 + hx_t_18 + hx_t_26 + hx_t_27 + hx_t_31 + hx_t_35 + hx_t_38 + hx_t_39"
    # Imagination: items 8,14,20,21,24,33,40,41,42,50
    im_formula = "hx_t_8 + hx_t_14 + hx_t_20 + hx_t_21 + hx_t_24 + hx_t_33 + hx_t_40 + hx_t_41 + hx_t_42 + hx_t_50"
    # Total
    total_formula = " + ".join(f"hx_t_{i}" for i in range(1, 51))

    return [
        dimension("社交技能", "social_skills", 1, ss_formula, "", [
            result_rule("hx_wd_y_1 <= 2", "社交技能正常",
                "您在社交互动方面表现自然，能够较好地理解和回应他人。", "none"),
            result_rule("hx_wd_y_1 > 2 && hx_wd_y_1 <= 4", "社交技能轻微困难",
                "您在某些社交场合可能感到不太自在，但整体社交能力正常。建议多参与社交活动以增强信心。", "low"),
            result_rule("hx_wd_y_1 > 4 && hx_wd_y_1 <= 6", "社交技能存在困难",
                "您在社交方面存在一些困难，可能需要更多努力来理解社交线索。建议通过社交技能训练来提升。", "middle"),
            result_rule("hx_wd_y_1 > 6", "社交技能显著困难",
                "您在社交方面存在明显困难，这可能是自闭谱系特征的表现。建议寻求专业评估和支持。", "high"),
        ]),
        dimension("注意力转换", "attention_switching", 2, as_formula, "", [
            result_rule("hx_wd_y_2 <= 2", "注意力转换正常",
                "您能够灵活地转换注意力，适应变化的能力良好。", "none"),
            result_rule("hx_wd_y_2 > 2 && hx_wd_y_2 <= 4", "注意力转换轻微困难",
                "您在面对变化时可能需要一些时间来调整，但整体适应能力正常。", "low"),
            result_rule("hx_wd_y_2 > 4 && hx_wd_y_2 <= 6", "注意力转换存在困难",
                "您在转换注意力和适应变化方面存在一些困难，可能更喜欢固定的日常安排。建议尝试逐步引入小变化。", "middle"),
            result_rule("hx_wd_y_2 > 6", "注意力转换显著困难",
                "您在注意力转换和适应变化方面存在明显困难。建议寻求专业评估，了解是否需要额外支持。", "high"),
        ]),
        dimension("细节注意力", "attention_to_detail", 3, ad_formula, "", [
            result_rule("hx_wd_y_3 <= 2", "细节注意力正常",
                "您对细节的关注处于正常范围。", "none"),
            result_rule("hx_wd_y_3 > 2 && hx_wd_y_3 <= 4", "细节注意力稍高",
                "您倾向于关注细节，这在某些工作中可能是优势。", "low"),
            result_rule("hx_wd_y_3 > 4 && hx_wd_y_3 <= 6", "细节注意力较高",
                "您对细节有很强的关注能力，这可能是您的特长。建议将这一优势应用到适合的领域。", "middle"),
            result_rule("hx_wd_y_3 > 6", "细节注意力非常高",
                "您对细节有极高的关注度，这是自闭谱系的一个常见特征。如果这不影响日常生活，可以视为个人优势。", "high"),
        ]),
        dimension("沟通能力", "communication", 4, com_formula, "", [
            result_rule("hx_wd_y_4 <= 2", "沟通能力正常",
                "您在语言沟通方面表现良好，能够理解言外之意和隐含信息。", "none"),
            result_rule("hx_wd_y_4 > 2 && hx_wd_y_4 <= 4", "沟通能力轻微困难",
                "您在某些沟通场合可能需要注意，但整体沟通能力正常。", "low"),
            result_rule("hx_wd_y_4 > 4 && hx_wd_y_4 <= 6", "沟通能力存在困难",
                "您在理解隐含信息和非字面意思方面存在一些困难。建议在重要沟通中多确认对方的意图。", "middle"),
            result_rule("hx_wd_y_4 > 6", "沟通能力显著困难",
                "您在沟通方面存在明显困难，这可能是自闭谱系特征的表现。建议寻求专业评估和支持。", "high"),
        ]),
        dimension("想象力", "imagination", 5, im_formula, "", [
            result_rule("hx_wd_y_5 <= 2", "想象力正常",
                "您在想象力和创造力方面表现正常。", "none"),
            result_rule("hx_wd_y_5 > 2 && hx_wd_y_5 <= 4", "想象力轻微受限",
                "您在某些需要想象力的任务上可能感到不太自在，但整体想象力正常。", "low"),
            result_rule("hx_wd_y_5 > 4 && hx_wd_y_5 <= 6", "想象力存在困难",
                "您在想象力和假装游戏方面存在一些困难。建议通过阅读小说、参与创意活动来锻炼想象力。", "middle"),
            result_rule("hx_wd_y_5 > 6", "想象力显著困难",
                "您在想象力方面存在明显困难，这可能是自闭谱系特征的表现。建议寻求专业评估。", "high"),
        ]),
        dimension("AQ总分", "total", 6, total_formula, "", [
            result_rule("hx_wd_y_6 < 26", "不太可能有自闭谱系特征",
                "您的AQ得分较低，不太可能有自闭谱系障碍（ASD）。您在社交、沟通和想象力等方面的表现处于正常范围。", "none"),
            result_rule("hx_wd_y_6 >= 26 && hx_wd_y_6 < 32", "可能有自闭谱系特征",
                "您的AQ得分处于中间范围，可能存在一些自闭谱系特征。如果这些特征影响了您的日常生活，建议寻求专业评估以了解更多。", "low"),
            result_rule("hx_wd_y_6 >= 32", "提示可能存在自闭谱系特征",
                "您的AQ得分较高，提示可能存在自闭谱系特征。这并不意味着确诊，但建议寻求专业的心理评估，以获得更全面的了解和支持。", "high"),
        ]),
    ]

def build():
    return build_scale(
        title="自闭谱系商数量表(AQ)",
        description="本问卷帮助了解您在社交沟通、注意力、想象力等方面的特点，用于自闭谱系特征的初步筛查。共50题，大约需要10分钟完成。",
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
