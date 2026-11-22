"""P1-12: WDS - Workplace Deviance Scale (Bennett & Robinson, 2000)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "wds-workplace-deviance"
IMPORT_CODE = "huaxinyun-wds-workplace-deviance"

# WDS: 19 items, 7-point frequency (1=never to 7=daily)
# Organizational deviance (items 1-12), Interpersonal deviance (items 13-19)

QUESTIONS = [
    # Organizational Deviance (1-12)
    (1, "上班迟到。"),
    (2, "早退。"),
    (3, "未经许可占用公司物品。"),
    (4, "在工作时间花大量时间做白日梦。"),
    (5, "伪造报销单据或工作记录。"),
    (6, "在工作中故意放慢速度。"),
    (7, "将工作中的错误归咎于他人。"),
    (8, "在工作时间处理私人事务。"),
    (9, "忽视上级的指示。"),
    (10, "在工作中饮酒或使用药物。"),
    (11, "在工作中传播关于同事的流言蜚语。"),
    (12, "故意不努力工作。"),
    # Interpersonal Deviance (13-19)
    (13, "在工作中对同事发表不当评论。"),
    (14, "在工作中对他人做出不雅手势。"),
    (15, "在工作中对他人发表种族歧视或性别歧视言论。"),
    (16, "在工作中咒骂同事。"),
    (17, "在工作中对他人进行恶作剧。"),
    (18, "在工作中公开让他人难堪。"),
    (19, "在工作中对他人进行身体威胁或恐吓。"),
]

FREQUENCY_7_OPTIONS = [
    ("从不", 1), ("每年一次", 2), ("每月一次", 3), ("每月数次", 4),
    ("每周一次", 5), ("每周数次", 6), ("每天", 7)
]

def make_questions():
    return [radio_q(order, text, FREQUENCY_7_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    # Organizational deviance: mean of items 1-12 (12 items)
    org_items = " + ".join(f"hx_t_{i}" for i in range(1, 13))
    org_formula = f"({org_items}) / 12"

    # Interpersonal deviance: mean of items 13-19 (7 items)
    inter_items = " + ".join(f"hx_t_{i}" for i in range(13, 20))
    inter_formula = f"({inter_items}) / 7"

    return [
        dimension("组织偏差行为", "org_deviance", 1, org_formula, "", [
            result_rule("hx_wd_y_1 <= 2.0", "组织偏差行为水平较低", "您在工作场所中的偏差行为频率很低，工作态度积极。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.0", "组织偏差行为水平中等", "您的组织偏差行为处于正常范围，偶尔会出现轻微的偏差行为。", "none"),
            result_rule("hx_wd_y_1 > 3.0 && hx_wd_y_1 <= 4.5", "组织偏差行为水平偏高", "您在组织偏差行为方面得分偏高，建议反思工作态度和行为习惯。", "low"),
            result_rule("hx_wd_y_1 > 4.5", "组织偏差行为水平异常偏高", "您的组织偏差行为频率明显偏高，建议寻求职业咨询帮助改善工作行为。", "middle"),
        ]),
        dimension("人际偏差行为", "inter_deviance", 2, inter_formula, "", [
            result_rule("hx_wd_y_2 <= 1.5", "人际偏差行为水平较低", "您在工作场所中的人际偏差行为频率很低，人际关系良好。", "none"),
            result_rule("hx_wd_y_2 > 1.5 && hx_wd_y_2 <= 2.5", "人际偏差行为水平中等", "您的人际偏差行为处于正常范围。", "none"),
            result_rule("hx_wd_y_2 > 2.5 && hx_wd_y_2 <= 4.0", "人际偏差行为水平偏高", "您在人际偏差行为方面得分偏高，建议关注同事关系和沟通方式。", "low"),
            result_rule("hx_wd_y_2 > 4.0", "人际偏差行为水平异常偏高", "您的人际偏差行为频率明显偏高，建议寻求职业咨询帮助改善人际互动。", "middle"),
        ]),
    ]

def build():
    return build_scale(
        title="职场偏差行为量表(WDS)",
        description="本问卷了解您在工作中可能出现的一些行为倾向，帮助促进更好的职场环境。共19题，大约需要3分钟完成。",
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
