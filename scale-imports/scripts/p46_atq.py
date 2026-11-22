"""P46: ATQ - Adult Temperament Questionnaire (成人气质问卷)
(Evans & Rothbart, 2007)
77 items, 7-point scale (1-7).
4 main dimensions with 15 subscales.
Many reverse items.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "atq-adult-temperament"
IMPORT_CODE = "huaxinyun-atq-adult-temperament"

# Normal options (1-7)
OPT_NORMAL = [
    ("完全不符合", 1),
    ("大部分不符合", 2),
    ("有些不符合", 3),
    ("不确定", 4),
    ("有些符合", 5),
    ("大部分符合", 6),
    ("完全符合", 7),
]

# Reverse options (1-7): invert values
OPT_REVERSE = [
    ("完全符合", 1),
    ("大部分符合", 2),
    ("有些符合", 3),
    ("不确定", 4),
    ("有些不符合", 5),
    ("大部分不符合", 6),
    ("完全不符合", 7),
]

# 77 items: (order, text, is_reverse)
# Subscales grouped by main dimension:
#
# I. Effortful Control (努力控制) — 17 items
#    A. Attention (注意力控制) — 6 items: 1,2,3,4,5,6
#    B. Inhibitory Control (抑制控制) — 5 items: 7,8,9,10,11
#    C. Activation Control (激活控制) — 6 items: 12,13,14,15,16,17
#
# II. Negative Affectivity (负性情感性) — 22 items
#    A. Discomfort (不适感) — 5 items: 18,19,20,21,22
#    B. Fear (恐惧) — 5 items: 23,24,25,26,27
#    C. Frustration (挫折感) — 6 items: 28,29,30,31,32,33
#    D. Sadness (悲伤) — 6 items: 34,35,36,37,38,39
#
# III. Extraversion/Surgency (外倾性/活跃性) — 21 items
#    A. Sociability (社交性) — 5 items: 40,41,42,43,44
#    B. Positive Affect (正性情感) — 6 items: 45,46,47,48,49,50
#    C. High Intensity Pleasure (高强度愉悦) — 5 items: 51,52,53,54,55
#    D. Activity Level (活动水平) — 5 items: 56,57,58,59,60
#
# IV. Orienting Sensitivity (感觉敏感性) — 17 items
#    A. Neutral Perceptual Sensitivity (中性感官敏感性) — 5 items: 61,62,63,64,65
#    B. Affective Perceptual Sensitivity (情感感官敏感性) — 6 items: 66,67,68,69,70,71
#    C. Low Intensity Pleasure (低强度愉悦) — 6 items: 72,73,74,75,76,77

QUESTIONS_RAW = [
    # === I. Effortful Control (努力控制) ===
    # A. Attention (注意力控制) — items 1-6
    (1,  "当我需要集中注意力做某件事时，我很容易分心。", True),             # R
    (2,  "在做一件需要长时间集中注意力的事情时，我能很好地保持专注。", False),
    (3,  "我很难将注意力从一件事转移到另一件事上。", True),                # R
    (4,  "即使周围有干扰，我也能保持注意力集中。", False),
    (5,  "阅读或学习时，我的思绪经常飘到别处。", True),                    # R
    (6,  "我能够长时间专注于一项任务而不感到厌倦。", False),

    # B. Inhibitory Control (抑制控制) — items 7-11
    (7,  "在说话之前，我通常能控制住自己先想一想。", False),
    (8,  "我经常在没有考虑后果的情况下就采取行动。", True),                # R
    (9,  "即使很想做某件事，如果时机不合适，我能够等待。", False),
    (10, "我很难抑制自己想要立刻表达想法的冲动。", True),                  # R
    (11, "在做出重要决定之前，我会花时间仔细思考。", False),

    # C. Activation Control (激活控制) — items 12-17
    (12, "即使不想做某件必要的事情，我也能让自己去做。", False),
    (13, "当一项任务变得枯燥时，我很容易放弃。", True),                    # R
    (14, "即使情绪低落，我也能完成应该做的事情。", False),
    (15, "在开始一项困难的任务时，我通常需要很大的意志力。", False),       # reverse = harder to activate
    (16, "我能够坚持完成一件自己不感兴趣但必须要做的事情。", False),
    (17, "当面对一项困难的工作时，我倾向于推迟而不是立即行动。", True),    # R

    # === II. Negative Affectivity (负性情感性) ===
    # A. Discomfort (不适感) — items 18-22
    (18, "陌生的环境会让我感到不自在。", False),
    (19, "温度或天气的小变化很容易让我感到不适。", False),
    (20, "在嘈杂的环境中我感到很不舒服。", False),
    (21, "我比大多数人更容易因为小事而感到烦躁。", False),
    (22, "我对身体的不适（如疼痛、疲劳）非常敏感。", False),

    # B. Fear (恐惧) — items 23-27
    (23, "我会主动回避可能让我感到害怕的场景。", False),
    (24, "面对新的或不确定的情况时，我很少感到害怕。", True),             # R
    (25, "我经常担心不好的事情会发生。", False),
    (26, "我比大多数人更容易感到害怕。", False),
    (27, "想到未来可能遇到的危险会让我感到不安。", False),

    # C. Frustration (挫折感) — items 28-33
    (28, "当事情不按计划进行时，我很容易感到沮丧。", False),
    (29, "当别人做事效率低时，我会感到不耐烦。", False),
    (30, "遇到挫折时，我通常能保持平静。", True),                          # R
    (31, "当被别人打断时，我很少感到恼火。", True),                        # R
    (32, "当排队等待时，我很容易感到烦躁。", False),
    (33, "当我的期望没有实现时，我很难接受。", False),

    # D. Sadness (悲伤) — items 34-39
    (34, "我很少因为生活中的事情而感到悲伤。", True),                      # R
    (35, "听到别人的不幸故事时，我很容易感到难过。", False),
    (36, "当我觉得自己让别人失望了，会感到非常难过。", False),
    (37, "我是一个容易感到忧郁的人。", False),
    (38, "失去对我来说重要的东西时，我比大多数人更难过。", False),
    (39, "回忆过去的遗憾很少让我感到悲伤。", True),                        # R

    # === III. Extraversion/Surgency (外倾性/活跃性) ===
    # A. Sociability (社交性) — items 40-44
    (40, "我喜欢与陌生人交谈。", False),
    (41, "在社交聚会中，我通常会主动与人互动。", False),
    (42, "我更喜欢独处而不是参加社交活动。", True),                        # R
    (43, "与很多人在一起时，我感到精力充沛。", False),
    (44, "在新环境中，我通常比较安静和退缩。", True),                      # R

    # B. Positive Affect (正性情感) — items 45-50
    (45, "我经常因为日常生活中的小事而感到高兴。", False),
    (46, "当好事发生在我身上时，我很少表现出兴奋。", True),                # R
    (47, "我经常感到内心充满喜悦。", False),
    (48, "我很容易被逗笑。", False),
    (49, "对我来说，感受到强烈的快乐是很少有的事情。", True),              # R
    (50, "我经常对生活感到乐观和充满希望。", False),

    # C. High Intensity Pleasure (高强度愉悦) — items 51-55
    (51, "我喜欢参加刺激和冒险的活动。", False),
    (52, "我更喜欢安静的休闲活动而不是刺激的活动。", True),              # R
    (53, "大声的音乐和热闹的氛围让我感到兴奋。", False),
    (54, "我倾向于选择安全和可预测的活动而不是冒险的活动。", True),       # R
    (55, "我喜欢体验速度感和肾上腺素飙升的感觉。", False),

    # D. Activity Level (活动水平) — items 56-60
    (56, "我通常有很高的精力水平。", False),
    (57, "我经常感到疲倦和缺乏活力。", True),                              # R
    (58, "在日常生活中，我走路和做事的速度比较快。", False),
    (59, "我更喜欢安静地坐着而不是四处活动。", True),                      # R
    (60, "我经常觉得有很多事情要做，闲不住。", False),

    # === IV. Orienting Sensitivity (感觉敏感性) ===
    # A. Neutral Perceptual Sensitivity (中性感官敏感性) — items 61-65
    (61, "我能很容易注意到环境中的微小变化。", False),
    (62, "我对光线、声音或气味的变化特别敏感。", False),
    (63, "即使很轻微的声音，我也能注意到。", False),
    (64, "我通常不会注意到背景中的环境变化。", True),                     # R
    (65, "我对周围环境中细微的感官刺激很敏感。", False),

    # B. Affective Perceptual Sensitivity (情感感官敏感性) — items 66-71
    (66, "别人的情绪变化很容易影响到我。", False),
    (67, "我很难察觉到别人的心情变化。", True),                            # R
    (68, "看到他人受苦会让我也感到不舒服。", False),
    (69, "我对别人的面部表情和肢体语言非常敏感。", False),
    (70, "音乐或艺术作品很容易让我产生强烈的情感反应。", False),
    (71, "我不太容易被别人的情绪所影响。", True),                          # R

    # C. Low Intensity Pleasure (低强度愉悦) — items 72-77
    (72, "享受安静的时刻对我来说很重要。", False),
    (73, "在自然环境中散步很少让我感到愉悦。", True),                     # R
    (74, "简单的日常小事（如一杯好茶、一段好音乐）就能让我感到满足。", False),
    (75, "我不太能从安静和慢节奏的活动中获得快乐。", True),                # R
    (76, "品味美好的事物（如美食、美景）是我生活中重要的乐趣。", False),
    (77, "平静和安宁的环境很少让我感到愉悦。", True),                     # R
]

# Subscale item assignments (1-indexed)
ATTENTION = [1, 2, 3, 4, 5, 6]
INHIBITORY_CONTROL = [7, 8, 9, 10, 11]
ACTIVATION_CONTROL = [12, 13, 14, 15, 16, 17]
DISCOMFORT = [18, 19, 20, 21, 22]
FEAR = [23, 24, 25, 26, 27]
FRUSTRATION = [28, 29, 30, 31, 32, 33]
SADNESS = [34, 35, 36, 37, 38, 39]
SOCIABILITY = [40, 41, 42, 43, 44]
POSITIVE_AFFECT = [45, 46, 47, 48, 49, 50]
HIGH_INTENSITY_PLEASURE = [51, 52, 53, 54, 55]
ACTIVITY_LEVEL = [56, 57, 58, 59, 60]
NEUTRAL_PERCEPTUAL = [61, 62, 63, 64, 65]
AFFECTIVE_PERCEPTUAL = [66, 67, 68, 69, 70, 71]
LOW_INTENSITY_PLEASURE = [72, 73, 74, 75, 76, 77]

# Main dimension groupings (subscale indices)
EFFORTFUL_CONTROL_SUBS = [ATTENTION, INHIBITORY_CONTROL, ACTIVATION_CONTROL]
NEGATIVE_AFFECT_SUBS = [DISCOMFORT, FEAR, FRUSTRATION, SADNESS]
EXTRAVERSION_SUBS = [SOCIABILITY, POSITIVE_AFFECT, HIGH_INTENSITY_PLEASURE, ACTIVITY_LEVEL]
ORIENTING_SUBS = [NEUTRAL_PERCEPTUAL, AFFECTIVE_PERCEPTUAL, LOW_INTENSITY_PLEASURE]

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

def _sum_formula(items_1indexed):
    return " + ".join(f"hx_t_{i}" for i in items_1indexed)

def make_dimensions():
    dim_num = 0

    def _subscale_dim(name, code, items, rules):
        nonlocal dim_num
        dim_num += 1
        return dimension(name, code, dim_num, _mean_formula(items), "", rules)

    def _main_dim(name, code, sub_codes, rules):
        nonlocal dim_num
        dim_num += 1
        # Average of all subscale means
        sum_expr = " + ".join(f"hx_wd_y_{sc}" for sc in sub_codes)
        formula = f"({sum_expr}) / {len(sub_codes)}"
        return dimension(name, code, dim_num, formula, "", rules)

    # Common result rules for 7-point mean scales
    def _low_mid_high_7(label_low, label_mid, label_high, label_very_high,
                        text_low, text_mid, text_high, text_very_high):
        return [
            result_rule(f"hx_wd_y_{dim_num} <= 2.5", label_low, text_low, "none"),
            result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", label_mid, text_mid, "none"),
            result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", label_high, text_high, "none"),
            result_rule(f"hx_wd_y_{dim_num} > 5.5", label_very_high, text_very_high, "none"),
        ]

    dims = []

    # ==========================================
    # I. Effortful Control (努力控制) subscales
    # ==========================================
    ec_sub_nums = []

    # Attention
    ec_sub_nums.append(dim_num + 1)
    dims.append(_subscale_dim("注意力控制", "attention", ATTENTION, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "注意力控制较低",
            "您在保持注意力集中方面可能存在较大困难，容易分心。建议尝试番茄工作法等专注力训练方法。", "low"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "注意力控制中等",
            "您的注意力控制能力处于中等水平，在大多数情况下能保持专注，但偶尔也会分心。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "注意力控制较好",
            "您具有较好的注意力控制能力，能够在需要时集中注意力并保持专注。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "注意力控制很好",
            "您具有出色的注意力控制能力，能够长时间保持高度专注，不太容易被外界干扰。", "none"),
    ]))

    # Inhibitory Control
    ec_sub_nums.append(dim_num + 1)
    dims.append(_subscale_dim("抑制控制", "inhibitory_control", INHIBITORY_CONTROL, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "抑制控制较低",
            "您在控制冲动方面可能存在挑战，容易在不加思考的情况下采取行动。建议练习\"暂停-思考-行动\"的策略。", "low"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "抑制控制中等",
            "您的抑制控制能力处于中等水平，在大多数情况下能控制冲动，但某些情境下可能难以抑制。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "抑制控制较好",
            "您具有较好的冲动控制能力，能够在行动前思考后果，做出理性的决定。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "抑制控制很好",
            "您具有出色的自我控制能力，能够很好地抑制冲动，在行动前做出深思熟虑的决定。", "none"),
    ]))

    # Activation Control
    ec_sub_nums.append(dim_num + 1)
    dims.append(_subscale_dim("激活控制", "activation_control", ACTIVATION_CONTROL, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "激活控制较低",
            "您在推动自己完成不想做但必须做的事情方面可能存在较大困难。建议将大任务分解为小步骤，逐步完成。", "low"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "激活控制中等",
            "您的激活控制能力处于中等水平，有时能够推动自己行动，但面对枯燥或困难任务时可能需要额外努力。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "激活控制较好",
            "您具有较好的自我驱动能力，即使面对枯燥或困难的任务也能推动自己去完成。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "激活控制很好",
            "您具有出色的自我驱动和执行能力，能够克服惰性和消极情绪，高效地完成各项任务。", "none"),
    ]))

    # Main dimension: Effortful Control
    ec_main_num = dim_num + 1
    dims.append(_main_dim("努力控制", "effortful_control", ec_sub_nums, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "努力控制水平较低",
            "您的整体努力控制能力较弱，在注意力集中、冲动控制和任务执行方面可能存在挑战。建议系统地培养自我调节能力。", "low"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "努力控制水平中等",
            "您的努力控制能力处于中等水平，在自我调节方面有一定的能力，但仍有提升空间。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "努力控制水平较好",
            "您具有较好的努力控制能力，能够在注意力、冲动控制和任务执行方面表现良好。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "努力控制水平很好",
            "您具有出色的努力控制能力，这是心理弹性的重要保护因素。", "none"),
    ]))

    # ==========================================
    # II. Negative Affectivity (负性情感性) subscales
    # ==========================================
    na_sub_nums = []

    # Discomfort
    na_sub_nums.append(dim_num + 1)
    dims.append(_subscale_dim("不适感", "discomfort", DISCOMFORT, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "不适感较低",
            "您对环境中的不适因素不太敏感，能够较好地适应各种环境条件。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "不适感中等",
            "您对某些环境因素会感到不适，但总体处于正常范围。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "不适感较高",
            "您对环境中的不适因素比较敏感，容易因感官刺激或环境变化而感到不舒服。建议学习适应性应对策略。", "low"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "不适感很高",
            "您对环境中的不适因素非常敏感，这可能影响到日常生活。建议寻求专业评估以了解感官敏感性的管理方法。", "middle"),
    ]))

    # Fear
    na_sub_nums.append(dim_num + 1)
    dims.append(_subscale_dim("恐惧", "fear", FEAR, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "恐惧反应较低",
            "您很少感到害怕，面对新环境和不确定情况时较为从容。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "恐惧反应中等",
            "您在某些情境下会感到恐惧或担忧，这是正常的反应。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "恐惧反应较高",
            "您较容易感到恐惧和担忧，这可能影响您尝试新事物或面对挑战。建议学习渐进式暴露和放松技巧。", "low"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "恐惧反应很高",
            "您非常容易感到恐惧和焦虑，这可能与焦虑障碍相关。建议寻求专业的心理评估和支持。", "middle"),
    ]))

    # Frustration
    na_sub_nums.append(dim_num + 1)
    dims.append(_subscale_dim("挫折感", "frustration", FRUSTRATION, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "挫折感较低",
            "您面对挫折和不如意的事情时能保持较好的情绪稳定性和耐心。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "挫折感中等",
            "在遇到障碍或延迟时，您会有一定程度的挫折感，但总体能较好地应对。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "挫折感较高",
            "您较容易感到挫折和不耐烦，这可能影响情绪和人际关系。建议学习认知重评和情绪调节技巧。", "low"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "挫折感很高",
            "您非常容易感到挫折和愤怒，这可能严重影响日常生活和人际关系。建议寻求专业的愤怒管理帮助。", "middle"),
    ]))

    # Sadness
    na_sub_nums.append(dim_num + 1)
    dims.append(_subscale_dim("悲伤", "sadness", SADNESS, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "悲伤倾向较低",
            "您较少感到悲伤或忧郁，情绪基调较为积极。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "悲伤倾向中等",
            "您在面对负面事件时会感到悲伤，这是正常的情感反应。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "悲伤倾向较高",
            "您较容易感到悲伤和忧郁，可能对生活中的负面事件反应较强烈。建议关注情绪健康，保持社交联系。", "low"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "悲伤倾向很高",
            "您非常容易感到悲伤和忧郁，这可能影响到日常生活。建议寻求专业的心理支持，特别是如果这种倾向持续存在。", "middle"),
    ]))

    # Main dimension: Negative Affectivity
    dims.append(_main_dim("负性情感性", "negative_affectivity", na_sub_nums, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "负性情感性较低",
            "您的负性情感反应较弱，情绪基调积极稳定，较少受到负面情绪的影响。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "负性情感性中等",
            "您的负性情感反应处于中等水平，在压力和负面事件面前有一定的敏感性，但总体能够有效应对。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "负性情感性较高",
            "您的负性情感反应较强，可能较容易体验到恐惧、悲伤、挫折和不适。建议积极发展情绪调节策略。", "low"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "负性情感性很高",
            "您的负性情感反应非常强烈，这可能影响到生活质量和心理健康。建议寻求专业的情绪管理和心理支持。", "middle"),
    ]))

    # ==========================================
    # III. Extraversion/Surgency (外倾性/活跃性) subscales
    # ==========================================
    ex_sub_nums = []

    # Sociability
    ex_sub_nums.append(dim_num + 1)
    dims.append(_subscale_dim("社交性", "sociability", SOCIABILITY, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "社交性较低",
            "您倾向于安静和内敛，在社交场合中可能不太主动。这不代表社交困难，可能是您的个人风格。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "社交性中等",
            "您的社交性处于中等水平，在合适的环境中能享受社交，但也能享受独处时光。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "社交性较高",
            "您是一个善于社交的人，喜欢与人互动，在社交场合中感到舒适和精力充沛。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "社交性很高",
            "您是一个非常外向和善于社交的人，社交活动能给您带来很大的能量和快乐。", "none"),
    ]))

    # Positive Affect
    ex_sub_nums.append(dim_num + 1)
    dims.append(_subscale_dim("正性情感", "positive_affect", POSITIVE_AFFECT, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "正性情感较低",
            "您体验积极情绪（如快乐、兴奋、乐观）的能力可能较弱。建议关注能带来愉悦感的活动。", "low"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "正性情感中等",
            "您能够体验到积极情绪，但强度和频率处于中等水平。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "正性情感较高",
            "您能够经常体验到积极的情绪，对生活保持乐观的态度。这是心理健康的重要保护因素。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "正性情感很高",
            "您具有非常丰富的积极情感体验，经常感到快乐、兴奋和充满希望。这种积极的情感基调有利于心理健康。", "none"),
    ]))

    # High Intensity Pleasure
    ex_sub_nums.append(dim_num + 1)
    dims.append(_subscale_dim("高强度愉悦", "high_intensity_pleasure", HIGH_INTENSITY_PLEASURE, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "高强度愉悦需求较低",
            "您对高强度刺激活动的兴趣较低，更偏好平静和安全的体验。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "高强度愉悦需求中等",
            "您对高强度刺激有适度的兴趣，在冒险和安全之间能取得平衡。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "高强度愉悦需求较高",
            "您喜欢刺激和冒险的体验，享受肾上腺素飙升的感觉。在追求刺激的同时注意安全。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "高强度愉悦需求很高",
            "您对高强度刺激有很强的需求，可能倾向于冒险行为。建议在追求刺激的同时注意风险评估。", "none"),
    ]))

    # Activity Level
    ex_sub_nums.append(dim_num + 1)
    dims.append(_subscale_dim("活动水平", "activity_level", ACTIVITY_LEVEL, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "活动水平较低",
            "您的精力水平和活动倾向较低，更喜欢安静和缓慢的生活节奏。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "活动水平中等",
            "您的活动水平处于中等范围，在需要时能保持活跃，但也能享受安静的时光。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "活动水平较高",
            "您通常精力充沛，喜欢保持忙碌和活跃的生活状态。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "活动水平很高",
            "您具有非常高的精力水平和活动需求，总是充满活力。注意在忙碌中也要给自己安排休息时间。", "none"),
    ]))

    # Main dimension: Extraversion/Surgency
    dims.append(_main_dim("外倾性/活跃性", "extraversion_surgency", ex_sub_nums, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "外倾性/活跃性较低",
            "您的外倾性和活跃性较低，倾向于安静、内敛的生活方式。建议在舒适范围内适当增加社交和活动。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "外倾性/活跃性中等",
            "您的外倾性和活跃性处于中等水平，在社交、积极情感和活动水平方面比较均衡。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "外倾性/活跃性较高",
            "您是一个比较外向、积极和活跃的人，享受社交和刺激性体验。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "外倾性/活跃性很高",
            "您具有很高的外倾性和活跃性，热爱社交、充满活力、追求刺激。在享受积极生活的同时注意适度休息。", "none"),
    ]))

    # ==========================================
    # IV. Orienting Sensitivity (感觉敏感性) subscales
    # ==========================================
    os_sub_nums = []

    # Neutral Perceptual Sensitivity
    os_sub_nums.append(dim_num + 1)
    dims.append(_subscale_dim("中性感官敏感性", "neutral_perceptual", NEUTRAL_PERCEPTUAL, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "中性感官敏感性较低",
            "您对周围环境中的感官刺激不太敏感，可能不太容易注意到环境中的细微变化。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "中性感官敏感性中等",
            "您对环境中的感官刺激有一定的敏感性，能够注意到一些环境变化。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "中性感官敏感性较高",
            "您对环境中的感官刺激比较敏感，能够轻易察觉到光线、声音或气味的变化。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "中性感官敏感性很高",
            "您对环境中的感官刺激非常敏感，可能需要注意避免感官过载。这种敏感性在某些职业中可能是优势。", "none"),
    ]))

    # Affective Perceptual Sensitivity
    os_sub_nums.append(dim_num + 1)
    dims.append(_subscale_dim("情感感官敏感性", "affective_perceptual", AFFECTIVE_PERCEPTUAL, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "情感感官敏感性较低",
            "您对他人的情感和艺术作品的情感表达不太敏感。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "情感感官敏感性中等",
            "您对他人的情感和情感性刺激有一定的感知能力。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "情感感官敏感性较高",
            "您对他人的情感变化和情感性刺激（如音乐、艺术）比较敏感，具有较强的共情能力。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "情感感官敏感性很高",
            "您对他人的情感和情感性刺激非常敏感，具有很强的共情能力。建议注意保护自己的情绪边界。", "none"),
    ]))

    # Low Intensity Pleasure
    os_sub_nums.append(dim_num + 1)
    dims.append(_subscale_dim("低强度愉悦", "low_intensity_pleasure", LOW_INTENSITY_PLEASURE, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "低强度愉悦能力较低",
            "您从安静和慢节奏的活动中获得快乐的能力较弱，可能需要更强的刺激才能感到愉悦。", "low"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "低强度愉悦能力中等",
            "您能从简单的日常事物中获得一定程度的愉悦和满足。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "低强度愉悦能力较高",
            "您善于从简单的事物中发现美和乐趣，能够在安静的时刻享受内心的平静和满足。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "低强度愉悦能力很高",
            "您具有非常强的从简单事物中获得快乐的能力，这是一种珍贵的心理特质。您能够在日常生活中发现美好。", "none"),
    ]))

    # Main dimension: Orienting Sensitivity
    dims.append(_main_dim("感觉敏感性", "orienting_sensitivity", os_sub_nums, [
        result_rule(f"hx_wd_y_{dim_num} <= 2.5", "感觉敏感性较低",
            "您的整体感觉敏感性较低，对环境刺激和他人情感的感知不太敏锐。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 2.5 && hx_wd_y_{dim_num} <= 4.0", "感觉敏感性中等",
            "您的感觉敏感性处于中等水平，对环境和情感刺激有一定的感知能力。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 4.0 && hx_wd_y_{dim_num} <= 5.5", "感觉敏感性较高",
            "您的感觉敏感性较高，对环境变化和他人情感有较强的感知能力。这可能是一种优势，但也要注意避免感官过载。", "none"),
        result_rule(f"hx_wd_y_{dim_num} > 5.5", "感觉敏感性很高",
            "您的感觉敏感性非常高，对各种感官和情感刺激都非常敏锐。建议学习自我保护策略，避免感官和情感过载。", "low"),
    ]))

    return dims

def build():
    return build_scale(
        title="成人气质问卷(ATQ)",
        description="本问卷帮助了解您在注意力控制、情绪反应、社交倾向等方面的气质特点。共77题，大约需要15分钟完成。",
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
