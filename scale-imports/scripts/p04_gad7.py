"""P0-4: GAD-7 - Generalized Anxiety Disorder 7-item Scale
(Spitzer, Kroenke, Williams & Lowe, 2006)
7 items, 4-point Likert (0-3). Total score 0-21.
Thresholds: 0-4 minimal, 5-9 mild, 10-14 moderate, 15-21 severe.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "gad7-anxiety"
IMPORT_CODE = "huaxinyun-gad7-anxiety"

# GAD-7 items: (order, Chinese text)
ITEMS = [
    (1, "感到紧张、焦虑或急切"),
    (2, "不能够停止或控制担忧"),
    (3, "对各种各样的事情担忧过多"),
    (4, "很难放松下来"),
    (5, "由于不安而无法静坐"),
    (6, "变得容易烦恼或急躁"),
    (7, "感到似乎将有可怕的事情发生"),
]

# 4-point scale options
GAD7_OPTIONS = [
    ("完全不会", 0),
    ("好几天", 1),
    ("一半以上的天数", 2),
    ("几乎每天", 3),
]

def make_questions():
    prompt = "在过去两周里，有多少时候您受到以下问题所困扰？"
    qs = []
    for order, text_zh in ITEMS:
        full_text = f"{prompt}\n{text_zh}"
        qs.append(radio_q(order, full_text, GAD7_OPTIONS))
    return qs

def make_dimensions():
    total_formula = q_range(1, 7)
    return [
        dimension("广泛性焦虑", "gad_total", 1, total_formula, "", [
            result_rule("hx_wd_y_1 <= 4", "无或极轻微焦虑",
                "您的焦虑症状处于正常范围，说明您的心理状态良好。建议继续保持健康的生活方式和积极的心态。",
                "none"),
            result_rule("hx_wd_y_1 > 4 && hx_wd_y_1 <= 9", "轻度焦虑",
                "您存在轻度焦虑症状。建议关注自己的情绪变化，尝试通过运动、冥想、规律作息等方式缓解压力。如症状持续或加重，建议寻求专业心理咨询。",
                "low"),
            result_rule("hx_wd_y_1 > 9 && hx_wd_y_1 <= 14", "中度焦虑",
                "您存在中度焦虑症状，建议尽快寻求专业心理咨询或就医评估。中度焦虑可能影响您的日常生活、工作效率和人际关系。专业的心理干预（如认知行为疗法）能有效帮助缓解症状。",
                "middle"),
            result_rule("hx_wd_y_1 > 14 && hx_wd_y_1 <= 21", "重度焦虑",
                "您的焦虑症状已达到重度水平，强烈建议尽快就医或寻求专业心理治疗。重度焦虑可能严重影响您的日常生活和社会功能。请不要忽视这些症状，及时的专业帮助对您的康复非常重要。",
                "high"),
        ]),
    ]

def build():
    return build_scale(
        title="广泛性焦虑量表(GAD-7)",
        description="本问卷用于评估您近期的焦虑状况，帮助了解您在日常生活中的情绪状态。共7题，大约需要2分钟完成。",
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
