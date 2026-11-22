"""P33: AUDIT - Alcohol Use Disorders Identification Test
(WHO, Babor et al., 2001)
10 items, mixed scoring. Total score 0-40.
Items 1-8: 0-4 frequency scale; Items 9-10: 0/2/4 scale.
Thresholds: 0-7 low risk, 8-15 hazardous, 16-19 harmful, 20-40 possible dependence.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "audit-alcohol"
IMPORT_CODE = "huaxinyun-audit-alcohol"

# Items 1-3: frequency options (0-4)
OPTIONS_Q1_3 = [
    ("从不", 0),
    ("每月一次或更少", 1),
    ("每月2-4次", 2),
    ("每周2-3次", 3),
    ("每周4次或更多", 4),
]

# Items 4-5: frequency of heavy drinking / inability to stop (0-4)
OPTIONS_Q4_5 = [
    ("从不", 0),
    ("每月不到一次", 1),
    ("每月一次", 2),
    ("每周一次", 3),
    ("每天或几乎每天", 4),
]

# Items 6-8: frequency of consequences (0-4)
OPTIONS_Q6_8 = [
    ("从不", 0),
    ("每月不到一次", 1),
    ("每月一次", 2),
    ("每周一次", 3),
    ("每天或几乎每天", 4),
]

# Items 9-10: 3-option scale (0/2/4)
OPTIONS_Q9_10 = [
    ("没有", 0),
    ("有，但不在过去一年内", 2),
    ("有，就在过去一年内", 4),
]

# 10 items with their option sets
QUESTIONS = [
    (1, "您多久喝一次酒？", OPTIONS_Q1_3),
    (2, "在喝酒的一天中，您通常喝多少杯（标准杯）？", OPTIONS_Q1_3),
    (3, "您多久有一次一次喝6杯或更多杯酒的情况？", OPTIONS_Q1_3),
    (4, "在过去一年中，您多久发现自己一旦开始饮酒就无法停止的情况？", OPTIONS_Q4_5),
    (5, "在过去一年中，您多久有一次因为喝酒而耽误了该做的事情？", OPTIONS_Q4_5),
    (6, "在过去一年中，您是否在大量饮酒后第二天早上需要喝一杯酒才能恢复正常？", OPTIONS_Q6_8),
    (7, "在过去一年中，您是否在大量饮酒后产生过内疚或自责的感受？", OPTIONS_Q6_8),
    (8, "在过去一年中，您是否因为喝酒而无法回忆起前一晚发生的事情？", OPTIONS_Q6_8),
    (9, "您或他人是否曾因您的饮酒行为而受伤？", OPTIONS_Q9_10),
    (10, "是否有亲戚、朋友、医生或其他卫生工作者曾对您的饮酒表示过担忧，或建议您减少饮酒？", OPTIONS_Q9_10),
]

def make_questions():
    return [radio_q(order, text, opts) for order, text, opts in QUESTIONS]

def make_dimensions():
    # Single dimension: total score (range 0-40)
    total_formula = q_range(1, 10)

    return [
        dimension("酒精使用风险", "alcohol_risk", 1, total_formula, "", [
            result_rule("hx_wd_y_1 <= 7", "低风险饮酒",
                "您的饮酒模式属于低风险范围，目前未发现酒精相关问题。建议继续保持适度饮酒的习惯，注意饮酒安全。", "none"),
            result_rule("hx_wd_y_1 > 7 && hx_wd_y_1 <= 15", "危险饮酒",
                "您的饮酒模式已经达到危险饮酒的水平，存在发展为酒精相关问题的风险。建议减少饮酒量，注意饮酒频率，必要时可咨询专业人士获取建议。", "low"),
            result_rule("hx_wd_y_1 > 15 && hx_wd_y_1 <= 19", "有害饮酒",
                "您的饮酒模式已经对健康造成有害影响。强烈建议您认真考虑减少饮酒，并寻求专业医疗人员的帮助和支持。", "middle"),
            result_rule("hx_wd_y_1 > 19", "可能酒精依赖",
                "您的得分提示可能存在酒精依赖问题。酒精依赖是一种需要专业治疗的疾病，强烈建议尽快就医或寻求专业的戒酒支持服务。及时的帮助对您的健康和生活质量至关重要。", "high"),
        ]),
    ]

def build():
    return build_scale(
        title="酒精使用障碍筛查量表(AUDIT)",
        description="本问卷由世界卫生组织开发，帮助了解您的饮酒模式和是否存在酒精相关风险。共10题，大约需要3分钟完成。",
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
