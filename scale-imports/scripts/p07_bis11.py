"""P0-7: BIS-11 - Barratt Impulsiveness Scale (Patton, Stanford & Barratt, 1995)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "bis11-impulsiveness"
IMPORT_CODE = "huaxinyun-bis11-impulsiveness"

# 30 items, 4-point scale (1-4)
# Reverse items: 1,7,8,9,10,11,12,14,15,18,24,26,28,29
# Second-order factors:
#   Attention (5,9,11,20,24,26,28) - 7 items
#   Motor (2,3,4,17,19,22,25) - 7 items
#   Nonplanning (1,6,7,8,10,12,13,14,15,16,18,21,23,27,29,30) - 16 items

REVERSE_ITEMS = {1, 7, 8, 9, 10, 11, 12, 14, 15, 18, 24, 26, 28, 29}

QUESTIONS = [
    # Nonplanning (reverse)
    (1,  "我会认真地规划事情。"),
    # Motor
    (2,  "我做事不加思考。"),
    # Motor
    (3,  "我很快就能做出决定。"),
    # Motor
    (4,  "我是个无忧无虑的人。"),
    # Attention
    (5,  "我注意力不集中。"),
    # Nonplanning
    (6,  "我思绪纷乱，难以平静。"),
    # Nonplanning (reverse)
    (7,  "我会提前做好旅行计划。"),
    # Nonplanning (reverse)
    (8,  "我有很强的自我控制能力。"),
    # Attention (reverse)
    (9,  "我能够轻松集中注意力。"),
    # Nonplanning (reverse)
    (10, "我经常定期存钱。"),
    # Attention (reverse)
    (11, "我做事前会反复思考。"),
    # Nonplanning (reverse)
    (12, "我买东西前会三思。"),
    # Nonplanning
    (13, "我做事比较冲动。"),
    # Nonplanning (reverse)
    (14, "我喜欢思考复杂的问题。"),
    # Nonplanning (reverse)
    (15, "我说话前会先思考。"),
    # Nonplanning
    (16, "我花钱没有计划。"),
    # Motor
    (17, "我容易产生冲动行为。"),
    # Nonplanning (reverse)
    (18, "我在做重要决定前会仔细考虑。"),
    # Motor
    (19, "我的注意力容易转移。"),
    # Attention
    (20, "我经常在不适当的时候走神。"),
    # Nonplanning
    (21, "我是个冲动的人。"),
    # Motor
    (22, "我做事情有时不考虑后果。"),
    # Nonplanning
    (23, "我花钱大手大脚。"),
    # Attention (reverse)
    (24, "我做决定时能保持专注。"),
    # Motor
    (25, "我经常在最后一刻改变主意。"),
    # Attention (reverse)
    (26, "我能很好地集中注意力。"),
    # Nonplanning
    (27, "我经常在事后为自己的决定感到后悔。"),
    # Attention (reverse)
    (28, "我能够在较长时间内保持专注。"),
    # Nonplanning (reverse)
    (29, "我善于提前规划。"),
    # Nonplanning
    (30, "我做事经常三分钟热度。"),
]

ATTN_ITEMS = {5, 9, 11, 20, 24, 26, 28}       # 7 items, range 7-28
MOTOR_ITEMS = {2, 3, 4, 17, 19, 22, 25}        # 7 items, range 7-28
NONPLAN_ITEMS = {1, 6, 7, 8, 10, 12, 13, 14, 15, 16, 18, 21, 23, 27, 29, 30}  # 16 items, range 16-64

def make_questions():
    qs = []
    for order, text_zh in QUESTIONS:
        if order in REVERSE_ITEMS:
            opts = [("很少/从不", 4), ("偶尔", 3), ("经常", 2), ("几乎总是/总是", 1)]
        else:
            opts = [("很少/从不", 1), ("偶尔", 2), ("经常", 3), ("几乎总是/总是", 4)]
        qs.append(radio_q(order, text_zh, opts))
    return qs

def items_formula(items):
    return " + ".join(f"hx_t_{i}" for i in sorted(items))

def make_dimensions():
    attn_formula   = items_formula(ATTN_ITEMS)
    motor_formula  = items_formula(MOTOR_ITEMS)
    nonplan_formula = items_formula(NONPLAN_ITEMS)
    total_formula  = q_range(1, 30)

    return [
        # Dimension 1: Attention (7 items, range 7-28)
        dimension("注意力冲动性", "attention", 1, attn_formula, "", [
            result_rule("hx_wd_y_1 <= 11", "注意力冲动性较低",
                "您的注意力控制能力较好，能够保持专注和集中。", "none"),
            result_rule("hx_wd_y_1 > 11 && hx_wd_y_1 <= 17", "注意力冲动性中等",
                "您的注意力冲动性处于正常范围，偶尔会出现注意力分散的情况。", "none"),
            result_rule("hx_wd_y_1 > 17 && hx_wd_y_1 <= 22", "注意力冲动性偏高",
                "您的注意力冲动性偏高，容易出现注意力分散和走神的情况，建议练习专注力训练。", "low"),
            result_rule("hx_wd_y_1 > 22", "注意力冲动性异常偏高",
                "您的注意力冲动性显著偏高，建议寻求专业评估，排除注意缺陷等可能。", "middle"),
        ]),
        # Dimension 2: Motor (7 items, range 7-28)
        dimension("运动冲动性", "motor", 2, motor_formula, "", [
            result_rule("hx_wd_y_2 <= 11", "运动冲动性较低",
                "您的运动冲动性较低，行为控制能力较好，能够三思而后行。", "none"),
            result_rule("hx_wd_y_2 > 11 && hx_wd_y_2 <= 17", "运动冲动性中等",
                "您的运动冲动性处于正常范围，偶尔会表现出冲动行为。", "none"),
            result_rule("hx_wd_y_2 > 17 && hx_wd_y_2 <= 22", "运动冲动性偏高",
                "您的运动冲动性偏高，容易在行动前缺乏充分思考，建议培养自我监控习惯。", "low"),
            result_rule("hx_wd_y_2 > 22", "运动冲动性异常偏高",
                "您的运动冲动性显著偏高，行为冲动性较强，建议寻求专业心理咨询评估。", "middle"),
        ]),
        # Dimension 3: Nonplanning (16 items, range 16-64)
        dimension("非计划冲动性", "nonplanning", 3, nonplan_formula, "", [
            result_rule("hx_wd_y_3 <= 26", "非计划冲动性较低",
                "您的非计划冲动性较低，具有良好的计划能力和自我控制力。", "none"),
            result_rule("hx_wd_y_3 > 26 && hx_wd_y_3 <= 38", "非计划冲动性中等",
                "您的非计划冲动性处于正常范围，在计划和自我控制方面表现一般。", "none"),
            result_rule("hx_wd_y_3 > 38 && hx_wd_y_3 <= 48", "非计划冲动性偏高",
                "您的非计划冲动性偏高，可能在生活规划和自我控制方面存在困难，建议培养计划习惯。", "low"),
            result_rule("hx_wd_y_3 > 48", "非计划冲动性异常偏高",
                "您的非计划冲动性显著偏高，在生活规划和自我控制方面存在明显困难，建议寻求专业指导。", "middle"),
        ]),
        # Total (30 items, range 30-120)
        dimension("冲动性总分", "total_impulsiveness", 4, total_formula, "", [
            result_rule("hx_wd_y_4 <= 52", "冲动性水平较低",
                "您的总体冲动性水平较低，具有良好的自我控制和计划能力。", "none"),
            result_rule("hx_wd_y_4 > 52 && hx_wd_y_4 <= 63", "冲动性水平中等",
                "您的总体冲动性水平处于正常范围，与一般人群常模水平相当（均值约63）。", "none"),
            result_rule("hx_wd_y_4 > 63 && hx_wd_y_4 <= 75", "冲动性水平偏高",
                "您的总体冲动性水平偏高，建议关注自我控制和计划能力的培养。", "low"),
            result_rule("hx_wd_y_4 > 75", "冲动性水平异常偏高",
                "您的总体冲动性水平显著高于常模（均值约63），建议寻求专业心理咨询评估。", "high"),
        ]),
    ]

def build():
    return build_scale(
        title="巴瑞特冲动性量表(BIS-11)",
        description="本问卷帮助了解您在行为决策中的冲动性特点，包括注意力、行动和计划三个方面。共30题，大约需要5分钟完成。",
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
