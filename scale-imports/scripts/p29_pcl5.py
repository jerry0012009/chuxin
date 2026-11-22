"""P29: PCL-5 - PTSD Checklist for DSM-5
(Weathers et al., 2013)
20 items, 5-point Likert (0-4). Total score 0-80.
4 dimensions: Intrusion (1-5), Avoidance (6-7), Negative Cognition/Mood (8-14), Arousal (15-20).
Thresholds: 0-32 no probable PTSD, 33-37 possible, 38-49 moderate, 50-80 severe.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "pcl5-ptsd"
IMPORT_CODE = "huaxinyun-pcl5-ptsd"

# 5-point Likert options (0-4)
PCL5_OPTIONS = [
    ("完全没有", 0),
    ("有一点", 1),
    ("中度", 2),
    ("相当程度", 3),
    ("极度", 4),
]

# 20 items: (order, Chinese text)
QUESTIONS = [
    (1,  "在过去一个月中，反复发生令人不安的记忆、想法或画面？"),
    (2,  "在过去一个月中，反复发生令人不安的梦境？"),
    (3,  "在过去一个月中，突然感觉或表现得好像创伤事件再次发生（好像您正在重新经历该事件）？"),
    (4,  "在过去一个月中，当某些事物让您想起创伤事件时，感到非常不安？"),
    (5,  "在过去一个月中，当某些事物让您想起创伤事件时，身体出现强烈反应（如心跳加速、呼吸困难、出汗）？"),
    (6,  "在过去一个月中，避免与创伤事件相关的记忆、想法或感受？"),
    (7,  "在过去一个月中，避免与创伤事件相关的人、地方、活动或情境？"),
    (8,  "在过去一个月中，对创伤事件的重要部分记不清楚？"),
    (9,  '在过去一个月中，对自己或他人持有强烈的负面信念（如"我是坏人""没有人可以信任"）？'),
    (10, "在过去一个月中，持续地自责或怪罪他人？"),
    (11, "在过去一个月中，有强烈的负面情绪，如恐惧、愤怒、内疚或羞耻？"),
    (12, "在过去一个月中，对重要活动失去兴趣或不再参与？"),
    (13, "在过去一个月中，感到与他人疏远或脱离？"),
    (14, "在过去一个月中，难以感受到正面情绪（如幸福、满足、爱）？"),
    (15, "在过去一个月中，容易被激怒或突然发怒？"),
    (16, "在过去一个月中，过度冒险或做出伤害自己或他人的行为？"),
    (17, "在过去一个月中，过度警觉或时刻保持警惕？"),
    (18, "在过去一个月中，容易受惊？"),
    (19, "在过去一个月中，难以集中注意力？"),
    (20, "在过去一个月中，难以入睡或保持睡眠？"),
]

def make_questions():
    return [radio_q(order, text, PCL5_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    # Intrusion: items 1-5 (hx_t_1 to hx_t_5)
    intrusion_formula = q_range(1, 5)
    # Avoidance: items 6-7
    avoidance_formula = q_range(6, 7)
    # Negative Cognition/Mood: items 8-14
    neg_cog_formula = q_range(8, 14)
    # Arousal: items 15-20
    arousal_formula = q_range(15, 20)
    # Total
    total_formula = q_range(1, 20)

    return [
        dimension("侵入性症状", "intrusion", 1, intrusion_formula, "", [
            result_rule("hx_wd_y_1 <= 4", "侵入性症状不明显",
                "您近期未表现出明显的侵入性症状（如反复回忆、噩梦等），心理状态较为稳定。", "none"),
            result_rule("hx_wd_y_1 > 4 && hx_wd_y_1 <= 8", "侵入性症状轻微",
                "您偶尔会出现与创伤相关的侵入性体验，但程度较轻。建议关注自身情绪变化，适当进行放松练习。", "low"),
            result_rule("hx_wd_y_1 > 8 && hx_wd_y_1 <= 12", "侵入性症状中等",
                "您存在一定程度的侵入性症状，可能影响日常生活。建议寻求专业心理咨询以获得更好的应对策略。", "middle"),
            result_rule("hx_wd_y_1 > 12", "侵入性症状严重",
                "您的侵入性症状较为严重，强烈建议尽快寻求专业心理评估和治疗。", "high"),
        ]),
        dimension("回避症状", "avoidance", 2, avoidance_formula, "", [
            result_rule("hx_wd_y_2 <= 2", "回避症状不明显",
                "您近期未表现出明显的回避行为，能够正常面对日常生活中的各种情境。", "none"),
            result_rule("hx_wd_y_2 > 2 && hx_wd_y_2 <= 4", "回避症状轻微",
                "您偶尔会回避与创伤相关的事物，但程度较轻。建议逐步尝试面对这些情境。", "low"),
            result_rule("hx_wd_y_2 > 4 && hx_wd_y_2 <= 6", "回避症状中等",
                "您存在一定程度的回避行为，可能限制了您的生活范围。建议在专业指导下逐步进行暴露练习。", "middle"),
            result_rule("hx_wd_y_2 > 6", "回避症状严重",
                "您的回避行为较为严重，强烈建议尽快寻求专业心理评估和治疗。", "high"),
        ]),
        dimension("认知情绪负性改变", "neg_cog_mood", 3, neg_cog_formula, "", [
            result_rule("hx_wd_y_3 <= 7", "认知情绪变化不明显",
                "您的认知和情绪状态较为稳定，未出现明显的负面改变。", "none"),
            result_rule("hx_wd_y_3 > 7 && hx_wd_y_3 <= 14", "认知情绪变化轻微",
                "您在认知和情绪方面出现了一些负面变化，但程度较轻。建议关注自身情绪，适当进行自我调节。", "low"),
            result_rule("hx_wd_y_3 > 14 && hx_wd_y_3 <= 21", "认知情绪变化中等",
                "您在认知和情绪方面存在较明显的负面变化，可能影响日常生活。建议寻求专业心理咨询。", "middle"),
            result_rule("hx_wd_y_3 > 21", "认知情绪变化严重",
                "您的认知和情绪变化较为严重，强烈建议尽快寻求专业心理评估和治疗。", "high"),
        ]),
        dimension("唤醒反应性改变", "arousal", 4, arousal_formula, "", [
            result_rule("hx_wd_y_4 <= 6", "唤醒反应性变化不明显",
                "您的警觉性和反应性处于正常范围，未出现明显的过度唤醒症状。", "none"),
            result_rule("hx_wd_y_4 > 6 && hx_wd_y_4 <= 12", "唤醒反应性变化轻微",
                "您在警觉性和反应性方面出现了一些变化，但程度较轻。建议保持规律作息和适当运动。", "low"),
            result_rule("hx_wd_y_4 > 12 && hx_wd_y_4 <= 18", "唤醒反应性变化中等",
                "您存在一定程度的过度唤醒症状，可能影响睡眠和日常生活。建议寻求专业心理咨询。", "middle"),
            result_rule("hx_wd_y_4 > 18", "唤醒反应性变化严重",
                "您的唤醒反应性变化较为严重，强烈建议尽快寻求专业心理评估和治疗。", "high"),
        ]),
        dimension("PTSD总分", "total", 5, total_formula, "", [
            result_rule("hx_wd_y_5 <= 32", "无明显PTSD症状",
                "您的得分未达到PTSD筛查的临界值，目前未发现明显的创伤后应激障碍症状。建议继续保持健康的心理状态。", "none"),
            result_rule("hx_wd_y_5 > 32 && hx_wd_y_5 <= 37", "可能存在PTSD症状",
                "您的得分接近PTSD筛查的临界值，可能存在一些创伤后应激症状。建议关注自身情绪变化，必要时寻求专业评估。", "low"),
            result_rule("hx_wd_y_5 > 37 && hx_wd_y_5 <= 49", "中度PTSD症状",
                "您的得分表明存在中度水平的PTSD症状，建议尽快寻求专业心理评估和治疗。及时的干预可以有效缓解症状。", "middle"),
            result_rule("hx_wd_y_5 > 49", "重度PTSD症状",
                "您的得分表明存在重度PTSD症状，强烈建议尽快就医或寻求专业心理治疗。重度PTSD症状可能严重影响您的日常生活和社会功能，请不要忽视这些症状。", "high"),
        ]),
    ]

def build():
    return build_scale(
        title="创伤后应激障碍检查表(PCL-5)",
        description="本问卷用于评估创伤后应激障碍(PTSD)症状的严重程度，包括反复回忆、回避、情绪变化等方面。共20题，大约需要5分钟完成。",
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
