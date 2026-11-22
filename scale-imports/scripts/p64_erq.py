"""P64: ERQ 情绪调节问卷 (Emotion Regulation Questionnaire)
Gross & John (2003), 中文版
10 items, 7-point scale. 2 dimensions: 认知重评/表达抑制.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "erq"
IMPORT_CODE = "huaxinyun-erq"

OPT7 = [
    ("非常不同意", 1), ("比较不同意", 2), ("有点不同意", 3),
    ("不确定", 4), ("有点同意", 5), ("比较同意", 6), ("非常同意", 7)
]

# 10 items: all forward scored
# Reappraisal: 1,3,5,7,8,10 | Suppression: 2,4,6,9
QUESTIONS_RAW = [
    (1,  "当我想感受一些积极的情绪（如快乐或高兴）时，我会改变自己思考问题的角度。", False),
    (2,  "我不会表露自己的情绪。", False),
    (3,  "当我想少感受一些消极的情绪（如悲伤或愤怒）时，我会改变自己思考问题的角度。", False),
    (4,  "当感受到积极情绪时，我会很小心地不让它们表露出来。", False),
    (5,  "在面对压力情境时，我会使自己以一种有助于保持平静的方式来考虑它。", False),
    (6,  "我控制自己情绪的方式是不表达它们。", False),
    (7,  "当我想多感受一些积极的情绪时，我会改变自己对情境的考虑方式。", False),
    (8,  "我会通过改变对情境的考虑方式来控制自己的情绪。", False),
    (9,  "当感受到消极的情绪时，我确定不会表露它们。", False),
    (10, "当我想少感受一些消极的情绪时，我会改变自己对情境的考虑方式。", False),
]

def make_questions():
    qs = []
    for order, text, is_rev in QUESTIONS_RAW:
        qs.append(radio_q(order, text, OPT7))
    return qs

def make_dimensions():
    # Reappraisal: items 1,3,5,7,8,10
    rp_formula = "(hx_t_1 + hx_t_3 + hx_t_5 + hx_t_7 + hx_t_8 + hx_t_10) / 6"
    # Suppression: items 2,4,6,9
    sp_formula = "(hx_t_2 + hx_t_4 + hx_t_6 + hx_t_9) / 4"

    return [
        dimension("认知重评", "reappraisal", 1, rp_formula, "", [
            result_rule("hx_wd_y_1 <= 3.0", "认知重评使用较少",
                "您较少使用改变思维方式来调节情绪，可能更多依赖其他情绪调节策略。", "none"),
            result_rule("hx_wd_y_1 > 3.0 && hx_wd_y_1 <= 5.0", "认知重评使用中等",
                "您有时会通过改变对情境的看法来调节情绪，这是一种较为适应性的情绪调节方式。", "none"),
            result_rule("hx_wd_y_1 > 5.0", "认知重评使用较多",
                "您善于通过改变对情境的看法来调节情绪，这是一种适应性的情绪调节策略，有助于维护心理健康。", "none"),
        ]),
        dimension("表达抑制", "suppression", 2, sp_formula, "", [
            result_rule("hx_wd_y_2 <= 3.0", "表达抑制使用较少",
                "您倾向于自然地表达自己的情绪，不太压抑情感的外在表达。", "none"),
            result_rule("hx_wd_y_2 > 3.0 && hx_wd_y_2 <= 5.0", "表达抑制使用中等",
                "您在某些情况下会抑制情绪的表达，但不会过度压抑。", "none"),
            result_rule("hx_wd_y_2 > 5.0", "表达抑制使用较多",
                "您经常抑制情绪的外在表达，长期使用此策略可能影响身心健康，建议适当练习情绪的自然表达。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="情绪调节问卷(ERQ)",
        description="本问卷帮助了解您常用的情绪调节策略。共10题，大约需要3分钟完成。",
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
