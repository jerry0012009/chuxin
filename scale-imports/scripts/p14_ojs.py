"""P1-14: Colquitt Organizational Justice Scale (Colquitt, 2001)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "ojs-organizational-justice"
IMPORT_CODE = "huaxinyun-ojs-organizational-justice"

# Colquitt OJS: 20 items, 5-point (1=to a small extent to 5=to a large extent)
# 4 dimensions:
#   Distributive Justice (1-4)
#   Procedural Justice (5-11)
#   Interpersonal Justice (12-15)
#   Informational Justice (16-20)

QUESTIONS = [
    # Distributive Justice (1-4)
    (1, "您的工作结果是否反映了您付出的努力？"),
    (2, "您的工作结果是否与您的工作职责相称？"),
    (3, "您的工作结果是否反映了您对工作的贡献？"),
    (4, "您的工作结果是否对于您的工作表现来说是合理的？"),
    # Procedural Justice (5-11)
    (5, "您能否对上级的决策程序发表自己的意见？"),
    (6, "您能否在决策程序中表达自己的意见和看法？"),
    (7, "决策程序是否基于准确的信息？"),
    (8, "决策程序是否允许提出申诉或质疑？"),
    (9, "决策程序是否遵循道德和伦理标准？"),
    (10, "决策程序对所有员工是否一视同仁？"),
    (11, "决策程序是否考虑到各方的利益和关切？"),
    # Interpersonal Justice (12-15)
    (12, "上级在决策过程中是否对您表现出尊重？"),
    (13, "上级在决策过程中是否维护了您的尊严？"),
    (14, "上级在决策过程中是否对您表现出礼貌？"),
    (15, "上级在决策过程中是否避免了不恰当的言论或行为？"),
    # Informational Justice (16-20)
    (16, "上级是否详细解释了决策的理由？"),
    (17, "上级的解释是否合理？"),
    (18, "上级是否坦诚地与您沟通？"),
    (19, "上级是否及时向您传达了相关信息？"),
    (20, "上级的解释是否有助于您理解决策过程？"),
]

JUSTICE_5_OPTIONS = [
    ("在极小程度上", 1), ("在较小程度上", 2), ("在中等程度上", 3),
    ("在较大程度上", 4), ("在极大程度上", 5)
]

def make_questions():
    return [radio_q(order, text, JUSTICE_5_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    # Distributive Justice: mean of items 1-4
    dj_items = " + ".join(f"hx_t_{i}" for i in range(1, 5))
    dj_formula = f"({dj_items}) / 4"

    # Procedural Justice: mean of items 5-11
    pj_items = " + ".join(f"hx_t_{i}" for i in range(5, 12))
    pj_formula = f"({pj_items}) / 7"

    # Interpersonal Justice: mean of items 12-15
    ij_items = " + ".join(f"hx_t_{i}" for i in range(12, 16))
    ij_formula = f"({ij_items}) / 4"

    # Informational Justice: mean of items 16-20
    infoj_items = " + ".join(f"hx_t_{i}" for i in range(16, 21))
    infoj_formula = f"({infoj_items}) / 5"

    return [
        dimension("分配公正", "distributive_justice", 1, dj_formula, "", [
            result_rule("hx_wd_y_1 <= 2.0", "分配公正水平较低", "您认为工作分配结果不够公平，建议与上级沟通期望和需求。", "low"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.0", "分配公正水平中等", "您对工作分配结果的公平感处于中等水平。", "none"),
            result_rule("hx_wd_y_1 > 3.0 && hx_wd_y_1 <= 4.0", "分配公正水平较高", "您认为工作分配结果较为公平。", "none"),
            result_rule("hx_wd_y_1 > 4.0", "分配公正水平很高", "您对工作分配结果有很高的公平感。", "none"),
        ]),
        dimension("程序公正", "procedural_justice", 2, pj_formula, "", [
            result_rule("hx_wd_y_2 <= 2.0", "程序公正水平较低", "您认为组织决策程序不够公平透明，建议向上级反映改善建议。", "low"),
            result_rule("hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.0", "程序公正水平中等", "您对组织决策程序的公平感处于中等水平。", "none"),
            result_rule("hx_wd_y_2 > 3.0 && hx_wd_y_2 <= 4.0", "程序公正水平较高", "您认为组织决策程序较为公平合理。", "none"),
            result_rule("hx_wd_y_2 > 4.0", "程序公正水平很高", "您对组织决策程序有很高的公平感。", "none"),
        ]),
        dimension("人际公正", "interpersonal_justice", 3, ij_formula, "", [
            result_rule("hx_wd_y_3 <= 2.0", "人际公正水平较低", "您在工作中感受到的人际尊重不足，建议与上级或HR沟通。", "low"),
            result_rule("hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.0", "人际公正水平中等", "您在工作中感受到的人际尊重处于中等水平。", "none"),
            result_rule("hx_wd_y_3 > 3.0 && hx_wd_y_3 <= 4.0", "人际公正水平较高", "您在工作中感受到较高的人际尊重。", "none"),
            result_rule("hx_wd_y_3 > 4.0", "人际公正水平很高", "您在工作中感受到很高的人际尊重。", "none"),
        ]),
        dimension("信息公正", "informational_justice", 4, infoj_formula, "", [
            result_rule("hx_wd_y_4 <= 2.0", "信息公正水平较低", "您认为组织的信息沟通不够充分透明，建议向上级反映沟通需求。", "low"),
            result_rule("hx_wd_y_4 > 2.0 && hx_wd_y_4 <= 3.0", "信息公正水平中等", "您对组织信息沟通的满意度处于中等水平。", "none"),
            result_rule("hx_wd_y_4 > 3.0 && hx_wd_y_4 <= 4.0", "信息公正水平较高", "您认为组织的信息沟通较为充分。", "none"),
            result_rule("hx_wd_y_4 > 4.0", "信息公正水平很高", "您对组织的信息沟通有很高的满意度。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="组织公正量表(OJS)",
        description="本问卷帮助了解您对工作环境中公平性的感受，包括资源分配、决策过程等方面。共20题，大约需要4分钟完成。",
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
