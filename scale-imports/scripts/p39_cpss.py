"""P39: CPSS-14 - Chinese Perceived Stress Scale (中文版知觉压力量表)
(Yang & Huang, 2003; adapted from Cohen et al., 1983)
14 items, 5-point scale (0-4). Total score 0-56.
2 dimensions: 紧张感 (7 items), 失控感 (7 items, all reverse-scored).
Reverse items (1-indexed): 4, 5, 6, 7, 9, 10, 13.
Thresholds: 0-18 低压力, 19-36 中等压力, 37-56 高压力.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "cpss14-stress"
IMPORT_CODE = "huaxinyun-cpss14-stress"

# Normal options (0-4): higher frequency = more stress
OPTIONS_NORMAL = [
    ("从不", 0),
    ("很少", 1),
    ("有时", 2),
    ("经常", 3),
    ("总是", 4),
]

# Reverse options (0-4): higher frequency = less control, reverse to = more stress
# Original: 从不=0, 很少=1, 有时=2, 经常=3, 总是=4
# Reversed: 从不=4, 很少=3, 有时=2, 经常=1, 总是=0
OPTIONS_REVERSE = [
    ("从不", 4),
    ("很少", 3),
    ("有时", 2),
    ("经常", 1),
    ("总是", 0),
]

# 14 items: (order, Chinese text, options)
# 紧张感 items (1-indexed): 1, 2, 3, 8, 11, 12, 14 (no reverse)
# 失控感 items (1-indexed): 4, 5, 6, 7, 9, 10, 13 (all reverse)
QUESTIONS = [
    # 紧张感 (Tension) - no reverse
    (1,  "在过去一个月中，有多少时候您因为发生了意想不到的事情而感到心烦意乱？", OPTIONS_NORMAL),
    (2,  "在过去一个月中，有多少时候您感到自己无法控制生活中的重要事情？", OPTIONS_NORMAL),
    (3,  "在过去一个月中，有多少时候您感到紧张和有压力？", OPTIONS_NORMAL),
    # 失控感 (Loss of Control) - reverse scored
    (4,  "在过去一个月中，有多少时候您感到自己有信心能够处理好个人问题？", OPTIONS_REVERSE),       # reverse
    (5,  "在过去一个月中，有多少时候您感到事情正按照您的意愿发展？", OPTIONS_REVERSE),               # reverse
    (6,  "在过去一个月中，有多少时候您能够控制生活中令您生气的事情？", OPTIONS_REVERSE),             # reverse
    (7,  "在过去一个月中，有多少时候您感到自己能够掌控生活中发生的事情？", OPTIONS_REVERSE),         # reverse
    # 紧张感
    (8,  "在过去一个月中，有多少时候您因为事情超出您的控制范围而感到不安？", OPTIONS_NORMAL),
    # 失控感 - reverse scored
    (9,  "在过去一个月中，有多少时候您能够有效地处理日常生活中的烦恼？", OPTIONS_REVERSE),           # reverse
    (10, "在过去一个月中，有多少时候您觉得自己能够应对生活中出现的大部分问题？", OPTIONS_REVERSE),   # reverse
    # 紧张感
    (11, "在过去一个月中，有多少时候您感到困难重重无法克服？", OPTIONS_NORMAL),
    (12, "在过去一个月中，有多少时候您因为担心某些事情而感到焦虑？", OPTIONS_NORMAL),
    # 失控感 - reverse scored
    (13, "在过去一个月中，有多少时候您觉得自己能够控制自己利用时间的方式？", OPTIONS_REVERSE),       # reverse
    # 紧张感
    (14, "在过去一个月中，有多少时候您感到自己处于极大的压力之下？", OPTIONS_NORMAL),
]

# Item assignments for dimensions
TENSION_ITEMS = [1, 2, 3, 8, 11, 12, 14]       # 紧张感 (1-indexed)
LOSS_CTRL_ITEMS = [4, 5, 6, 7, 9, 10, 13]       # 失控感 (1-indexed)

def make_questions():
    return [radio_q(order, text, opts) for order, text, opts in QUESTIONS]

def make_dimensions():
    tension_formula = " + ".join(f"hx_t_{i}" for i in TENSION_ITEMS)
    loss_ctrl_formula = " + ".join(f"hx_t_{i}" for i in LOSS_CTRL_ITEMS)
    total_formula = q_range(1, 14)

    return [
        # Dimension 1: 紧张感 (7 items, range 0-28)
        dimension("紧张感", "tension", 1, tension_formula, "", [
            result_rule("hx_wd_y_1 <= 7", "紧张感较低",
                "您的紧张感水平较低，说明您近期在情绪上较为放松，没有明显的紧张和焦虑。请继续保持良好的心态。", "none"),
            result_rule("hx_wd_y_1 > 7 && hx_wd_y_1 <= 14", "紧张感中等",
                "您的紧张感处于中等水平，说明您近期经历了一定程度的紧张和压力。建议关注自身的压力来源，适当采取放松措施，如深呼吸、运动或与朋友交流。", "none"),
            result_rule("hx_wd_y_1 > 14 && hx_wd_y_1 <= 21", "紧张感较高",
                "您的紧张感水平较高，说明您近期承受了较大的心理压力，经常感到紧张和焦虑。建议积极寻求减压方式，必要时可向心理咨询师寻求帮助。", "low"),
            result_rule("hx_wd_y_1 > 21", "紧张感非常高",
                "您的紧张感水平非常高，说明您近期持续处于高度紧张和焦虑的状态。强烈建议尽快寻求专业的心理咨询或医疗帮助，以避免长期压力对身心健康的不良影响。", "high"),
        ]),
        # Dimension 2: 失控感 (7 items, range 0-28, all reverse-scored)
        dimension("失控感", "loss_of_control", 2, loss_ctrl_formula, "", [
            result_rule("hx_wd_y_2 <= 7", "失控感较低",
                "您的失控感水平较低，说明您对自己生活中的事情有较好的掌控感，能够有效处理日常问题。请继续保持。", "none"),
            result_rule("hx_wd_y_2 > 7 && hx_wd_y_2 <= 14", "失控感中等",
                "您的失控感处于中等水平，说明您在某些时候可能会感到对生活缺乏掌控。建议重新审视自己的目标和优先事项，提升自我效能感。", "none"),
            result_rule("hx_wd_y_2 > 14 && hx_wd_y_2 <= 21", "失控感较高",
                "您的失控感水平较高，说明您近期经常感到无法掌控生活中的重要事情。建议学习时间管理和问题解决技巧，提升对生活的掌控感。", "low"),
            result_rule("hx_wd_y_2 > 21", "失控感非常高",
                "您的失控感水平非常高，说明您近期持续感到对生活缺乏掌控。这可能与长期压力和无力感有关。强烈建议寻求专业心理咨询，学习有效的应对策略。", "high"),
        ]),
        # Total score (14 items, range 0-56)
        dimension("知觉压力总分", "total_stress", 3, total_formula, "", [
            result_rule("hx_wd_y_3 <= 18", "低压力水平",
                "您的总体知觉压力水平较低，说明您近期的生活压力较小，心理状态较为轻松。建议继续保持积极的生活方式和有效的压力管理习惯。", "none"),
            result_rule("hx_wd_y_3 > 18 && hx_wd_y_3 <= 36", "中等压力水平",
                "您的总体知觉压力处于中等水平，说明您近期经历了一定程度的生活压力。建议关注自身的压力来源，适当采取减压措施，如规律运动、充足睡眠和社交活动。", "none"),
            result_rule("hx_wd_y_3 > 36 && hx_wd_y_3 <= 56", "高压力水平",
                "您的总体知觉压力水平较高，说明您近期承受了较大的生活压力，可能已经影响到身心健康。建议积极寻求减压方式，必要时可向专业心理咨询师寻求帮助，以避免长期压力对身体和心理造成不良影响。", "high"),
        ]),
    ]

def build():
    return build_scale(
        title="中文版知觉压力量表(CPSS-14)",
        description="本问卷帮助了解您近一个月来的压力感受，包括紧张感和对生活的控制感。共14题，大约需要3分钟完成。",
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
