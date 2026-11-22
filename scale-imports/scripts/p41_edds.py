"""P41: EDDS - Eating Disorder Diagnostic Scale (饮食障碍诊断量表)
(Stice, Telch, & Rizvi, 2000)
22 items, mixed response types (7-point scales, yes/no, frequency counts).
Custom scoring for DSM-5 diagnostic categories.
answer = "custom" for diagnostic algorithm.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "edds-eating-disorder"
IMPORT_CODE = "huaxinyun-edds-eating-disorder"

# 7-point dissatisfaction scale (0-6)
OPT_DISSATISFACTION = [
    ("非常满意", 0),
    ("比较满意", 1),
    ("有点满意", 2),
    ("无所谓", 3),
    ("有点不满意", 4),
    ("比较不满意", 5),
    ("非常不满意", 6),
]

# 6-point fear/concern scale (0-5)
OPT_FEAR = [
    ("完全不害怕", 0),
    ("稍微有些害怕", 1),
    ("有点害怕", 2),
    ("比较害怕", 3),
    ("很害怕", 4),
    ("极度害怕", 5),
]

# 6-point frequency scale (0-5) for subjective experience
OPT_FREQUENCY_6 = [
    ("从不", 0),
    ("很少", 1),
    ("偶尔", 2),
    ("有时", 3),
    ("经常", 4),
    ("总是", 5),
]

# 6-point behavior frequency (past 28 days) for compensatory behaviors
OPT_BEHAV_FREQ = [
    ("0次", 0),
    ("1-3次", 1),
    ("4-7次", 2),
    ("8-11次", 3),
    ("12-15次", 4),
    ("16次或更多", 5),
]

# Binge eating frequency (past 28 days)
OPT_BINGE_FREQ = [
    ("0次", 0),
    ("1-3次", 1),
    ("4-7次", 2),
    ("8-11次", 3),
    ("12-15次", 4),
    ("16次或更多", 5),
]

# Yes/No
OPT_YESNO = [("否", 0), ("是", 1)]

# Severity scale (0-6)
OPT_SEVERITY = [
    ("没有", 0),
    ("很轻微", 1),
    ("轻微", 2),
    ("中等", 3),
    ("偏重", 4),
    ("严重", 5),
    ("非常严重", 6),
]

# 22 items
QUESTIONS = [
    (1,  "在过去28天内，您对自己体重的不满意程度如何？", OPT_DISSATISFACTION),
    (2,  "在过去28天内，您对自己体型的不满意程度如何？", OPT_DISSATISFACTION),
    (3,  "在过去28天内，您对自己腹部（肚子）的不满意程度如何？", OPT_DISSATISFACTION),
    (4,  "在过去28天内，您害怕体重增加5斤（约2.5公斤）的程度如何？", OPT_FEAR),
    (5,  "在过去28天内，您感到自己很胖的频率如何？", OPT_FREQUENCY_6),
    (6,  "在过去28天内，您感到进食失控的频率如何？", OPT_SEVERITY),
    (7,  "在过去28天内，您有多少次吃了别人认为异常大量的食物？", OPT_BINGE_FREQ),
    (8,  "在上述暴食发作时，您感到无法停止进食或无法控制吃了多少的频率如何？", OPT_SEVERITY),
    (9,  "在过去28天内，您是否曾通过催吐（自行呕吐）来防止体重增加或促进体重减轻？", OPT_BEHAV_FREQ),
    (10, "在过去28天内，您是否曾使用泻药来防止体重增加或促进体重减轻？", OPT_BEHAV_FREQ),
    (11, "在过去28天内，您是否曾使用利尿剂（排水药）来防止体重增加或促进体重减轻？", OPT_BEHAV_FREQ),
    (12, "在过去28天内，您是否曾通过严格节食或禁食来防止体重增加或促进体重减轻？", OPT_BEHAV_FREQ),
    (13, "在过去28天内，您是否曾通过剧烈运动来防止体重增加或促进体重减轻？", OPT_BEHAV_FREQ),
    (14, "您是否曾经在事后感到严重的内疚或自我厌恶，因为您觉得自己吃了太多？", OPT_YESNO),
    (15, "在过去的3-6个月中，您是否因为暴食和/或清除行为（呕吐、使用泻药等）而导致体重减轻超过4.5公斤？", OPT_YESNO),
    (16, "在过去的3-6个月中，其他人是否注意到您存在进食异常的问题？", OPT_YESNO),
    (17, "在过去28天内，您每天是否感到强烈的进食欲望且难以抗拒？", OPT_FREQUENCY_6),
    (18, "在过去28天内，您是否在独处时进食？", OPT_FREQUENCY_6),
    (19, "在过去28天内，您在进食后是否感到非常饱胀或不舒服？", OPT_FREQUENCY_6),
    (20, "您对自己当前体重和身高的感知准确吗？（如果刻意低报体重选\"否\"）", OPT_YESNO),
    (21, "在过去一年中，您的月经周期是否曾经连续3个月或更长时间不规律或停止？", OPT_YESNO),
    (22, "在过去28天内，您是否觉得自己需要接受专业帮助来解决进食问题？", OPT_YESNO),
]

def make_questions():
    return [radio_q(order, text, opts) for order, text, opts in QUESTIONS]

def make_dimensions():
    # Custom scoring: the import system will use answer="custom" and evaluate
    # diagnostic criteria server-side. We define dimensions for sub-scores.
    #
    # Diagnostic scoring algorithm (EDDS):
    # Body dissatisfaction: items 1-3 (range 0-18)
    # Fear of weight gain: item 4 (range 0-5)
    # Feeling fat: item 5 (range 0-5)
    # Binge eating: items 6-8
    # Compensatory behaviors: items 9-13
    # Associated features: items 14-22

    body_dissat = "hx_t_1 + hx_t_2 + hx_t_3"
    binge_score = "hx_t_6 + hx_t_7 + hx_t_8"
    compensatory = "hx_t_9 + hx_t_10 + hx_t_11 + hx_t_12 + hx_t_13"
    total_score = q_range(1, 22)

    return [
        # Subscore 1: Body dissatisfaction (items 1-3, range 0-18)
        dimension("体型不满", "body_dissatisfaction", 1, body_dissat, "", [
            result_rule("hx_wd_y_1 <= 3", "体型满意度较高",
                "您对自身体型的满意度较高，对身体形象有积极的认知。", "none"),
            result_rule("hx_wd_y_1 > 3 && hx_wd_y_1 <= 9", "体型不满程度中等",
                "您对体型存在一定程度的不满意，这在普通人群中较为常见。建议关注自我接纳和健康的身体形象。", "none"),
            result_rule("hx_wd_y_1 > 9 && hx_wd_y_1 <= 14", "体型不满程度较高",
                "您对体型存在较明显的不满，可能影响到日常生活和情绪。建议关注健康的自我形象，必要时可寻求心理咨询。", "low"),
            result_rule("hx_wd_y_1 > 14", "体型不满程度严重",
                "您对体型存在严重的不满，这可能与饮食障碍风险相关。建议尽快寻求专业的心理健康评估。", "middle"),
        ]),
        # Subscore 2: Binge/loss of control (items 6-8, range 0-17)
        dimension("暴食与失控感", "binge_eating", 2, binge_score, "", [
            result_rule("hx_wd_y_2 == 0", "无暴食症状",
                "在过去28天内未发现暴食或进食失控的情况。", "none"),
            result_rule("hx_wd_y_2 > 0 && hx_wd_y_2 <= 5", "暴食症状轻微",
                "偶尔出现进食失控的情况，建议关注自己的进食模式，注意规律饮食。", "none"),
            result_rule("hx_wd_y_2 > 5 && hx_wd_y_2 <= 11", "暴食症状中等",
                "存在一定程度的暴食和失控感，建议评估自己的进食行为，必要时寻求专业帮助。", "low"),
            result_rule("hx_wd_y_2 > 11", "暴食症状严重",
                "存在频繁的暴食和强烈失控感，可能与暴食障碍或神经性贪食症相关。强烈建议寻求专业的饮食障碍评估和治疗。", "middle"),
        ]),
        # Subscore 3: Compensatory behaviors (items 9-13, range 0-25)
        dimension("代偿行为", "compensatory", 3, compensatory, "", [
            result_rule("hx_wd_y_3 == 0", "无代偿行为",
                "在过去28天内未发现清除或代偿行为。", "none"),
            result_rule("hx_wd_y_3 > 0 && hx_wd_y_3 <= 5", "代偿行为轻微",
                "偶尔出现代偿行为（如催吐、使用泻药、过度运动等），请关注这些行为是否在增加。", "low"),
            result_rule("hx_wd_y_3 > 5 && hx_wd_y_3 <= 15", "代偿行为中等",
                "存在较频繁的代偿行为，这是饮食障碍的重要风险因素。建议尽快寻求专业评估和支持。", "middle"),
            result_rule("hx_wd_y_3 > 15", "代偿行为严重",
                "存在非常频繁的代偿行为，可能对身体造成严重伤害。请立即寻求专业的饮食障碍治疗服务。", "high"),
        ]),
        # Total severity score (items 1-22, range 0-93)
        dimension("饮食障碍总体严重程度", "total_severity", 4, total_score, "", [
            result_rule("hx_wd_y_4 <= 15", "饮食障碍风险低",
                "您的总体评分较低，未发现明显的饮食障碍症状。如果您有任何关于饮食或体重的困扰，建议保持健康的生活方式。", "none"),
            result_rule("hx_wd_y_4 > 15 && hx_wd_y_4 <= 35", "饮食障碍风险中等",
                "您的评分提示存在一定的饮食相关困扰。建议关注自己的进食模式和对体型的态度，如有加重趋势请及时寻求帮助。", "low"),
            result_rule("hx_wd_y_4 > 35 && hx_wd_y_4 <= 55", "饮食障碍风险较高",
                "您的评分提示可能存在饮食障碍的风险因素，包括体型不满、暴食或代偿行为。建议尽快寻求心理健康专业人员的评估。", "middle"),
            result_rule("hx_wd_y_4 > 55", "饮食障碍风险高",
                "您的评分提示存在严重的饮食障碍症状。饮食障碍是可以治疗的疾病，强烈建议尽快到专业的饮食障碍治疗机构或精神科就诊。", "high"),
        ]),
    ]

def build():
    scale = build_scale(
        title="饮食障碍诊断量表(EDDS)",
        description="本问卷帮助了解您近期的进食行为和体型关注程度，用于饮食障碍的初步筛查。共22题，大约需要5分钟完成。",
        code=SCALE_CODE,
        questions=make_questions(),
        dimensions=make_dimensions(),
    )
    # Mark as custom scoring (complex diagnostic algorithm)
    scale["answer"] = "custom"
    return scale

if __name__ == "__main__":
    scale = build()
    json_path = os.path.join(os.path.dirname(__file__), "..", "json", f"{SCALE_CODE}.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(scale, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON saved: {json_path}")
    print(f"   Questions: {len(scale['questions'])}")
    print(f"   Dimensions: {len(scale['dimensions'])}")
    print(f"   Custom scoring: {scale.get('answer', 'N/A')}")

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
