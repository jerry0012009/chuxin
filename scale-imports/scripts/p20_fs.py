"""P1-20: FS - Flourishing Scale (Diener et al., 2010)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "fs-flourishing"
IMPORT_CODE = "huaxinyun-fs-flourishing"

# FS (Diener): 8 items, 7-point (1=strongly disagree to 7=strongly agree)
# Single dimension. Sum 8-56.

FS_7_OPTIONS = [
    ("非常不同意", 1), ("不同意", 2), ("有些不同意", 3), ("不确定", 4),
    ("有些同意", 5), ("同意", 6), ("非常同意", 7)
]

QUESTIONS = [
    (1, "我的生活有明确的意义和目标。"),
    (2, "我的社交关系能给我支持和鼓励。"),
    (3, "我对日常生活很投入、很积极。"),
    (4, "我积极地为他人的幸福做贡献。"),
    (5, "我有能力胜任生活中的重要事情。"),
    (6, "我是一个好人，过着美好的生活。"),
    (7, "我对未来充满乐观。"),
    (8, "别人尊重我。"),
]

def make_questions():
    return [radio_q(order, text, FS_7_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    sum_formula = " + ".join(f"hx_t_{i}" for i in range(1, 9))

    return [
        dimension("繁荣感总分", "flourishing_total", 1, f"({sum_formula})", "", [
            result_rule("hx_wd_y_1 <= 24", "繁荣感水平较低", "您的繁荣感得分较低，在生活意义感和积极功能方面有提升空间。", "low"),
            result_rule("hx_wd_y_1 > 24 && hx_wd_y_1 <= 36", "繁荣感水平中等", "您的繁荣感处于中等水平，心理社会功能总体尚可。", "none"),
            result_rule("hx_wd_y_1 > 36 && hx_wd_y_1 <= 48", "繁荣感水平较高", "您的繁荣感得分较高，在生活意义、人际关系和自我实现方面表现良好。", "none"),
            result_rule("hx_wd_y_1 > 48", "繁荣感水平很高", "您的繁荣感得分非常高，表明您在各方面都感受到蓬勃发展的状态。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="繁荣感量表(FS)",
        description="本问卷帮助了解您在人际关系、生活目标和自我价值感等方面的心理状态。共8题，大约需要2分钟完成。",
        code=SCALE_CODE,
        questions=make_questions(),
        dimensions=make_dimensions(),
        survey_type="basic",
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
