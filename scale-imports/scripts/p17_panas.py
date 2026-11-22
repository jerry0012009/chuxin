"""P1-17: PANAS - Positive and Negative Affect Schedule (Watson, Clark & Tellegen, 1988)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "panas-affect"
IMPORT_CODE = "huaxinyun-panas-affect"

# PANAS: 20 items, 5-point (1=very slightly to 5=extremely)
# PA items: 1,3,5,9,10,12,14,16,17,19
# NA items: 2,4,6,7,8,11,13,15,18,20

PANAS_5_OPTIONS = [
    ("非常轻微", 1), ("比较轻微", 2), ("中等程度", 3), ("比较强烈", 4), ("极其强烈", 5)
]

QUESTIONS = [
    (1, "感兴趣的"),
    (2, "心烦的"),
    (3, "兴奋的"),
    (4, "害怕的"),
    (5, "受到鼓舞的"),
    (6, "有敌意的"),
    (7, "热情的"),
    (8, "易怒的"),
    (9, "警觉的"),
    (10, "羞愧的"),
    (11, "受鼓舞的"),
    (12, "紧张的"),
    (13, "意志坚定的"),
    (14, "专注的"),
    (15, "坐立不安的"),
    (16, "有活力的"),
    (17, "恐惧的"),
    (18, "骄傲的"),
    (19, "警惕的"),
    (20, "神经质的"),
]

PA_ITEMS = [1, 3, 5, 9, 11, 13, 14, 16, 18, 19]
NA_ITEMS = [2, 4, 6, 7, 8, 10, 12, 15, 17, 20]

def make_questions():
    return [radio_q(order, text, PANAS_5_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    pa_formula = " + ".join(f"hx_t_{i}" for i in PA_ITEMS)
    na_formula = " + ".join(f"hx_t_{i}" for i in NA_ITEMS)

    return [
        dimension("正性情绪", "positive_affect", 1, f"({pa_formula})", "", [
            result_rule("hx_wd_y_1 <= 20", "正性情绪水平较低", "您的正性情绪得分较低，可能处于情绪低落状态，建议关注自身情绪健康。", "low"),
            result_rule("hx_wd_y_1 > 20 && hx_wd_y_1 <= 30", "正性情绪水平中等", "您的正性情绪处于中等水平，总体情绪状态尚可。", "none"),
            result_rule("hx_wd_y_1 > 30 && hx_wd_y_1 <= 40", "正性情绪水平较高", "您的正性情绪得分较高，情绪状态积极良好。", "none"),
            result_rule("hx_wd_y_1 > 40", "正性情绪水平很高", "您的正性情绪得分非常高，情绪状态非常积极。", "none"),
        ]),
        dimension("负性情绪", "negative_affect", 2, f"({na_formula})", "", [
            result_rule("hx_wd_y_2 <= 15", "负性情绪水平较低", "您的负性情绪得分很低，情绪状态良好。", "none"),
            result_rule("hx_wd_y_2 > 15 && hx_wd_y_2 <= 25", "负性情绪水平中等", "您的负性情绪处于中等水平，属于正常范围。", "none"),
            result_rule("hx_wd_y_2 > 25 && hx_wd_y_2 <= 35", "负性情绪水平偏高", "您的负性情绪得分偏高，建议关注压力管理和情绪调节。", "low"),
            result_rule("hx_wd_y_2 > 35", "负性情绪水平很高", "您的负性情绪得分很高，建议寻求专业心理支持。", "middle"),
        ]),
    ]

def build():
    return build_scale(
        title="正负性情绪量表(PANAS)",
        description="本问卷帮助了解您近期的情绪状态，包括积极情绪和消极情绪两个方面。共20题，大约需要3分钟完成。",
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
