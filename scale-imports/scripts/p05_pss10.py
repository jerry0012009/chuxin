"""P0-5: PSS-10 - Perceived Stress Scale (Cohen, Kamarck & Mermelstein, 1983)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "pss10-stress"
IMPORT_CODE = "huaxinyun-pss10-stress"

# 10 items, 5-point scale (0-4)
# Reverse items: 4, 5, 6, 7, 8 (scored 4,3,2,1,0)
REVERSE_ITEMS = {4, 5, 6, 7, 8}

QUESTIONS = [
    (1,  "在过去一个月中，有多少时候您因为发生了意想不到的事情而感到心烦不安？"),
    (2,  "在过去一个月中，有多少时候您感到自己无法控制生活中的重要事情？"),
    (3,  "在过去一个月中，有多少时候您感到紧张和有压力？"),
    (4,  "在过去一个月中，有多少时候您感到自己有信心能够处理好个人问题？"),
    (5,  "在过去一个月中，有多少时候您感到事情正按照您的意愿发展？"),
    (6,  "在过去一个月中，有多少时候您发现自己无法应对所有必须做的事情？"),
    (7,  "在过去一个月中，有多少时候您能够控制生活中令您生气的事情？"),
    (8,  "在过去一个月中，有多少时候您感到自己能够掌控生活中发生的事情？"),
    (9,  "在过去一个月中，有多少时候您因为事情超出您的控制范围而感到生气？"),
    (10, "在过去一个月中，有多少时候您感到困难堆积如山，无法克服？"),
]

def make_questions():
    qs = []
    for order, text_zh in QUESTIONS:
        if order in REVERSE_ITEMS:
            opts = [("从不", 4), ("偶尔", 3), ("有时", 2), ("经常", 1), ("总是", 0)]
        else:
            opts = [("从不", 0), ("偶尔", 1), ("有时", 2), ("经常", 3), ("总是", 4)]
        qs.append(radio_q(order, text_zh, opts))
    return qs

def make_dimensions():
    # Total score: sum of all 10 items (range 0-40)
    total_formula = q_range(1, 10)
    return [
        dimension("知觉压力", "total_stress", 1, total_formula, "", [
            result_rule("hx_wd_y_1 <= 13", "知觉压力水平较低",
                "您的压力感知水平较低，说明您近期感受到的压力较小，心理状态较为轻松。建议继续保持积极的生活方式和压力管理习惯。", "none"),
            result_rule("hx_wd_y_1 > 13 && hx_wd_y_1 <= 26", "知觉压力水平中等",
                "您的压力感知水平处于中等范围，说明您近期感受到一定程度的压力。建议关注自身压力来源，适当采取放松和减压措施，如运动、冥想等。", "none"),
            result_rule("hx_wd_y_1 > 26 && hx_wd_y_1 <= 40", "知觉压力水平较高",
                "您的压力感知水平较高，说明您近期承受了较大的心理压力。建议积极寻求减压方式，必要时可向专业心理咨询师寻求帮助，以避免长期压力对身心健康造成不良影响。", "high"),
        ]),
    ]

def build():
    return build_scale(
        title="知觉压力量表(PSS-10)",
        description="本问卷用于了解您近一个月来的压力感受，帮助评估您当前的压力水平。共10题，大约需要3分钟完成。",
        code=SCALE_CODE,
        questions=make_questions(),
        dimensions=make_dimensions(),
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
