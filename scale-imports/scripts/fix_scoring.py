"""
Fix three scales with scoring errors identified in audit:
1. PSS-10: Q6 incorrectly reverse-scored (should be forward)
2. BIS-11: Subscale allocation wrong (7+7+16 vs standard 8+11+11) + 6 extra reverse items
3. LOT-R: Q1 (optimism) excluded, Q8 (non-standard) included
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

# ─── Fix 1: PSS-10 ─────────────────────────────────────────────────
# Standard PSS-10 (Cohen et al., 1983): reverse items = {4, 5, 7, 8}
# Our error: included Q6 in reverse set
# Q6 "发现自己无法应对所有必须做的事情" = stress indicator, should be FORWARD

def fix_pss10():
    print("=" * 60)
    print("Fix 1: PSS-10 — Q6 reverse → forward")
    print("=" * 60)
    
    scale = {
        "id": "pss10-stress",
        "title": "知觉压力量表(PSS-10)",
        "description": "Perceived Stress Scale (PSS-10)，Cohen, Kamarck & Mermelstein (1983) 编制，测量个体在最近一个月中感知到的压力水平。共10题，5点计分（0=从不 到 4=总是），其中有4道反向计分题(Q4,Q5,Q7,Q8)。总分范围0-40，分数越高表示感知到的压力越大。常模参考：中国成人均值约19.0(SD≈7.1)，0-13为低压力，14-26为中等压力，27-40为高压力。",
        "type": "basic",
        "questions": [],
        "dimensions": []
    }
    
    # Standard reverse items: 4, 5, 7, 8 (NOT 6!)
    REVERSE = {4, 5, 7, 8}
    QUESTIONS = [
        (1,  "在过去一个月中，有多少时候您因为发生了意想不到的事情而感到心烦不安？"),
        (2,  "在过去一个月中，有多少时候您感到自己无法控制生活中的重要事情？"),
        (3,  "在过去一个月中，有多少时候您感到紧张和有压力？"),
        (4,  "在过去一个月中，有多少时候您感到自己有信心能够处理好个人问题？"),
        (5,  "在过去一个月中，有多少时候您感到事情正按照您的意愿发展？"),
        (6,  "在过去一个月中，有多少时候您发现自己无法应对所有必须做的事情？"),
        (7,  "在过去一个月中，有多少时候您能够控制生活中令您生气的事情？"),
        (8,  "在过去一个月中，有多少时候您感到自己能够掌控生活中发生的事情？"),
        (9,  "在过去一个月中，有多少时候您因为事情超出您的控制范围而感到生气？"),
        (10, "在过去一个月中，有多少时候您感到困难堆积如山，无法克服？"),
    ]
    
    for order, text in QUESTIONS:
        if order in REVERSE:
            opts = [("从不", 4), ("偶尔", 3), ("有时", 2), ("经常", 1), ("总是", 0)]
        else:
            opts = [("从不", 0), ("偶尔", 1), ("有时", 2), ("经常", 3), ("总是", 4)]
        scale["questions"].append(radio_q(order, text, opts))
    
    total_formula = q_range(1, 10)
    scale["dimensions"] = [
        dimension("知觉压力", "total_stress", 1, total_formula, "", [
            result_rule("hx_wd_y_1 <= 13", "知觉压力水平较低",
                "您的压力感知水平较低，说明您近期感受到的压力较小，心理状态较为轻松。建议继续保持积极的生活方式和压力管理习惯。", "none"),
            result_rule("hx_wd_y_1 > 13 && hx_wd_y_1 <= 26", "知觉压力水平中等",
                "您的压力感知水平处于中等范围，说明您近期感受到一定程度的压力。建议关注自身压力来源，适当采取放松和减压措施，如运动、冥想等。", "none"),
            result_rule("hx_wd_y_1 > 26 && hx_wd_y_1 <= 40", "知觉压力水平较高",
                "您的压力感知水平较高，说明您近期承受了较大的心理压力。建议积极寻求减压方式，必要时可向专业心理咨询师寻求帮助，以避免长期压力对身心健康造成不良影响。", "high"),
        ]),
    ]
    
    result = import_scale(scale, dry_run=False, publish=True, overwrite=True)
    print(f"   Imported: {result.get('imported', 0)}, Updated: {result.get('updated', 0)}")
    for item in result.get("items", []):
        print(f"   {item.get('title')}: {item.get('action')}")
    return True


# ─── Fix 2: BIS-11 ─────────────────────────────────────────────────
# Standard BIS-11 (Patton et al., 1995; Stanford et al., 2009):
#   Attention (8): {1, 2, 3, 4, 5, 6, 11, 28}
#   Motor (11):    {7, 8, 9, 10, 16, 17, 19, 21, 22, 25, 26}
#   Nonplanning (11): {12, 13, 14, 15, 18, 20, 23, 24, 27, 29, 30}
#   Reverse items: {1, 7, 8, 9, 10, 12, 13, 15, 20, 29, 30}
# Our errors:
#   - Subscales: 7+7+16 instead of 8+11+11
#   - Reverse: added {11,14,18,24,26,28}, missing {13,15,20,30}

def fix_bis11():
    print("=" * 60)
    print("Fix 2: BIS-11 — subscales + reverse items")
    print("=" * 60)
    
    # Standard definitions
    ATTN_ITEMS = {1, 2, 3, 4, 5, 6, 11, 28}          # 8 items
    MOTOR_ITEMS = {7, 8, 9, 10, 16, 17, 19, 21, 22, 25, 26}  # 11 items
    NONPLAN_ITEMS = {12, 13, 14, 15, 18, 20, 23, 24, 27, 29, 30}  # 11 items
    REVERSE_ITEMS = {1, 7, 8, 9, 10, 12, 13, 15, 20, 29, 30}  # 11 items
    
    # Verify
    assert len(ATTN_ITEMS) == 8
    assert len(MOTOR_ITEMS) == 11
    assert len(NONPLAN_ITEMS) == 11
    assert ATTN_ITEMS | MOTOR_ITEMS | NONPLAN_ITEMS == set(range(1, 31))
    assert len(ATTN_ITEMS & MOTOR_ITEMS & NONPLAN_ITEMS) == 0  # no overlap
    assert len(REVERSE_ITEMS) == 11
    
    QUESTIONS = [
        (1,  "我会认真地规划事情。"),              # Attention (R)
        (2,  "我做事不加思考。"),                  # Attention
        (3,  "我很快就能做出决定。"),              # Attention (R)  
        (4,  "我是个无忧无虑的人。"),              # Attention (R)
        (5,  "我注意力不集中。"),                  # Attention
        (6,  "我思绪纷乱，难以平静。"),            # Attention
        (7,  "我会提前做好旅行计划。"),            # Motor (R)
        (8,  "我有很强的自我控制能力。"),          # Motor (R)
        (9,  "我能够轻松集中注意力。"),            # Motor (R)
        (10, "我经常定期存钱。"),                  # Motor (R)
        (11, "我做事前会反复思考。"),              # Attention
        (12, "我买东西前会三思。"),                # Nonplanning (R)
        (13, "我做事比较冲动。"),                  # Nonplanning (R)
        (14, "我喜欢思考复杂的问题。"),            # Nonplanning
        (15, "我说话前会先思考。"),                # Nonplanning (R)
        (16, "我花钱没有计划。"),                  # Motor
        (17, "我容易产生冲动行为。"),              # Motor
        (18, "我在做重要决定前会仔细考虑。"),      # Nonplanning
        (19, "我的注意力容易转移。"),              # Motor
        (20, "我经常在不适当的时候走神。"),        # Nonplanning (R)
        (21, "我是个冲动的人。"),                  # Motor
        (22, "我做事情有时不考虑后果。"),          # Motor
        (23, "我花钱大手大脚。"),                  # Nonplanning
        (24, "我做决定时能保持专注。"),            # Nonplanning
        (25, "我经常在最后一刻改变主意。"),        # Motor
        (26, "我能很好地集中注意力。"),            # Motor
        (27, "我经常在事后为自己的决定感到后悔。"), # Nonplanning
        (28, "我能够在较长时间内保持专注。"),      # Attention
        (29, "我善于提前规划。"),                  # Nonplanning (R)
        (30, "我做事经常三分钟热度。"),            # Nonplanning (R)
    ]
    
    scale = {
        "id": "bis11-impulsiveness",
        "title": "巴瑞特冲动性量表(BIS-11)",
        "description": "Barratt Impulsiveness Scale (BIS-11)，Patton, Stanford & Barratt (1995) 编制，测量冲动性的三个维度：注意力冲动性(8题)、运动冲动性(11题)和非计划冲动性(11题)。共30题，4点计分（1=很少/从不 到 4=几乎总是/总是），其中11道反向计分题。总分范围30-120，分数越高表示冲动性越强。常模参考：一般人群均值约63(SD≈10)。",
        "type": "basic",
        "questions": [],
        "dimensions": []
    }
    
    for order, text in QUESTIONS:
        if order in REVERSE_ITEMS:
            opts = [("很少/从不", 4), ("偶尔", 3), ("经常", 2), ("几乎总是/总是", 1)]
        else:
            opts = [("很少/从不", 1), ("偶尔", 2), ("经常", 3), ("几乎总是/总是", 4)]
        scale["questions"].append(radio_q(order, text, opts))
    
    def items_formula(items):
        return " + ".join(f"hx_t_{i}" for i in sorted(items))
    
    total_formula = q_range(1, 30)
    
    scale["dimensions"] = [
        # Attention (8 items, range 8-32)
        dimension("注意力冲动性", "attention", 1, items_formula(ATTN_ITEMS), "", [
            result_rule("hx_wd_y_1 <= 12", "注意力冲动性较低",
                "您的注意力控制能力较好，能够保持专注和集中。", "none"),
            result_rule("hx_wd_y_1 > 12 && hx_wd_y_1 <= 18", "注意力冲动性中等",
                "您的注意力冲动性处于正常范围，偶尔会出现注意力分散的情况。", "none"),
            result_rule("hx_wd_y_1 > 18 && hx_wd_y_1 <= 24", "注意力冲动性偏高",
                "您的注意力冲动性偏高，容易出现注意力分散和走神的情况，建议练习专注力训练。", "low"),
            result_rule("hx_wd_y_1 > 24", "注意力冲动性异常偏高",
                "您的注意力冲动性显著偏高，建议寻求专业评估，排除注意缺陷等可能。", "middle"),
        ]),
        # Motor (11 items, range 11-44)
        dimension("运动冲动性", "motor", 2, items_formula(MOTOR_ITEMS), "", [
            result_rule("hx_wd_y_2 <= 17", "运动冲动性较低",
                "您的运动冲动性较低，行为控制能力较好，能够三思而后行。", "none"),
            result_rule("hx_wd_y_2 > 17 && hx_wd_y_2 <= 25", "运动冲动性中等",
                "您的运动冲动性处于正常范围，偶尔会表现出冲动行为。", "none"),
            result_rule("hx_wd_y_2 > 25 && hx_wd_y_2 <= 33", "运动冲动性偏高",
                "您的运动冲动性偏高，容易在行动前缺乏充分思考，建议培养自我监控习惯。", "low"),
            result_rule("hx_wd_y_2 > 33", "运动冲动性异常偏高",
                "您的运动冲动性显著偏高，行为冲动性较强，建议寻求专业心理咨询评估。", "middle"),
        ]),
        # Nonplanning (11 items, range 11-44)
        dimension("非计划冲动性", "nonplanning", 3, items_formula(NONPLAN_ITEMS), "", [
            result_rule("hx_wd_y_3 <= 17", "非计划冲动性较低",
                "您的非计划冲动性较低，具有良好的计划能力和自我控制力。", "none"),
            result_rule("hx_wd_y_3 > 17 && hx_wd_y_3 <= 25", "非计划冲动性中等",
                "您的非计划冲动性处于正常范围，在计划和自我控制方面表现一般。", "none"),
            result_rule("hx_wd_y_3 > 25 && hx_wd_y_3 <= 33", "非计划冲动性偏高",
                "您的非计划冲动性偏高，可能在生活规划和自我控制方面存在困难，建议培养计划习惯。", "low"),
            result_rule("hx_wd_y_3 > 33", "非计划冲动性异常偏高",
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
    
    result = import_scale(scale, dry_run=False, publish=True, overwrite=True)
    print(f"   Imported: {result.get('imported', 0)}, Updated: {result.get('updated', 0)}")
    for item in result.get("items", []):
        print(f"   {item.get('title')}: {item.get('action')}")
    return True


# ─── Fix 3: LOT-R ──────────────────────────────────────────────────
# Standard LOT-R (Scheier, Carver & Bridges, 1994) — from Carver's official website:
#   Optimism (direct): items 1, 4, 10
#   Pessimism (reverse): items 3, 7, 9
#   Fillers (not scored): items 2, 5, 6, 8
#   Total scored items: 6, range 0-24
#
# Chinese version item mapping (by content):
#   CN Q1  → LOT-R #1  "expect the best" → Optimism
#   CN Q2  → LOT-R #6  "keep busy" → Filler
#   CN Q3  → LOT-R #4  "always optimistic" → Optimism
#   CN Q4  → LOT-R #3  "go wrong" → Pessimism (reverse)
#   CN Q5  → LOT-R #9  "rarely count on good" → Pessimism (reverse)
#   CN Q6  → LOT-R #7  "hardly ever expect" → Pessimism (reverse)
#   CN Q7  → LOT-R #10 "expect more good" → Optimism
#   CN Q8  → "事情很少按照意愿发展" → NOT standard LOT-R, exclude as filler
#   CN Q9  → "结果比预期好" → NOT standard LOT-R, exclude as filler
#   CN Q10 → LOT-R #2  "easy to relax" → Filler
#
# Fixes needed:
#   Q1: was filler → now optimism (direct)
#   Q8: was pessimism → now excluded (filler)
#   Q9: was optimism → now excluded (filler)

def fix_lotr():
    print("=" * 60)
    print("Fix 3: LOT-R — item mapping correction")
    print("=" * 60)
    
    # Pessimism items that need reverse coding
    P_REVERSE = {4, 5, 6}  # CN Q4, Q5, Q6 = LOT-R #3, #9, #7
    
    QUESTIONS = [
        # Optimism (direct): Q1, Q3, Q7
        (1, "在不确定的时候，我通常会期望最好的结果。"),
        # Filler: Q2
        (2, "对我来说，保持忙碌是很重要的。"),
        # Optimism (direct): Q3
        (3, "我总是对自己的未来持乐观态度。"),
        # Pessimism (reverse): Q4
        (4, "如果我认为某件事情会出错，那它通常确实会出错。"),
        # Pessimism (reverse): Q5
        (5, "我很少指望好事会发生在我身上。"),
        # Pessimism (reverse): Q6
        (6, "我总是预期最坏的结果。"),
        # Optimism (direct): Q7
        (7, "总的来说，我期望更多好事而不是坏事发生在我身上。"),
        # Filler (non-standard, excluded): Q8
        (8, "事情很少按照我的意愿发展。"),
        # Filler (non-standard, excluded): Q9
        (9, "在大多数情况下，事情的结果都比我预期的好。"),
        # Filler: Q10
        (10, "我很容易放松。"),
    ]
    
    scale = {
        "id": "lotr-optimism",
        "title": "生活取向测验修订版(LOT-R)",
        "description": "Life Orientation Test-Revised (LOT-R)，Scheier, Carver & Bridges (1994)编制，测量乐观与悲观倾向。10题，其中4题为填充题不计分(Q2,Q8,Q9,Q10)，5点计分（0=非常不同意到4=非常同意）。乐观维度(Q1,Q3,Q7)直接计分，悲观维度(Q4,Q5,Q6)反向计分。有效计分范围0-24，分数越高越乐观。参考来源：Carver CS, University of Miami官网。",
        "type": "basic",
        "questions": [],
        "dimensions": []
    }
    
    for order, text in QUESTIONS:
        if order in P_REVERSE:
            opts = [("非常不同意", 4), ("不同意", 3), ("不确定", 2), ("同意", 1), ("非常同意", 0)]
        else:
            opts = [("非常不同意", 0), ("不同意", 1), ("不确定", 2), ("同意", 3), ("非常同意", 4)]
        scale["questions"].append(radio_q(order, text, opts))
    
    # Scored items: Q1, Q3, Q4, Q5, Q6, Q7 (range 0-24)
    scored_formula = "hx_t_1 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7"
    optimism_formula = "hx_t_1 + hx_t_3 + hx_t_7"   # 3 items, range 0-12
    pessimism_formula = "hx_t_4 + hx_t_5 + hx_t_6"  # 3 items, range 0-12
    
    scale["dimensions"] = [
        dimension("乐观", "optimism", 1, optimism_formula, "", [
            result_rule("hx_wd_y_1 <= 4", "乐观倾向较低",
                "您的乐观得分较低，对未来积极事件的期望偏低。建议关注积极心态的培养。", "none"),
            result_rule("hx_wd_y_1 > 4 && hx_wd_y_1 <= 8", "乐观倾向中等",
                "您的乐观得分处于中等水平。", "none"),
            result_rule("hx_wd_y_1 > 8", "乐观倾向较高",
                "您的乐观得分较高，对未来抱有积极期望。", "none"),
        ]),
        dimension("悲观", "pessimism", 2, pessimism_formula, "", [
            result_rule("hx_wd_y_2 <= 4", "悲观倾向较低",
                "您的悲观得分较低，较少预期消极结果。", "none"),
            result_rule("hx_wd_y_2 > 4 && hx_wd_y_2 <= 8", "悲观倾向中等",
                "您的悲观得分处于中等水平。", "none"),
            result_rule("hx_wd_y_2 > 8", "悲观倾向较高",
                "您的悲观得分较高，倾向于预期消极结果，建议关注心理健康。", "low"),
        ]),
        dimension("总分", "total", 3, scored_formula, "", [
            result_rule("hx_wd_y_3 <= 8", "悲观倾向",
                "您的LOT-R总分较低（0-8），整体倾向于悲观。建议关注自身心态，培养积极的思维方式。", "low"),
            result_rule("hx_wd_y_3 > 8 && hx_wd_y_3 <= 16", "中等水平",
                "您的LOT-R总分处于中等范围（9-16），乐观与悲观倾向较为平衡。", "none"),
            result_rule("hx_wd_y_3 > 16", "乐观倾向",
                "您的LOT-R总分较高（17-24），整体倾向于乐观，对未来持积极态度。", "none"),
        ]),
    ]
    
    result = import_scale(scale, dry_run=False, publish=True, overwrite=True)
    print(f"   Imported: {result.get('imported', 0)}, Updated: {result.get('updated', 0)}")
    for item in result.get("items", []):
        print(f"   {item.get('title')}: {item.get('action')}")
    return True


# ─── Main ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"{'='*60}")
    print(f"  Scale Scoring Fixes — 3 scales")
    print(f"{'='*60}\n")
    
    results = []
    
    try:
        fix_pss10()
        results.append(("PSS-10", "✅"))
    except Exception as e:
        results.append(("PSS-10", f"❌ {e}"))
    
    try:
        fix_bis11()
        results.append(("BIS-11", "✅"))
    except Exception as e:
        results.append(("BIS-11", f"❌ {e}"))
    
    try:
        fix_lotr()
        results.append(("LOT-R", "✅"))
    except Exception as e:
        results.append(("LOT-R", f"❌ {e}"))
    
    print(f"\n{'='*60}")
    print(f"  Results")
    print(f"{'='*60}")
    for name, status in results:
        print(f"  {status} {name}")
    
    # Verify in DB
    print(f"\n{'='*60}")
    print(f"  DB Verification")
    print(f"{'='*60}")
    import subprocess
    for code in ["pss10-stress", "bis11-impulsiveness", "lotr-optimism"]:
        full_code = f"huaxinyun-{code}"
        r = subprocess.run(
            ["mysql", "-u", "root", "-p123456", "chuxin", "-e",
             f"SELECT code, status, self_test_enabled FROM scale_surveys WHERE code='{full_code}';"],
            capture_output=True, text=True
        )
        print(f"  {r.stdout.strip()}")
