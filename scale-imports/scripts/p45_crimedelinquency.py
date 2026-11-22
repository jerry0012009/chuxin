"""P45: Crime & Delinquency Scale (犯罪与违法行为量表)
48 items, frequency input (填写数字: 0=去年没有做过).
answer = "custom" for frequency-based scoring.
Multiple dimensions: 暴力犯罪, 财产犯罪, 药物相关, 性犯罪, 其他违法行为.
No fixed clinical cutoffs — prevalence-based scoring.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "crime-delinquency"
IMPORT_CODE = "huaxinyun-crime-delinquency"

# Frequency options: 0=never in past year, up to many times
# Using numeric frequency ranges for practical input
OPT_FREQUENCY = [
    ("0次（没有做过）", 0),
    ("1次", 1),
    ("2-3次", 2),
    ("4-5次", 3),
    ("6次或更多", 4),
]

# 48 items across 5 dimensions
# 暴力犯罪 (Violent Crime): items 1-12
# 财产犯罪 (Property Crime): items 13-22
# 药物相关 (Drug-related): items 23-32
# 性犯罪 (Sex Crime): items 33-38
# 其他违法行为 (Other Delinquency): items 39-48

QUESTIONS = [
    # === 暴力犯罪 (Violent Crime) ===
    (1,  "在过去一年中，您动手打过别人（包括扇耳光、推搡等）。", OPT_FREQUENCY),
    (2,  "在过去一年中，您参与过群体斗殴。", OPT_FREQUENCY),
    (3,  "在过去一年中，您威胁过要伤害他人。", OPT_FREQUENCY),
    (4,  "在过去一年中，您使用武器（如刀具、棍棒等）威胁过他人。", OPT_FREQUENCY),
    (5,  "在过去一年中，您故意损坏过他人的财物以发泄愤怒。", OPT_FREQUENCY),
    (6,  "在过去一年中，您对家人或亲密伴侣动过手。", OPT_FREQUENCY),
    (7,  "在过去一年中，您欺凌或恐吓过他人（包括网络欺凌）。", OPT_FREQUENCY),
    (8,  "在过去一年中，您故意伤害过动物。", OPT_FREQUENCY),
    (9,  "在过去一年中，您在愤怒中扔过东西或砸过物品。", OPT_FREQUENCY),
    (10, "在过去一年中，您因打架导致他人受伤。", OPT_FREQUENCY),
    (11, "在过去一年中，您胁迫他人做他们不愿意做的事情。", OPT_FREQUENCY),
    (12, "在过去一年中，您参与过任何形式的人身攻击或伤人行为。", OPT_FREQUENCY),

    # === 财产犯罪 (Property Crime) ===
    (13, "在过去一年中，您从商店偷过东西（入店行窃）。", OPT_FREQUENCY),
    (14, "在过去一年中，您偷过他人的钱包、手机或其他个人物品。", OPT_FREQUENCY),
    (15, "在过去一年中，您未经允许进入过他人的建筑或车辆。", OPT_FREQUENCY),
    (16, "在过去一年中，您偷过自行车、摩托车或汽车。", OPT_FREQUENCY),
    (17, "在过去一年中，您伪造过文件或签名。", OPT_FREQUENCY),
    (18, "在过去一年中，您在网上实施过诈骗或欺诈行为。", OPT_FREQUENCY),
    (19, "在过去一年中，您故意损坏过公共设施或他人财物。", OPT_FREQUENCY),
    (20, "在过去一年中，您使用过他人的信用卡或银行卡信息进行消费。", OPT_FREQUENCY),
    (21, "在过去一年中，您参与过抢劫或抢夺行为。", OPT_FREQUENCY),
    (22, "在过去一年中，您通过纵火来损坏财物。", OPT_FREQUENCY),

    # === 药物相关 (Drug-related) ===
    (23, "在过去一年中，您使用过非法药物（如大麻、摇头丸、冰毒等）。", OPT_FREQUENCY),
    (24, "在过去一年中，您出售或分发过非法药物。", OPT_FREQUENCY),
    (25, "在过去一年中，您持有过非法药物。", OPT_FREQUENCY),
    (26, "在过去一年中，您在醉酒或药物影响下驾驶过车辆。", OPT_FREQUENCY),
    (27, "在过去一年中，您使用过他人的处方药物。", OPT_FREQUENCY),
    (28, "在过去一年中，您参与过非法药物的运输。", OPT_FREQUENCY),
    (29, "在过去一年中，您为了获得药物而做过违法的事情。", OPT_FREQUENCY),
    (30, "在过去一年中，您尝试过制造或合成非法药物。", OPT_FREQUENCY),
    (31, "在过去一年中，您提供过场所供他人使用非法药物。", OPT_FREQUENCY),
    (32, "在过去一年中，您在公共场所醉酒闹事。", OPT_FREQUENCY),

    # === 性犯罪 (Sex Crime) ===
    (33, "在过去一年中，您对他人实施过性骚扰（包括言语和肢体）。", OPT_FREQUENCY),
    (34, "在过去一年中，您在对方不同意的情况下触摸过他人的身体。", OPT_FREQUENCY),
    (35, "在过去一年中，您传播过他人的私密照片或视频。", OPT_FREQUENCY),
    (36, "在过去一年中，您观看或传播过非法的色情内容。", OPT_FREQUENCY),
    (37, "在过去一年中，您暴露过自己的身体以引起他人不适。", OPT_FREQUENCY),
    (38, "在过去一年中，您在网上对他人进行过性方面的骚扰或跟踪。", OPT_FREQUENCY),

    # === 其他违法行为 (Other Delinquency) ===
    (39, "在过去一年中，您逃过票（如公交、地铁、火车等）。", OPT_FREQUENCY),
    (40, "在过去一年中，您使用过假证件（如假身份证、假学生证等）。", OPT_FREQUENCY),
    (41, "在过去一年中，您在考试中作弊。", OPT_FREQUENCY),
    (42, "在过去一年中，您故意散布过谣言或诽谤他人。", OPT_FREQUENCY),
    (43, "在过去一年中，您参与过赌博活动。", OPT_FREQUENCY),
    (44, "在过去一年中，您向执法人员提供过虚假信息。", OPT_FREQUENCY),
    (45, "在过去一年中，您在没有许可的情况下参加过非法集会。", OPT_FREQUENCY),
    (46, "在过去一年中，您违反过交通法规（如闯红灯、酒驾等）。", OPT_FREQUENCY),
    (47, "在过去一年中，您非法下载或复制过受版权保护的软件或内容。", OPT_FREQUENCY),
    (48, "在过去一年中，您参与过任何其他形式的违法活动。", OPT_FREQUENCY),
]

# Dimension assignments (1-indexed)
VIOLENT_CRIME = list(range(1, 13))      # items 1-12
PROPERTY_CRIME = list(range(13, 23))    # items 13-22
DRUG_RELATED = list(range(23, 33))      # items 23-32
SEX_CRIME = list(range(33, 39))         # items 33-38
OTHER_DELINQUENCY = list(range(39, 49)) # items 39-48

def make_questions():
    return [radio_q(order, text, opts) for order, text, opts in QUESTIONS]

def _sum_formula(items):
    return " + ".join(f"hx_t_{i}" for i in items)

def make_dimensions():
    violent_formula = _sum_formula(VIOLENT_CRIME)
    property_formula = _sum_formula(PROPERTY_CRIME)
    drug_formula = _sum_formula(DRUG_RELATED)
    sex_formula = _sum_formula(SEX_CRIME)
    other_formula = _sum_formula(OTHER_DELINQUENCY)
    total_formula = q_range(1, 48)

    return [
        # 暴力犯罪 (12 items, range 0-48)
        dimension("暴力犯罪", "violent_crime", 1, violent_formula, "", [
            result_rule("hx_wd_y_1 == 0", "无暴力行为",
                "在过去一年中未报告任何暴力行为。目前来看您在暴力犯罪方面没有风险。", "none"),
            result_rule("hx_wd_y_1 > 0 && hx_wd_y_1 <= 6", "暴力行为轻微",
                "在过去一年中存在少量的暴力行为（如推搡、争吵中的肢体冲突等）。建议学习愤怒管理和冲突解决技巧。", "low"),
            result_rule("hx_wd_y_1 > 6 && hx_wd_y_1 <= 18", "暴力行为中等",
                "在过去一年中存在较频繁的暴力行为，这可能对他人造成伤害并带来法律风险。强烈建议寻求专业的愤怒管理和情绪调节帮助。", "middle"),
            result_rule("hx_wd_y_1 > 18", "暴力行为严重",
                "在过去一年中存在非常频繁的暴力行为，已经构成严重的社会风险。请立即寻求专业的行为干预和心理评估服务。", "high"),
        ]),
        # 财产犯罪 (10 items, range 0-40)
        dimension("财产犯罪", "property_crime", 2, property_formula, "", [
            result_rule("hx_wd_y_2 == 0", "无财产犯罪行为",
                "在过去一年中未报告任何财产犯罪行为。", "none"),
            result_rule("hx_wd_y_2 > 0 && hx_wd_y_2 <= 5", "财产犯罪行为轻微",
                "在过去一年中存在少量的财产相关违法行为。请认识到这些行为的法律风险，建议停止此类行为。", "low"),
            result_rule("hx_wd_y_2 > 5 && hx_wd_y_2 <= 15", "财产犯罪行为中等",
                "在过去一年中存在较频繁的财产犯罪行为。这些行为具有法律风险，建议寻求帮助以改变行为模式。", "middle"),
            result_rule("hx_wd_y_2 > 15", "财产犯罪行为严重",
                "在过去一年中存在非常频繁的财产犯罪行为。强烈建议立即停止违法行为并寻求专业帮助。", "high"),
        ]),
        # 药物相关 (10 items, range 0-40)
        dimension("药物相关", "drug_related", 3, drug_formula, "", [
            result_rule("hx_wd_y_3 == 0", "无药物相关行为",
                "在过去一年中未报告任何药物相关的违法行为。", "none"),
            result_rule("hx_wd_y_3 > 0 && hx_wd_y_3 <= 5", "药物相关行为轻微",
                "在过去一年中存在少量的药物使用或相关行为。建议了解药物滥用的健康和法律风险，必要时寻求戒断支持。", "low"),
            result_rule("hx_wd_y_3 > 5 && hx_wd_y_3 <= 15", "药物相关行为中等",
                "在过去一年中存在较频繁的药物使用或相关违法行为。药物滥用可能严重影响健康和社会功能，建议尽快寻求专业的药物依赖治疗。", "middle"),
            result_rule("hx_wd_y_3 > 15", "药物相关行为严重",
                "在过去一年中存在非常频繁的药物使用和相关违法行为。请立即寻求专业的药物依赖治疗和行为干预服务。", "high"),
        ]),
        # 性犯罪 (6 items, range 0-24)
        dimension("性犯罪", "sex_crime", 4, sex_formula, "", [
            result_rule("hx_wd_y_4 == 0", "无性犯罪行为",
                "在过去一年中未报告任何性方面的违法行为。", "none"),
            result_rule("hx_wd_y_4 > 0 && hx_wd_y_4 <= 3", "性犯罪行为轻微",
                "在过去一年中存在少量的性骚扰或不当行为。请认识到此类行为对他人造成的伤害和法律后果，建议立即停止并反思。", "low"),
            result_rule("hx_wd_y_4 > 3 && hx_wd_y_4 <= 10", "性犯罪行为中等",
                "在过去一年中存在较频繁的性相关违法行为。这些行为对受害者造成严重伤害，强烈建议寻求专业的行为评估和干预。", "middle"),
            result_rule("hx_wd_y_4 > 10", "性犯罪行为严重",
                "在过去一年中存在非常频繁的性犯罪行为。这是非常严重的问题，请立即寻求专业的行为治疗和法律咨询。", "high"),
        ]),
        # 其他违法行为 (10 items, range 0-40)
        dimension("其他违法行为", "other_delinquency", 5, other_formula, "", [
            result_rule("hx_wd_y_5 == 0", "无其他违法行为",
                "在过去一年中未报告其他类型的违法行为。", "none"),
            result_rule("hx_wd_y_5 > 0 && hx_wd_y_5 <= 5", "其他违法行为轻微",
                "在过去一年中存在少量的轻微违法行为。建议增强法律意识，避免这些行为升级。", "low"),
            result_rule("hx_wd_y_5 > 5 && hx_wd_y_5 <= 15", "其他违法行为中等",
                "在过去一年中存在较频繁的违法行为。建议反思这些行为的根源，必要时寻求专业帮助来改善行为模式。", "middle"),
            result_rule("hx_wd_y_5 > 15", "其他违法行为严重",
                "在过去一年中存在非常频繁的违法行为。建议认真审视自己的行为，并寻求专业的评估和干预。", "high"),
        ]),
        # 总分 (48 items, range 0-192)
        dimension("违法行为总分", "total_crime", 6, total_formula, "", [
            result_rule("hx_wd_y_6 == 0", "无违法行为",
                "在过去一年中未报告任何违法行为。您遵守法律法规，行为表现良好。", "none"),
            result_rule("hx_wd_y_6 > 0 && hx_wd_y_6 <= 12", "违法行为轻微",
                "在过去一年中存在少量的违法行为。建议增强法律意识，认识到违法行为的后果，并积极改正。", "low"),
            result_rule("hx_wd_y_6 > 12 && hx_wd_y_6 <= 48", "违法行为中等",
                "在过去一年中存在较频繁的违法行为，涵盖多个领域。建议认真反思并寻求专业帮助来改善行为模式，避免进一步的法律风险。", "middle"),
            result_rule("hx_wd_y_6 > 48", "违法行为严重",
                "在过去一年中存在非常频繁的违法行为。您的行为模式已经构成严重的法律和社会风险。强烈建议尽快寻求专业的行为评估、心理干预和法律咨询。", "high"),
        ]),
    ]

def build():
    scale = build_scale(
        title="犯罪与违法行为量表",
        description="本问卷了解您在过去一年中的各种行为发生频率，帮助评估行为风险。共48题，大约需要10分钟完成。",
        code=SCALE_CODE,
        questions=make_questions(),
        dimensions=make_dimensions(),
    )
    # Mark as custom scoring (frequency-based, prevalence model)
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
