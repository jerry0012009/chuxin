"""P34: DAST-10 - Drug Abuse Screening Test
(Skinner, 1982)
10 items, yes/no format. Total score 0-10.
Yes=1, No=0; EXCEPT item 3 REVERSE (No=1, Yes=0).
Thresholds: 0 no problem, 1-2 low risk, 3-5 moderate, 6-8 severe, 9-10 very severe.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "dast10-drugs"
IMPORT_CODE = "huaxinyun-dast10-drugs"

# Standard options: Yes=1, No=0
OPTIONS_NORMAL = [("是", 1), ("否", 0)]

# Reverse options for item 3: No=1, Yes=0
OPTIONS_REVERSE = [("是", 0), ("否", 1)]

# 10 items: (order, Chinese text, options)
QUESTIONS = [
    (1,  "在过去12个月中，您是否使用过除医生处方之外的药物（毒品）？", OPTIONS_NORMAL),
    (2,  "您是否滥用过一种以上的药物（毒品）？", OPTIONS_NORMAL),
    (3,  "您是否能够只使用医生处方给您的药物？", OPTIONS_REVERSE),  # reverse
    (4,  '您是否曾因为使用药物（毒品）而感到过"兴奋"或"快感"？', OPTIONS_NORMAL),
    (5,  "您是否曾因戒断药物（毒品）而出现身体不适（如出汗、颤抖、恶心等）？", OPTIONS_NORMAL),
    (6,  "您是否曾因使用药物（毒品）而对自己的行为感到过内疚？", OPTIONS_NORMAL),
    (7,  "您的亲友是否曾对您使用药物（毒品）表示过担忧？", OPTIONS_NORMAL),
    (8,  "您是否曾因使用药物（毒品）而忽略了家庭或工作责任？", OPTIONS_NORMAL),
    (9,  "您是否曾因使用药物（毒品）而与家人发生冲突？", OPTIONS_NORMAL),
    (10, "您是否曾因使用药物（毒品）而卷入非法活动（如持有、贩卖毒品等）？", OPTIONS_NORMAL),
]

def make_questions():
    return [radio_q(order, text, opts) for order, text, opts in QUESTIONS]

def make_dimensions():
    # Single dimension: total score (range 0-10)
    total_formula = q_range(1, 10)

    return [
        dimension("药物使用风险", "drug_risk", 1, total_formula, "", [
            result_rule("hx_wd_y_1 == 0", "无药物使用问题",
                "您目前没有药物（毒品）使用方面的问题。请继续保持远离药物的健康生活方式。", "none"),
            result_rule("hx_wd_y_1 > 0 && hx_wd_y_1 <= 2", "低风险",
                "您存在轻微的药物使用风险。建议审视自己的用药习惯，避免使用非处方药物，保持健康的生活方式。", "low"),
            result_rule("hx_wd_y_1 > 2 && hx_wd_y_1 <= 5", "中度风险",
                "您的药物使用存在中度风险，可能已经影响到您的生活。建议认真考虑减少或停止药物使用，并寻求专业医疗人员的帮助。", "middle"),
            result_rule("hx_wd_y_1 > 5 && hx_wd_y_1 <= 8", "重度风险",
                "您的药物使用问题已经比较严重，强烈建议尽快寻求专业的戒毒治疗和支持服务。药物依赖是可以治疗的，及时的专业帮助对您的康复非常重要。", "high"),
            result_rule("hx_wd_y_1 > 8", "极严重风险",
                "您的药物使用问题非常严重，需要紧急的专业干预。请立即寻求戒毒治疗机构或医疗机构的帮助。您的健康和安全是最重要的，请不要犹豫寻求帮助。", "high"),
        ]),
    ]

def build():
    return build_scale(
        title="药物滥用筛查量表(DAST-10)",
        description="本问卷帮助了解您是否存在药物（毒品）使用方面的问题，是药物滥用的快速筛查工具。共10题，大约需要2分钟完成。",
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
