"""P40: C-SSRS - Columbia Suicide Severity Rating Scale Screening Version
(哥伦比亚自杀严重程度评定量表筛查版) (Posner et al., 2011)
6 items, Yes/No format. Clinical screening tool with risk-based scoring.
Items 1-5 assess suicidal ideation (increasing severity), Item 6 assesses behavior.
Uses weighted scoring formula for risk stratification.
answer = "custom" for branching/risk-based scoring.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "cssrs-suicide-risk"
IMPORT_CODE = "huaxinyun-cssrs-suicide-risk"

# Yes/No options (0-1)
YES_NO = [("否", 0), ("是", 1)]

# 6 items: (order, Chinese text)
# Items 1-5: Suicidal ideation (increasing severity)
# Item 6: Suicidal behavior
QUESTIONS = [
    (1, "最近一个月内，您是否希望死去，或者希望自己能以某种方式死去？"),
    (2, "最近一个月内，您是否曾有主动的自杀想法，但没有具体的方法或计划？"),
    (3, "最近一个月内，您是否曾想过自杀的具体方法，但没有打算去实施？"),
    (4, "最近一个月内，您是否曾想过自杀，并且有过一些去实施的打算？"),
    (5, "最近一个月内，您是否曾想过自杀，并且有具体的计划和明确的意图去实施？"),
    (6, "最近一个月内，您是否曾经实际尝试过自杀，或做出过自杀的准备行为（如收集药片、写遗书、选择地点等）？"),
]

def make_questions():
    return [radio_q(order, text, YES_NO) for order, text in QUESTIONS]

def make_dimensions():
    # Weighted scoring formula for risk stratification
    # Item 6 (behavior) × 100, Item 5 (plan+intent) × 20, Item 4 (some intent) × 15,
    # Item 3 (method, no intent) × 10, Item 2 (active thoughts) × 5, Item 1 (wish dead) × 1
    # Score ranges:
    #   0 = no risk
    #   1-4 = low risk (mild ideation)
    #   5-9 = moderate risk (active ideation)
    #   10-19 = high risk (method or intent)
    #   20-99 = critical risk (plan + intent)
    #   100+ = critical risk (behavior present)
    weighted_formula = "hx_t_6 * 100 + hx_t_5 * 20 + hx_t_4 * 15 + hx_t_3 * 10 + hx_t_2 * 5 + hx_t_1 * 1"

    return [
        dimension("自杀风险等级", "suicide_risk", 1, weighted_formula, "", [
            result_rule("hx_wd_y_1 == 0", "无自杀风险",
                "筛查结果未发现自杀意念或自杀行为。目前来看您没有自杀方面的风险。如果您今后出现相关想法，请及时寻求帮助。", "none"),
            result_rule("hx_wd_y_1 > 0 && hx_wd_y_1 < 5", "低风险",
                "筛查发现您存在轻度的自杀意念（如希望死去的想法）。虽然目前风险较低，但请关注自身的情绪变化。建议与信任的人分享您的感受，必要时寻求心理咨询支持。", "low"),
            result_rule("hx_wd_y_1 >= 5 && hx_wd_y_1 < 10", "中等风险",
                "筛查发现您存在主动的自杀想法。建议您尽快联系专业的心理健康服务机构或拨打心理援助热线（如24小时热线：400-161-9995），与专业人员进行深入评估和沟通。", "middle"),
            result_rule("hx_wd_y_1 >= 10 && hx_wd_y_1 < 20", "较高风险",
                "筛查发现您存在有一定意图或方法的自杀想法，风险较高。强烈建议您立即联系专业的心理危机干预机构或前往医院精神科/心理科就诊。请记住，您并不孤单，专业的帮助可以有效缓解您的痛苦。", "high"),
            result_rule("hx_wd_y_1 >= 20 && hx_wd_y_1 < 100", "高风险",
                "筛查发现您存在有具体计划和实施意图的自杀想法，风险很高。请立即联系心理危机干预热线（24小时：400-161-9995）或前往最近的医院急诊科。请确保身边有人陪伴，远离可能用于自我伤害的物品。", "high"),
            result_rule("hx_wd_y_1 >= 100", "极高风险",
                "筛查发现您近期有自杀行为或准备行为，风险极高。请立即拨打急救电话（120）或前往最近的医院急诊科。如果您目前处于危险中，请立即联系家人、朋友或拨打心理危机热线（24小时：400-161-9995）。您的生命非常重要，请让专业人员帮助您。", "high"),
        ]),
    ]

def build():
    scale = build_scale(
        title="哥伦比亚自杀严重程度评定量表筛查版(C-SSRS)",
        description="本问卷是国际通用的自杀风险筛查工具，帮助专业人员快速评估自杀风险等级。共6题，大约需要2分钟完成。",
        code=SCALE_CODE,
        questions=make_questions(),
        dimensions=make_dimensions(),
    )
    # Mark as custom scoring (clinical screening tool, not standard self-report)
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
