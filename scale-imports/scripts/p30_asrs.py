"""P30: ASRS-v1.1 - Adult ADHD Self-Report Scale
(Kessler et al., 2005)
18 items, 5-point scale (0-4). Total score 0-72.
Part A (screening, items 1-6), Part B (supplemental, items 7-18).
Dimensions: Inattention (1-9), Hyperactivity-Impulsivity (10-18).
Thresholds: 0-16 unlikely ADHD, 17-23 likely, >=24 highly likely.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "asrs-adhd"
IMPORT_CODE = "huaxinyun-asrs-adhd"

# 5-point frequency scale (0-4)
ASRS_OPTIONS = [
    ("从不", 0),
    ("很少", 1),
    ("有时", 2),
    ("经常", 3),
    ("非常频繁", 4),
]

# 18 items: (order, Chinese text)
# Part A (items 1-6): screening items
# Part B (items 7-18): supplemental items
QUESTIONS = [
    # Part A - Screening
    (1,  "在完成有困难的项目或任务的最后阶段时，您在注意细节方面有多大困难？"),
    (2,  "在需要有条理地完成任务或活动时，您有多大困难？"),
    (3,  "在需要记住约会或约定时，您有多大困难？"),
    (4,  "在需要处理一项复杂、需要提前规划的任务时，您有多大困难？"),
    (5,  "在需要处理长篇报告或需要填写的表格时，您有多大困难？"),
    (6,  "在需要把东西放错地方或找不到东西的频率是多少？"),
    # Part B - Supplemental
    (7,  "在需要集中注意力时，您有多大困难保持专注（如阅读、听课）？"),
    (8,  "在需要安静地坐着时（如开会、看电影），您的坐立不安程度如何？"),
    (9,  "在需要安静地独自完成某项任务时，您有多大困难让自己安静下来？"),
    (10, "在社交场合中（如聚会），您在别人还没说完话时就插嘴的频率是多少？"),
    (11, "在排队或轮流等待时，您的不耐烦程度如何？"),
    (12, "在感到不安时，您大声说话或打断他人的频率是多少？"),
    (13, "在别人要求您坐着不动时，您扭动或坐立不安的程度如何？"),
    (14, "在需要做自己不太感兴趣的事情时，您集中注意力的困难程度如何？"),
    (15, "当有事情吸引您注意力时，您从正在进行的工作中分心的频率是多少？"),
    (16, "在需要安静地坐着时，您感到内心不安的程度如何？"),
    (17, "在需要等待的场合中，您坐立不安的程度如何？"),
    (18, "在一天结束时，您感到精力充沛的程度如何？"),
]

def make_questions():
    return [radio_q(order, text, ASRS_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    # Inattention: items 1-9
    inattention_formula = q_range(1, 9)
    # Hyperactivity-Impulsivity: items 10-18
    hyper_formula = q_range(10, 18)
    # Total
    total_formula = q_range(1, 18)

    return [
        dimension("注意缺陷", "inattention", 1, inattention_formula, "", [
            result_rule("hx_wd_y_1 <= 9", "注意缺陷症状不明显",
                "您在注意力集中方面表现正常，未发现明显的注意缺陷症状。", "none"),
            result_rule("hx_wd_y_1 > 9 && hx_wd_y_1 <= 15", "注意缺陷症状轻微",
                "您在注意力方面存在一些困难，但程度较轻。建议通过制定计划、减少干扰等方式来提高注意力。", "low"),
            result_rule("hx_wd_y_1 > 15 && hx_wd_y_1 <= 22", "注意缺陷症状中等",
                "您在注意力方面存在较明显的困难，可能影响学习和工作效率。建议寻求专业评估和指导。", "middle"),
            result_rule("hx_wd_y_1 > 22", "注意缺陷症状严重",
                "您的注意缺陷症状较为严重，强烈建议尽快寻求专业心理评估。ADHD是可以有效治疗的，专业的帮助可以显著改善您的生活质量。", "high"),
        ]),
        dimension("多动冲动", "hyperactivity", 2, hyper_formula, "", [
            result_rule("hx_wd_y_2 <= 9", "多动冲动症状不明显",
                "您在行为控制方面表现正常，未发现明显的多动或冲动症状。", "none"),
            result_rule("hx_wd_y_2 > 9 && hx_wd_y_2 <= 15", "多动冲动症状轻微",
                "您偶尔会有多动或冲动的表现，但程度较轻。建议练习深呼吸和暂停思考等自我调节技巧。", "low"),
            result_rule("hx_wd_y_2 > 15 && hx_wd_y_2 <= 22", "多动冲动症状中等",
                "您存在较明显的多动或冲动症状，可能影响人际关系和日常活动。建议寻求专业评估和指导。", "middle"),
            result_rule("hx_wd_y_2 > 22", "多动冲动症状严重",
                "您的多动冲动症状较为严重，强烈建议尽快寻求专业心理评估。专业的行为管理和药物治疗可以有效帮助您。", "high"),
        ]),
        dimension("ADHD总分", "total", 3, total_formula, "", [
            result_rule("hx_wd_y_3 <= 16", "不太可能有ADHD",
                "您的得分较低，不太可能患有注意力缺陷多动障碍（ADHD）。如果您仍然感到困扰，建议关注日常习惯和压力管理。", "none"),
            result_rule("hx_wd_y_3 > 16 && hx_wd_y_3 <= 23", "可能有ADHD",
                "您的得分表明您可能有ADHD的特征。建议进行专业的心理评估，以确定是否需要进一步的支持和干预。", "low"),
            result_rule("hx_wd_y_3 > 23", "非常可能有ADHD",
                "您的得分较高，强烈建议尽快寻求专业心理评估。ADHD是一种可以有效管理的神经发育障碍，早期识别和干预对改善生活质量非常重要。", "high"),
        ]),
    ]

def build():
    return build_scale(
        title="成人ADHD自评量表(ASRS-v1.1)",
        description="本问卷帮助了解您是否存在注意力不集中、多动或冲动等方面的困难，是成人ADHD的筛查工具。共18题，大约需要5分钟完成。",
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
