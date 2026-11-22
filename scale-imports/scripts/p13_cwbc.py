"""P1-13: CWB-C - Counterproductive Work Behavior Checklist (Spector, 2006)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "cwbc-counterproductive-work"
IMPORT_CODE = "huaxinyun-cwbc-counterproductive-work"

# CWB-C: 32 items, 5-point frequency (1=never to 5=every day)
# 2-factor model:
#   CWB-Interpersonal (items 1-20): behaviors targeting people
#   CWB-Organization (items 21-32): behaviors targeting the organization
# Total sum range: 32-160

QUESTIONS = [
    # CWB-Interpersonal (1-20) - targeting people
    (1, "在工作中公开羞辱同事。"),
    (2, "对同事发表伤人或侮辱性的评论。"),
    (3, "在工作中对同事大喊大叫。"),
    (4, "在工作中对同事恶语相向。"),
    (5, "故意制造让同事难堪的尴尬场面。"),
    (6, "对同事发出威胁恐吓。"),
    (7, "在工作中对同事使用粗俗语言或脏话。"),
    (8, "对同事做出不雅或冒犯性的手势。"),
    (9, "对同事散布流言蜚语。"),
    (10, "在工作中与同事发生激烈争吵。"),
    (11, "对同事的工作成果发表贬低性评论。"),
    (12, "故意忽视或排挤同事。"),
    (13, "在工作中对同事进行人身攻击。"),
    (14, "故意阻碍同事完成工作任务。"),
    (15, "在工作中对同事表现出不尊重的态度。"),
    (16, "以粗暴或无礼的方式对待同事。"),
    (17, "在背后说同事坏话。"),
    (18, "对同事进行种族、性别或其他歧视性言行。"),
    (19, "在工作中对同事恶作剧或戏弄同事。"),
    (20, "故意拒绝与某些同事合作。"),
    # CWB-Organization (21-32) - targeting the organization
    (21, "故意放慢工作速度以降低效率。"),
    (22, "故意不按照工作要求工作。"),
    (23, "在工作时间做私人事情。"),
    (24, "故意推迟或拖延工作任务。"),
    (25, "伪造病假条或其他证明文件。"),
    (26, "未经允许早退。"),
    (27, "未经允许迟到。"),
    (28, "在工作中偷懒。"),
    (29, "偷窃公司物品或资源。"),
    (30, "未经授权使用公司设备或车辆。"),
    (31, "故意浪费公司材料或物资。"),
    (32, "故意损坏公司设备或财产。"),
]

FREQUENCY_5_OPTIONS = [
    ("从不", 1), ("一年几次", 2), ("每月几次", 3), ("每周几次", 4), ("每天", 5)
]

def make_questions():
    return [radio_q(order, text, FREQUENCY_5_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    # CWB-Interpersonal: mean of items 1-20
    cwb_i_items = " + ".join(f"hx_t_{i}" for i in range(1, 21))
    cwb_i_formula = f"({cwb_i_items}) / 20"

    # CWB-Organization: mean of items 21-32
    cwb_o_items = " + ".join(f"hx_t_{i}" for i in range(21, 33))
    cwb_o_formula = f"({cwb_o_items}) / 12"

    # Total score: sum of all 32 items
    all_items = " + ".join(f"hx_t_{i}" for i in range(1, 33))
    total_formula = f"({all_items})"

    return [
        dimension("人际反生产行为", "cwb_interpersonal", 1, cwb_i_formula, "", [
            result_rule("hx_wd_y_1 <= 1.5", "人际反生产行为水平极低", "您几乎没有针对同事的反生产行为，人际关系行为良好。", "none"),
            result_rule("hx_wd_y_1 > 1.5 && hx_wd_y_1 <= 2.0", "人际反生产行为水平较低", "您针对同事的反生产行为频率较低。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.0", "人际反生产行为水平中等", "您偶尔会出现针对同事的反生产行为，建议注意职场人际互动方式。", "low"),
            result_rule("hx_wd_y_1 > 3.0", "人际反生产行为水平偏高", "您针对同事的反生产行为频率较高，建议反思职场人际行为并寻求改善。", "middle"),
        ]),
        dimension("组织反生产行为", "cwb_organization", 2, cwb_o_formula, "", [
            result_rule("hx_wd_y_2 <= 1.5", "组织反生产行为水平极低", "您几乎没有针对组织的反生产行为，工作态度积极。", "none"),
            result_rule("hx_wd_y_2 > 1.5 && hx_wd_y_2 <= 2.0", "组织反生产行为水平较低", "您针对组织的反生产行为频率较低。", "none"),
            result_rule("hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.0", "组织反生产行为水平中等", "您偶尔会出现针对组织的反生产行为，建议关注工作纪律和职业规范。", "low"),
            result_rule("hx_wd_y_2 > 3.0", "组织反生产行为水平偏高", "您针对组织的反生产行为频率较高，建议反思工作态度并寻求职业咨询。", "middle"),
        ]),
        dimension("反生产行为总分", "cwb_total", 3, total_formula, "", [
            result_rule("hx_wd_y_3 <= 48", "反生产行为总分很低", "您的反生产行为总体水平很低，工作行为规范。", "none"),
            result_rule("hx_wd_y_3 > 48 && hx_wd_y_3 <= 64", "反生产行为总分较低", "您的反生产行为总体水平较低。", "none"),
            result_rule("hx_wd_y_3 > 64 && hx_wd_y_3 <= 96", "反生产行为总分中等", "您的反生产行为处于中等水平，建议注意减少工作场所中的不当行为。", "low"),
            result_rule("hx_wd_y_3 > 96", "反生产行为总分偏高", "您的反生产行为总分偏高，建议寻求专业帮助以改善工作行为。", "middle"),
        ]),
    ]

def build():
    return build_scale(
        title="反生产行为检查表(CWB-C)",
        description="本问卷了解您在工作中可能出现的一些行为，帮助促进更和谐的工作关系。共45题，大约需要8分钟完成。",
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
