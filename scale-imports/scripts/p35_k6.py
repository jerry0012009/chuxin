"""P35: K6 - Kessler心理痛苦量表 (Kessler Psychological Distress Scale)
(Kessler et al., 2002)
6 items, 5-point scale (0-4). Total score 0-24.
No reverse items. Single dimension: 心理痛苦.
Thresholds: 0-7 低痛苦, 8-12 中等痛苦, 13-24 严重心理痛苦.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "k6-distress"
IMPORT_CODE = "huaxinyun-k6-distress"

# 5-point scale options (0-4): frequency of distress in past month
K6_OPTIONS = [
    ("没有", 0),
    ("一小部分时间", 1),
    ("一部分时间", 2),
    ("大部分时间", 3),
    ("全部时间", 4),
]

# 6 items: (order, Chinese text)
QUESTIONS = [
    (1, "在过去一个月中，有多少时候您感到紧张？"),
    (2, "在过去一个月中，有多少时候您感到绝望？"),
    (3, "在过去一个月中，有多少时候您感到不安或烦躁？"),
    (4, "在过去一个月中，有多少时候您感到悲伤，以至于没有什么能让您高兴起来？"),
    (5, "在过去一个月中，有多少时候您觉得自己做每件事都很费力？"),
    (6, "在过去一个月中，有多少时候您觉得自己毫无价值？"),
]

def make_questions():
    return [radio_q(order, text, K6_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    total_formula = q_range(1, 6)

    return [
        dimension("心理痛苦", "distress", 1, total_formula, "", [
            result_rule("hx_wd_y_1 <= 7", "低痛苦水平",
                "您的心理痛苦水平较低，说明您近期的心理状态较为健康，没有明显的心理困扰。建议继续保持积极的生活方式和良好的心理调适习惯。", "none"),
            result_rule("hx_wd_y_1 > 7 && hx_wd_y_1 <= 12", "中等痛苦水平",
                "您的心理痛苦水平处于中等范围，说明您近期可能经历了一些心理压力或情绪困扰。建议关注自身的情绪变化，适当采取放松和减压措施，如运动、社交活动或冥想练习。", "low"),
            result_rule("hx_wd_y_1 > 12 && hx_wd_y_1 <= 24", "严重心理痛苦",
                "您的心理痛苦水平较高，表明您近期可能承受了较大的心理压力，出现了较为明显的情绪困扰。建议尽快寻求专业心理咨询或医疗帮助，以便及时获得支持和干预。", "high"),
        ]),
    ]

def build():
    return build_scale(
        title="Kessler心理痛苦量表(K6)",
        description="本问卷用6个简短问题快速了解您近一个月的心理状态，适合大规模心理健康筛查。大约需要1分钟完成。",
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
