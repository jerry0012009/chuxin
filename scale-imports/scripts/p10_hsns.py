"""P1-10: HSNS - Hypersensitive Narcissism Scale (Hendin & Cheek, 1997)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "hsns-narcissism"
IMPORT_CODE = "huaxinyun-hsns-narcissism"

# HSNS: 10 items, 5-point scale (1=very uncharacteristic to 5=very characteristic)
# All items scored directly. Sum 10-50. Mean in US college=29.4

QUESTIONS = [
    (1, "我很容易对他人感到失望，因为别人总是达不到我的标准。"),
    (2, "我常常觉得自己在与他人比较时更有能力。"),
    (3, "当别人没有给予我应有的重视时，我会感到非常不满。"),
    (4, "我觉得自己应该得到特殊的待遇。"),
    (5, "我发现自己很难接受他人的批评。"),
    (6, "我经常感到自己比周围的人更优秀。"),
    (7, "当我走进一个房间时，我感觉自己应该成为关注的焦点。"),
    (8, "我有时会幻想自己拥有巨大的成就、影响力或权力。"),
    (9, "我觉得自己有很多未被赏识的才能。"),
    (10, "我对他人的需求和感受不太关心。"),
]

LIKERT5_OPTIONS = [
    ("非常不符合", 1), ("不太符合", 2), ("不确定", 3), ("比较符合", 4), ("非常符合", 5)
]

def make_questions():
    return [radio_q(order, text, LIKERT5_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    # Sum of all 10 items (range 10-50)
    total = " + ".join(f"hx_t_{i}" for i in range(1, 11))

    return [
        dimension("高敏感性自恋", "hsns", 1, total, "", [
            result_rule("hx_wd_y_1 <= 20", "高敏感性自恋水平较低", "您的自恋特质较低，自我认知较为务实和平衡。", "none"),
            result_rule("hx_wd_y_1 > 20 && hx_wd_y_1 <= 29", "高敏感性自恋水平中等", "您的自恋特质处于正常范围（常模均值29.4）。", "none"),
            result_rule("hx_wd_y_1 > 29 && hx_wd_y_1 <= 38", "高敏感性自恋水平偏高", "您在自我重要性和对他人的敏感方面得分偏高，建议关注共情能力和自我觉察。", "low"),
            result_rule("hx_wd_y_1 > 38", "高敏感性自恋水平异常偏高", "您的得分显著高于常模均值（29.4），建议进行专业心理评估。", "middle"),
        ]),
    ]

def build():
    return build_scale(
        title="高敏感性自恋量表(HSNS)",
        description="本问卷帮助了解您在人际交往中是否存在过度敏感或自我中心的倾向。共10题，大约需要3分钟完成。",
        code=SCALE_CODE,
        questions=make_questions(),
        dimensions=make_dimensions(),
        survey_type="basic",
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
