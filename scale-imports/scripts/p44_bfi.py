"""P44: BFI - Big Five Inventory (大五人格量表)
(John & Srivastava, 1999)
44 items, 5-point scale (1-5). Each dimension scored as mean.
5 dimensions: 外倾性(8), 宜人性(9), 责任感(9), 神经质(8), 开放性(10).
Many reverse items (marked with R).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "bfi-big-five"
IMPORT_CODE = "huaxinyun-bfi-big-five"

# Normal options (1-5)
OPT_NORMAL = [
    ("完全不同意", 1),
    ("不太同意", 2),
    ("既不同意也不否定", 3),
    ("比较同意", 4),
    ("完全同意", 5),
]

# Reverse options (1-5): invert values
OPT_REVERSE = [
    ("完全同意", 1),
    ("比较同意", 2),
    ("既不同意也不否定", 3),
    ("不太同意", 4),
    ("完全不同意", 5),
]

# 44 items: (order, text, is_reverse)
# BFI factor structure:
#   E (Extraversion): 1R, 6, 11R, 16, 21R, 26, 31R, 36
#   A (Agreeableness): 2R, 7, 12R, 17, 22R, 27R, 32, 37R, 42
#   C (Conscientiousness): 3, 8R, 13, 18R, 23R, 28, 33R, 38, 43R
#   N (Neuroticism): 4, 9R, 14, 19R, 24, 29R, 34, 39R
#   O (Openness): 5, 10, 15R, 20, 25, 30R, 35, 40R, 41R, 44
QUESTIONS_RAW = [
    # Extraversion
    (1,  "是一个健谈的人。", False),                   # E1 → reverse: reserved → 健谈
    (2,  "倾向于挑别人的毛病。", False),               # A2R → 倾向于挑毛病 = low agreeableness
    (3,  "做事认真仔细。", False),                      # C3
    (4,  "情绪容易低落、忧郁。", False),                # N4
    (5,  "有独创性，能提出新想法。", False),             # O5

    (6,  "性格内向、沉默寡言。", True),                 # E6R → reverse
    (7,  "乐于助人、不自私。", False),                  # A7
    (8,  "做事比较懒散。", False),                      # C8R → 懒散 = low C
    (9,  "情绪稳定、不易心烦。", True),                 # N9R → reverse: 情绪稳定 = low N
    (10, "对很多事物充满好奇。", False),                # O10

    # Agreeableness
    (11, "精力充沛。", False),                          # E11
    (12, "经常和别人起冲突。", False),                  # A12R → 冲突 = low A
    (13, "是可靠的、可信赖的人。", False),              # C13
    (14, "情绪波动很大。", False),                      # N14
    (15, "善于用艺术、音乐或文学表达自己。", False),    # O15 → in O factor

    (16, "比较安静。", True),                           # E16R → reverse
    (17, "对人有同情心。", False),                      # A17
    (18, "做事有条理。", False),                        # C18
    (19, "遇事沉着冷静。", True),                       # N19R → reverse
    (20, "对抽象概念感兴趣。", False),                  # O20

    # Conscientiousness
    (21, "精力旺盛。", False),                          # E21
    (22, "对人比较冷淡。", False),                      # A22R → 冷淡 = low A
    (23, "做事有持久性、能坚持到底。", False),          # C23
    (24, "容易感到紧张。", False),                      # N24
    (25, "想象力丰富。", False),                        # O25

    (26, "喜欢和别人在一起。", False),                  # E26
    (27, "对人态度粗鲁。", False),                      # A27R → 粗鲁 = low A
    (28, "做事有效率。", False),                        # C28
    (29, "遇事不担心。", True),                         # N29R → reverse
    (30, "对艺术品不感兴趣。", True),                   # O30R → reverse: 不感兴趣 = low O

    # Neuroticism
    (31, "喜欢和人交往。", False),                      # E31 → reverse coding by structure
    (32, "经常为别人着想。", False),                    # A32
    (33, "经常迟到。", False),                          # C33R → 迟到 = low C
    (34, "容易担忧。", False),                          # N34
    (35, "思维方式新颖独特。", False),                  # O35

    (36, "喜欢合作而非竞争。", False),                  # E36 (treated as E item)
    (37, "容易原谅别人。", False),                      # A37
    (38, "注重细节。", False),                          # C38
    (39, "遇事不焦虑。", True),                         # N39R → reverse
    (40, "对文化体验不感兴趣。", True),                 # O40R → reverse

    # Openness
    (41, "对艺术和审美不感兴趣。", True),               # O41R → reverse
    (42, "喜欢与人合作。", False),                      # A42
    (43, "容易分心。", False),                          # C43R → 分心 = low C
    (44, "对新事物持开放态度。", False),                # O44
]

# Dimension assignments (0-indexed based on question order 1-44 → indices 0-43)
E_ITEMS = [0, 5, 10, 15, 20, 25, 30, 35]                    # items 1,6,11,16,21,26,31,36
A_ITEMS = [1, 6, 11, 16, 21, 26, 31, 36, 41]                # items 2,7,12,17,22,27,32,37,42
C_ITEMS = [2, 7, 12, 17, 22, 27, 32, 37, 42]                # items 3,8,13,18,23,28,33,38,43
N_ITEMS = [3, 8, 13, 18, 23, 28, 33, 38]                    # items 4,9,14,19,24,29,34,39
O_ITEMS = [4, 9, 14, 19, 24, 29, 34, 39, 40, 43]            # items 5,10,15,20,25,30,35,40,41,44

# Note: O includes index 40 (item 41) and index 43 (item 44)
# E items 1-indexed: 1,6,11,16,21,26,31,36
# A items 1-indexed: 2,7,12,17,22,27,32,37,42
# C items 1-indexed: 3,8,13,18,23,28,33,38,43
# N items 1-indexed: 4,9,14,19,24,29,34,39
# O items 1-indexed: 5,10,15,20,25,30,35,40,41,44

E_ITEMS_1 = [1, 6, 11, 16, 21, 26, 31, 36]
A_ITEMS_1 = [2, 7, 12, 17, 22, 27, 32, 37, 42]
C_ITEMS_1 = [3, 8, 13, 18, 23, 28, 33, 38, 43]
N_ITEMS_1 = [4, 9, 14, 19, 24, 29, 34, 39]
O_ITEMS_1 = [5, 10, 15, 20, 25, 30, 35, 40, 41, 44]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        opts = OPT_REVERSE if is_rev else OPT_NORMAL
        qs.append(radio_q(order, text, opts))
    return qs

def _mean_formula(items_1indexed):
    """Build a mean formula: (sum of items) / count."""
    sum_parts = " + ".join(f"hx_t_{i}" for i in items_1indexed)
    return f"({sum_parts}) / {len(items_1indexed)}"

def make_dimensions():
    e_formula = _mean_formula(E_ITEMS_1)
    a_formula = _mean_formula(A_ITEMS_1)
    c_formula = _mean_formula(C_ITEMS_1)
    n_formula = _mean_formula(N_ITEMS_1)
    o_formula = _mean_formula(O_ITEMS_1)

    return [
        # Extraversion (8 items, mean 1-5)
        dimension("外倾性", "extraversion", 1, e_formula, "", [
            result_rule("hx_wd_y_1 <= 2.0", "外倾性较低",
                "您倾向于安静和内敛，更喜欢独处或小范围社交。您可能在社交场合中感到消耗精力，更享受独处的时间。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.0", "外倾性中等",
                "您的外倾性处于中等水平，在社交和独处之间能较好地平衡。在熟悉的人面前您会比较活跃，但也能享受独处。", "none"),
            result_rule("hx_wd_y_1 > 3.0 && hx_wd_y_1 <= 4.0", "外倾性较高",
                "您是一个比较外向的人，喜欢社交活动，善于与人互动。社交能给您带来能量和积极情绪。", "none"),
            result_rule("hx_wd_y_1 > 4.0", "外倾性很高",
                "您是一个非常外向的人，热爱社交，精力充沛，善于表达。您在群体中通常比较活跃，喜欢成为关注的中心。", "none"),
        ]),
        # Agreeableness (9 items, mean 1-5)
        dimension("宜人性", "agreeableness", 2, a_formula, "", [
            result_rule("hx_wd_y_2 <= 2.0", "宜人性较低",
                "您在人际交往中倾向于直接和独立，可能不太在意他人的感受或不太愿意迁就他人。建议在保持自我的同时适当关注他人需求。", "low"),
            result_rule("hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.0", "宜人性中等",
                "您的宜人性处于中等水平，能够在维护自身利益和关心他人之间取得平衡。", "none"),
            result_rule("hx_wd_y_2 > 3.0 && hx_wd_y_2 <= 4.0", "宜人性较高",
                "您是一个温和友善、富有同情心的人，善于理解和关心他人。您通常能够与不同类型的人和谐相处。", "none"),
            result_rule("hx_wd_y_2 > 4.0", "宜人性很高",
                "您是一个非常友善和有同情心的人，总是为他人着想。但也要注意在必要时坚持自己的立场和需求。", "none"),
        ]),
        # Conscientiousness (9 items, mean 1-5)
        dimension("责任感", "conscientiousness", 3, c_formula, "", [
            result_rule("hx_wd_y_3 <= 2.0", "责任感较低",
                "您在组织和自律方面可能存在一些挑战，做事可能不太注重计划和细节。建议尝试建立日常规律和制定小目标来提升效率。", "low"),
            result_rule("hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.0", "责任感中等",
                "您的责任感处于中等水平，能够在需要时保持专注和有条理，但也有灵活放松的一面。", "none"),
            result_rule("hx_wd_y_3 > 3.0 && hx_wd_y_3 <= 4.0", "责任感较高",
                "您是一个认真负责、有条理的人，能够有效地计划和执行任务。您的可靠性和自律性帮助您在学业和工作中取得好成绩。", "none"),
            result_rule("hx_wd_y_3 > 4.0", "责任感很高",
                "您是一个非常有责任感的人，做事严谨有序，自律性强。您注重计划和细节，是值得信赖的人。但也注意不要给自己过大的压力。", "none"),
        ]),
        # Neuroticism (8 items, mean 1-5)
        dimension("神经质", "neuroticism", 4, n_formula, "", [
            result_rule("hx_wd_y_4 <= 2.0", "情绪稳定性高",
                "您的情绪非常稳定，面对压力和挫折时能够保持冷静和理性。您很少感到焦虑或沮丧，心理韧性较强。", "none"),
            result_rule("hx_wd_y_4 > 2.0 && hx_wd_y_4 <= 3.0", "情绪稳定性中等",
                "您的情绪稳定性处于中等水平，在大多数情况下能保持平稳，但偶尔也会感到焦虑或情绪波动。", "none"),
            result_rule("hx_wd_y_4 > 3.0 && hx_wd_y_4 <= 4.0", "情绪敏感性较高",
                "您是一个情绪比较敏感的人，容易受到压力和负面事件的影响。建议学习情绪调节技巧，如正念冥想和深呼吸等。", "low"),
            result_rule("hx_wd_y_4 > 4.0", "情绪敏感性很高",
                "您的情绪波动较大，容易感到焦虑、担忧或沮丧。这可能影响到日常生活和决策。建议关注心理健康，学习有效的情绪管理方法，必要时可寻求专业支持。", "middle"),
        ]),
        # Openness (10 items, mean 1-5)
        dimension("开放性", "openness", 5, o_formula, "", [
            result_rule("hx_wd_y_5 <= 2.0", "开放性较低",
                "您倾向于传统和务实的生活方式，对新奇事物和抽象概念的兴趣较低。您更喜欢熟悉和可预测的环境。", "none"),
            result_rule("hx_wd_y_5 > 2.0 && hx_wd_y_5 <= 3.0", "开放性中等",
                "您的开放性处于中等水平，对新事物有一定的接受能力，但也不会过度追求新奇体验。", "none"),
            result_rule("hx_wd_y_5 > 3.0 && hx_wd_y_5 <= 4.0", "开放性较高",
                "您是一个思想开放、好奇心强的人，喜欢探索新想法和体验。您对艺术、文化和创造性活动有较高的兴趣。", "none"),
            result_rule("hx_wd_y_5 > 4.0", "开放性很高",
                "您是一个非常开放和富有创造力的人，对各种新奇事物充满好奇。您善于抽象思考，对艺术和文化有深厚的兴趣和鉴赏力。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="大五人格量表(BFI)",
        description="本问卷帮助了解您在五个核心人格维度上的特征：外倾性、宜人性、责任感、神经质和开放性。共44题，大约需要8分钟完成。",
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
