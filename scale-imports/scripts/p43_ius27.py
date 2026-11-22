"""P43: IUS-27 - Intolerance of Uncertainty Scale-27 (不确定性不耐受量表)
(Carleton, Norton, & Asmundson, 2007)
27 items, 5-point scale (1-5). Total score 27-135.
2 dimensions: 前瞻性焦虑(Prospective Anxiety, 9 items), 抑制性焦虑(Inhibitory Anxiety, 9 items).
Thresholds: 27-53 低不耐受, 54-80 中等, 81-107 高, 108-135 极高.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "ius27-intolerance-uncertainty"
IMPORT_CODE = "huaxinyun-ius27-intolerance-uncertainty"

# 5-point scale (1-5)
OPTIONS = [
    ("完全不符合", 1),
    ("基本不符合", 2),
    ("一般", 3),
    ("基本符合", 4),
    ("完全符合", 5),
]

# Dimension assignments (1-indexed):
# 前瞻性焦虑: 1,3,4,5,6,7,17,23,26
# 抑制性焦虑: 8,9,11,12,13,14,19,20,24
# Remaining items (not in subscales but in total): 2,10,15,16,18,21,22,25,27

QUESTIONS = [
    (1,  "不确定的事情会让我感到不安。", OPTIONS),
    (2,  "不受自己掌控的事情会让我感到沮丧。", OPTIONS),
    (3,  "不确定的未来会让我感到焦虑。", OPTIONS),
    (4,  "当事情不确定时，我无法放松下来。", OPTIONS),
    (5,  "当我不知道事情会怎样发展时，我很难集中注意力。", OPTIONS),
    (6,  "一个不确定的情境会让我感到很紧张。", OPTIONS),
    (7,  "面对不确定的结果时，我会变得烦躁不安。", OPTIONS),
    (8,  "不确定的状况会阻碍我行动。", OPTIONS),
    (9,  "当我感到不确定时，我会回避采取行动。", OPTIONS),
    (10, "我应该能够提前规划好一切，避免意外。", OPTIONS),
    (11, "当我对某件事不确定时，我很难开始做这件事。", OPTIONS),
    (12, "不确定感让我无法正常生活。", OPTIONS),
    (13, "当结果不确定时，我会一直感到不安。", OPTIONS),
    (14, "面对不确定性时，我会感到自己被束缚住了。", OPTIONS),
    (15, "我必须把所有的不确定性消除掉才能感到安心。", OPTIONS),
    (16, "生活中充满了不确定的事情。", OPTIONS),
    (17, "我无法忍受事情不在自己的掌控之中。", OPTIONS),
    (18, "当我不确定一件事是否会发生时，我会一直关注它。", OPTIONS),
    (19, "不确定感让我无法前进。", OPTIONS),
    (20, "在不确定的情况下做决定让我感到困难。", OPTIONS),
    (21, "我需要确切知道将来会发生什么。", OPTIONS),
    (22, "我讨厌在最后一刻才知道计划变了。", OPTIONS),
    (23, "对未来可能发生的事情感到焦虑。", OPTIONS),
    (24, "当事情不按计划进行时，我会感到非常沮丧。", OPTIONS),
    (25, "一点点的不确定性就足以让我不安。", OPTIONS),
    (26, "在做决定之前，我需要知道所有可能的结果。", OPTIONS),
    (27, "当面对新的或陌生的情况时，我会感到紧张。", OPTIONS),
]

# Dimension item assignments (1-indexed)
PROSPECTIVE_ANXIETY = [1, 3, 4, 5, 6, 7, 17, 23, 26]
INHIBITORY_ANXIETY = [8, 9, 11, 12, 13, 14, 19, 20, 24]

def make_questions():
    return [radio_q(order, text, opts) for order, text, opts in QUESTIONS]

def make_dimensions():
    prospective_formula = " + ".join(f"hx_t_{i}" for i in PROSPECTIVE_ANXIETY)
    inhibitory_formula = " + ".join(f"hx_t_{i}" for i in INHIBITORY_ANXIETY)
    total_formula = q_range(1, 27)

    return [
        # 前瞻性焦虑 (9 items, range 9-45)
        dimension("前瞻性焦虑", "prospective_anxiety", 1, prospective_formula, "", [
            result_rule("hx_wd_y_1 <= 15", "前瞻性焦虑低",
                "您对不确定事件的预期性焦虑较低，面对未知情况时能保持相对平静。", "none"),
            result_rule("hx_wd_y_1 > 15 && hx_wd_y_1 <= 25", "前瞻性焦虑中等",
                "您对不确定事件存在一定程度的预期性焦虑，这是常见的心理反应。建议学习放松技巧来应对焦虑。", "none"),
            result_rule("hx_wd_y_1 > 25 && hx_wd_y_1 <= 35", "前瞻性焦虑较高",
                "您对不确定事件的预期性焦虑较高，可能影响到日常决策和情绪状态。建议关注焦虑管理，必要时可寻求心理咨询。", "low"),
            result_rule("hx_wd_y_1 > 35", "前瞻性焦虑很高",
                "您对不确定事件存在强烈的预期性焦虑，这可能严重影响您的生活质量和决策能力。建议寻求专业的心理评估和干预。", "middle"),
        ]),
        # 抑制性焦虑 (9 items, range 9-45)
        dimension("抑制性焦虑", "inhibitory_anxiety", 2, inhibitory_formula, "", [
            result_rule("hx_wd_y_2 <= 15", "抑制性焦虑低",
                "不确定感很少阻碍您的行动和决策，您能够较好地在不确定情境中前进。", "none"),
            result_rule("hx_wd_y_2 > 15 && hx_wd_y_2 <= 25", "抑制性焦虑中等",
                "不确定性在一定程度上会影响您的行动和决策。建议练习在不确定情境下采取小步行动。", "none"),
            result_rule("hx_wd_y_2 > 25 && hx_wd_y_3 <= 35", "抑制性焦虑较高",
                "不确定性明显阻碍了您的行动能力和日常生活。建议学习接纳不确定性的方法，如正念练习。", "low"),
            result_rule("hx_wd_y_2 > 35", "抑制性焦虑很高",
                "不确定性严重阻碍了您的行动能力，可能已经影响到日常生活和社会功能。建议寻求专业的认知行为治疗帮助。", "middle"),
        ]),
        # 总分 (27 items, range 27-135)
        dimension("不确定性不耐受总分", "total_iu", 3, total_formula, "", [
            result_rule("hx_wd_y_3 <= 53", "低不耐受",
                "您的不确定性不耐受程度较低，表明您能够较好地容忍和应对生活中的不确定情境。这是心理弹性的重要表现。", "none"),
            result_rule("hx_wd_y_3 > 53 && hx_wd_y_3 <= 80", "中等不耐受",
                "您的不确定性不耐受程度处于中等水平，在某些情况下您可能会感到不安或焦虑。建议发展应对不确定性的策略，如认知重评和正念练习。", "none"),
            result_rule("hx_wd_y_3 > 80 && hx_wd_y_3 <= 107", "高不耐受",
                "您的不确定性不耐受程度较高，不确定性可能经常导致您感到焦虑、担忧或行动受限。建议积极学习接纳不确定性的方法，必要时寻求专业心理咨询。", "low"),
            result_rule("hx_wd_y_3 > 107", "极高不耐受",
                "您的不确定性不耐受程度极高，这可能与广泛性焦虑、强迫症或其他焦虑障碍相关。不确定性可能严重影响您的生活质量和日常功能。强烈建议寻求专业的心理评估和认知行为治疗。", "middle"),
        ]),
    ]

def build():
    return build_scale(
        title="不确定性不耐受量表(IUS-27)",
        description="本问卷帮助了解您面对不确定性时的情绪反应和行为倾向。共27题，大约需要5分钟完成。",
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
