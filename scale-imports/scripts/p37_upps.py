"""P37: UPPS-P - UPPS-P Impulsive Behavior Scale Short Form (冲动行为量表简版)
(Cyders et al., 2007; Lynam et al., 2006)
20 items, 4-point scale (1-4). Total score 20-80.
5 dimensions (4 items each): 负性急迫性, 缺少预先考虑, 快感寻求, 缺少毅力, 正性急迫性.
Reverse items (1-indexed): 2, 4, 6, 8, 12, 14, 16, 20.
Thresholds: 20-35 低冲动, 36-50 中等, 51-65 较高, 66-80 高冲动.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "uppsp-impulsivity"
IMPORT_CODE = "huaxinyun-uppsp-impulsivity"

# Normal options (1-4): higher agreement = more impulsive
OPTIONS_NORMAL = [
    ("非常不同意", 1),
    ("有些不同意", 2),
    ("有些同意", 3),
    ("非常同意", 4),
]

# Reverse options (1-4): higher agreement = less impulsive (invert values)
OPTIONS_REVERSE = [
    ("非常不同意", 4),
    ("有些不同意", 3),
    ("有些同意", 2),
    ("非常同意", 1),
]

# 20 items: (order, Chinese text, options)
# Dimensions:
#   负性急迫性 (1-4), 缺少预先考虑 (5-8), 快感寻求 (9-12),
#   缺少毅力 (13-16), 正性急迫性 (17-20)
# Reverse items (1-indexed): 2, 4, 6, 8, 12, 14, 16, 20
QUESTIONS = [
    # 负性急迫性 (Negative Urgency)
    (1,  "当我感到沮丧时，我往往会做一些事后会后悔的事情来让自己好受一些。", OPTIONS_NORMAL),
    (2,  "即使在心情不好的时候，我也能控制自己的行为。", OPTIONS_REVERSE),              # reverse
    (3,  "当我感到心烦意乱时，我往往会做出冲动的决定。", OPTIONS_NORMAL),
    (4,  "即使情绪低落时，我也能保持冷静和理性。", OPTIONS_REVERSE),                    # reverse

    # 缺少预先考虑 (Lack of Premeditation)
    (5,  "我做事往往不假思索。", OPTIONS_NORMAL),
    (6,  "在做决定之前，我会仔细考虑各种可能的结果。", OPTIONS_REVERSE),                # reverse
    (7,  "我通常会先行动再思考。", OPTIONS_NORMAL),
    (8,  "我在采取行动之前会认真思考可能的后果。", OPTIONS_REVERSE),                    # reverse

    # 快感寻求 (Sensation Seeking)
    (9,  "我喜欢冒险和寻求刺激的体验。", OPTIONS_NORMAL),
    (10, "我喜欢做大胆和刺激的事情。", OPTIONS_NORMAL),
    (11, "我更喜欢兴奋和冒险的生活方式，而不是平静和可预测的生活。", OPTIONS_NORMAL),
    (12, "我更喜欢稳定和安全的生活，而不是充满冒险的生活。", OPTIONS_REVERSE),         # reverse

    # 缺少毅力 (Lack of Perseverance)
    (13, "我很难集中精力完成一项任务。", OPTIONS_NORMAL),
    (14, "一旦开始做一件事，我通常会坚持到底。", OPTIONS_REVERSE),                      # reverse
    (15, "我经常半途而废。", OPTIONS_NORMAL),
    (16, "即使遇到困难，我也会坚持完成已经开始的事情。", OPTIONS_REVERSE),              # reverse

    # 正性急迫性 (Positive Urgency)
    (17, "当我非常开心的时候，我往往会做出一些冲动的事情。", OPTIONS_NORMAL),
    (18, "当心情特别好的时候，我可能会做出一些事后后悔的决定。", OPTIONS_NORMAL),
    (19, "当我兴奋的时候，我往往会不假思索地说出一些话。", OPTIONS_NORMAL),
    (20, "即使在非常开心的时候，我也能控制自己的冲动。", OPTIONS_REVERSE),              # reverse
]

def make_questions():
    return [radio_q(order, text, opts) for order, text, opts in QUESTIONS]

def make_dimensions():
    neg_urgency  = " + ".join(f"hx_t_{i}" for i in range(1, 5))    # items 1-4
    lpremed      = " + ".join(f"hx_t_{i}" for i in range(5, 9))    # items 5-8
    sensation    = " + ".join(f"hx_t_{i}" for i in range(9, 13))   # items 9-12
    lpersev      = " + ".join(f"hx_t_{i}" for i in range(13, 17))  # items 13-16
    pos_urgency  = " + ".join(f"hx_t_{i}" for i in range(17, 21))  # items 17-20
    total        = q_range(1, 20)

    return [
        # Dimension 1: 负性急迫性 (4 items, range 4-16)
        dimension("负性急迫性", "neg_urgency", 1, neg_urgency, "", [
            result_rule("hx_wd_y_1 <= 7", "负性急迫性较低",
                "您在负面情绪下的冲动性较低，能够较好地控制自己在情绪低落时的行为。", "none"),
            result_rule("hx_wd_y_1 > 7 && hx_wd_y_1 <= 10", "负性急迫性中等",
                "您在负面情绪下偶尔会出现冲动行为，属于正常范围。建议学习情绪调节技巧，以便更好地管理情绪驱动的冲动。", "none"),
            result_rule("hx_wd_y_1 > 10 && hx_wd_y_1 <= 13", "负性急迫性较高",
                "您在负面情绪下容易做出冲动决定，建议关注情绪管理，学习正念等调节方法，避免在情绪低落时做出让自己后悔的行为。", "low"),
            result_rule("hx_wd_y_1 > 13", "负性急迫性很高",
                "您在负面情绪下的冲动性非常高，可能已经对生活造成了影响。建议寻求专业心理咨询，学习有效的情绪调节和冲动控制策略。", "middle"),
        ]),
        # Dimension 2: 缺少预先考虑 (4 items, range 4-16)
        dimension("缺少预先考虑", "lack_premeditation", 2, lpremed, "", [
            result_rule("hx_wd_y_2 <= 7", "预先考虑能力良好",
                "您在行动前能够充分思考和计划，具有良好的预判能力。", "none"),
            result_rule("hx_wd_y_2 > 7 && hx_wd_y_2 <= 10", "预先考虑能力中等",
                "您在行动前的思考能力处于正常范围，偶尔可能会冲动行事。建议在重要决定前给自己留出思考的时间。", "none"),
            result_rule("hx_wd_y_2 > 10 && hx_wd_y_2 <= 13", "缺少预先考虑",
                "您在行动前可能缺乏充分的思考，容易不经考虑就做出决定。建议培养「暂停-思考-行动」的习惯。", "low"),
            result_rule("hx_wd_y_2 > 13", "严重缺少预先考虑",
                "您在行动前很少进行充分的思考和计划，这可能影响到您的决策质量和生活。建议寻求专业指导，提升计划和预判能力。", "middle"),
        ]),
        # Dimension 3: 快感寻求 (4 items, range 4-16)
        dimension("快感寻求", "sensation_seeking", 3, sensation, "", [
            result_rule("hx_wd_y_3 <= 7", "快感寻求较低",
                "您对新奇和刺激体验的需求较低，更倾向于稳定和安全的生活方式。", "none"),
            result_rule("hx_wd_y_3 > 7 && hx_wd_y_3 <= 10", "快感寻求中等",
                "您对新奇体验的需求处于正常范围，能够平衡冒险和安全之间的关系。", "none"),
            result_rule("hx_wd_y_3 > 10 && hx_wd_y_3 <= 13", "快感寻求较高",
                "您对刺激和冒险体验有较高的需求，建议在追求刺激的同时注意安全和风险评估。", "none"),
            result_rule("hx_wd_y_3 > 13", "快感寻求很高",
                "您对刺激和冒险体验的需求非常高，可能会因为追求刺激而忽视潜在风险。建议在满足好奇心的同时保持理性的风险意识。", "low"),
        ]),
        # Dimension 4: 缺少毅力 (4 items, range 4-16)
        dimension("缺少毅力", "lack_perseverance", 4, lpersev, "", [
            result_rule("hx_wd_y_4 <= 7", "毅力良好",
                "您具有良好的坚持能力，能够专注于完成任务和目标。", "none"),
            result_rule("hx_wd_y_4 > 7 && hx_wd_y_4 <= 10", "毅力中等",
                "您的坚持能力处于正常范围，偶尔可能会在遇到困难时放弃。建议设定阶段性目标以保持动力。", "none"),
            result_rule("hx_wd_y_4 > 10 && hx_wd_y_4 <= 13", "缺少毅力",
                "您在完成任务和坚持目标方面可能存在困难，建议学习时间管理技巧，将大目标分解为小步骤逐步完成。", "low"),
            result_rule("hx_wd_y_4 > 13", "严重缺少毅力",
                "您在坚持完成任务方面存在明显困难，可能影响到学业或工作表现。建议寻求专业指导，提升自我管理和执行功能。", "middle"),
        ]),
        # Dimension 5: 正性急迫性 (4 items, range 4-16)
        dimension("正性急迫性", "pos_urgency", 5, pos_urgency, "", [
            result_rule("hx_wd_y_5 <= 7", "正性急迫性较低",
                "您在积极情绪下能够保持较好的行为控制，不易因兴奋而冲动行事。", "none"),
            result_rule("hx_wd_y_5 > 7 && hx_wd_y_5 <= 10", "正性急迫性中等",
                "您在积极情绪下偶尔会出现冲动行为，属于正常范围。建议在开心时也保持适度的自我觉察。", "none"),
            result_rule("hx_wd_y_5 > 10 && hx_wd_y_5 <= 13", "正性急迫性较高",
                "您在积极情绪下容易做出冲动决定，建议学会在兴奋和快乐时也保持冷静思考。", "low"),
            result_rule("hx_wd_y_5 > 13", "正性急迫性很高",
                "您在积极情绪下的冲动性非常高，可能会在兴奋时做出不理性的决定。建议培养情绪觉察能力，在任何情绪状态下都保持适度的思考。", "middle"),
        ]),
        # Total (20 items, range 20-80)
        dimension("冲动性总分", "total_impulsivity", 6, total, "", [
            result_rule("hx_wd_y_6 <= 35", "低冲动水平",
                "您的总体冲动性水平较低，具有较好的自我控制和决策能力。请继续保持。", "none"),
            result_rule("hx_wd_y_6 > 35 && hx_wd_y_6 <= 50", "中等冲动水平",
                "您的总体冲动性水平处于中等范围，说明您在某些情境下可能会出现冲动行为。建议关注自身的冲动模式，学习适当的自我调节策略。", "none"),
            result_rule("hx_wd_y_6 > 50 && hx_wd_y_6 <= 65", "较高冲动水平",
                "您的总体冲动性水平较高，可能在情绪管理、行为控制和决策方面存在一定的困难。建议积极学习冲动控制技巧，必要时可寻求专业心理咨询。", "low"),
            result_rule("hx_wd_y_6 > 65 && hx_wd_y_6 <= 80", "高冲动水平",
                "您的总体冲动性水平很高，可能在多个方面存在明显的冲动行为，已经影响到日常生活和人际关系。强烈建议寻求专业的心理咨询和行为干预。", "high"),
        ]),
    ]

def build():
    return build_scale(
        title="UPPS-P冲动行为量表(UPPS-P)",
        description="本问卷帮助了解您在冲动性方面的五个不同维度，包括情绪冲动和行为冲动。共20题，大约需要4分钟完成。",
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
