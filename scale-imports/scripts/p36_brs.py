"""P36: BRS - Brief Resilience Scale (简明韧性量表)
(Smith et al., 2008)
6 items, 5-point scale (1-5). Total score 6-30.
Reverse items: 2, 4, 6 (1-indexed). Single dimension: 心理韧性.
Thresholds: 6-17 低韧性, 18-25 正常, 26-30 高韧性.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "brs-resilience"
IMPORT_CODE = "huaxinyun-brs-resilience"

# Normal options (1-5): higher agreement = more resilient
OPTIONS_NORMAL = [
    ("非常不同意", 1),
    ("不同意", 2),
    ("中立", 3),
    ("同意", 4),
    ("非常同意", 5),
]

# Reverse options (1-5): higher agreement = less resilient (invert values)
OPTIONS_REVERSE = [
    ("非常不同意", 5),
    ("不同意", 4),
    ("中立", 3),
    ("同意", 2),
    ("非常同意", 1),
]

# 6 items: (order, Chinese text, options)
# Items 2, 4, 6 are reverse-scored
QUESTIONS = [
    (1, "我能够从困境中恢复过来。", OPTIONS_NORMAL),
    (2, "我很难度过困难的压力事件。", OPTIONS_REVERSE),      # reverse
    (3, "面对压力事件，我通常能轻松应对。", OPTIONS_NORMAL),
    (4, "当糟糕的事情发生时，我很难从中恢复。", OPTIONS_REVERSE),  # reverse
    (5, "我通常能在困难时期保持积极的态度。", OPTIONS_NORMAL),
    (6, "我往往需要很长时间才能从压力事件中恢复过来。", OPTIONS_REVERSE),  # reverse
]

def make_questions():
    return [radio_q(order, text, opts) for order, text, opts in QUESTIONS]

def make_dimensions():
    total_formula = q_range(1, 6)

    return [
        dimension("心理韧性", "resilience", 1, total_formula, "", [
            result_rule("hx_wd_y_1 <= 17", "低韧性水平",
                "您的心理韧性水平较低，说明您在面对困难和压力时可能较难恢复。建议通过建立社会支持网络、学习压力管理技巧、培养积极的应对方式来提升韧性。", "low"),
            result_rule("hx_wd_y_1 > 17 && hx_wd_y_1 <= 25", "正常韧性水平",
                "您的心理韧性水平处于正常范围，说明您在面对困难时具备一定的恢复能力。建议继续培养积极的心态和有效的应对策略，以进一步增强心理韧性。", "none"),
            result_rule("hx_wd_y_1 > 25 && hx_wd_y_1 <= 30", "高韧性水平",
                "您的心理韧性水平较高，说明您在面对困难和压力时能够较快地恢复，并保持积极的心态。这是心理健康的良好指标，请继续保持。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="简明韧性量表(BRS)",
        description="本问卷帮助了解您面对困难和压力时的恢复能力，即心理韧性水平。共6题，大约需要2分钟完成。",
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
