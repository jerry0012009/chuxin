"""P49: 控制源量表(LOC)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "loc-control"
IMPORT_CODE = "huaxinyun-loc-control"

OPTIONS = [
    ("非常不准确", 1), ("比较不准确", 2), ("不确定", 3), ("比较准确", 4), ("非常准确", 5)
]

QUESTIONS_RAW = [
    (1, "我能否得到晋升主要取决于我的能力"),
    (2, "当我制定计划时，我几乎肯定能实现它"),
    (3, "我的成绩完全取决于我的努力程度"),
    (4, "对我来说，坚持自己的理想和目标是可能的"),
    (5, "只要我下定决心，就能影响身边发生的事"),
    (6, "我过着的生活很大程度上是由我自己决定的"),
    (7, "在与人交往时，我通常能掌控局面"),
    (8, "我的命运由自己掌握"),
    (9, "只要足够努力，我就能实现目标"),
    (10, "我在生活中取得的成就完全取决于我的能力"),
    (11, "能否得到我想要的晋升取决于有影响力的人"),
    (12, "我生活中发生的事大多是由有权势的人决定的"),
    (13, "在制定计划时，我需要确保它们不会触怒有权势的人"),
    (14, "为了实现目标，我需要获得有影响力的人的支持"),
    (15, "我的人生道路很大程度上取决于有权势的人"),
    (16, "有影响力的人决定了我能否成功"),
    (17, "要升职加薪，我必须讨好上司"),
    (18, "那些有权力的人掌控着我的生活"),
    (19, "我感到自己无法改变与权威人士的关系"),
    (20, "在社会中，普通人很难影响决策者"),
    (21, "很多事情的发生纯属偶然"),
    (22, "我的人生很大程度上取决于运气"),
    (23, "我常常发现好事会自然而然地发生"),
    (24, "我很难理解为什么有些事情会发生在我身上"),
    (25, "命运对我有很大影响"),
    (26, "运气在决定我的人生方向中起重要作用"),
    (27, "我生活中很多好事都是碰巧发生的"),
    (28, "我觉得很多事情都无法预料和控制"),
    (29, "我经常凭运气做成事情"),
    (30, "机遇决定了我人生中的大部分事情"),
]

def make_questions():
    return [radio_q(order, text, OPTIONS) for order, text in QUESTIONS_RAW]

def make_dimensions():
    return [
        dimension("内控性", "internality", 1, "(hx_t_1 + hx_t_2 + hx_t_3 + hx_t_4 + hx_t_5 + hx_t_6 + hx_t_7 + hx_t_8 + hx_t_9 + hx_t_10) / 10", "", [
            result_rule("hx_wd_y_1 <= 2.0", "低", "您倾向于认为外部因素决定事件结果，较少相信自己能掌控局面。", "none"),
            result_rule("hx_wd_y_1 > 2.0 && hx_wd_y_1 <= 3.5", "中", "您对内外控制源的看法较为平衡。", "none"),
            result_rule("hx_wd_y_1 > 3.5", "高", "您倾向于认为自己的行为和努力能够影响事件结果，具有较强的自主感。", "none"),
        ]),
        dimension("权威他人", "powerful_others", 2, "(hx_t_11 + hx_t_12 + hx_t_13 + hx_t_14 + hx_t_15 + hx_t_16 + hx_t_17 + hx_t_18 + hx_t_19 + hx_t_20) / 10", "", [
            result_rule("hx_wd_y_2 <= 2.0", "低", "您较少认为他人（权威、领导）控制着自己的生活。", "none"),
            result_rule("hx_wd_y_2 > 2.0 && hx_wd_y_2 <= 3.5", "中", "您对权威他人影响力的感知中等。", "none"),
            result_rule("hx_wd_y_2 > 3.5", "高", "您倾向于认为有权势的人掌控着自己的生活方向。", "none"),
        ]),
        dimension("机遇", "chance", 3, "(hx_t_21 + hx_t_22 + hx_t_23 + hx_t_24 + hx_t_25 + hx_t_26 + hx_t_27 + hx_t_28 + hx_t_29 + hx_t_30) / 10", "", [
            result_rule("hx_wd_y_3 <= 2.0", "低", "您较少将生活事件归因于运气或偶然。", "none"),
            result_rule("hx_wd_y_3 > 2.0 && hx_wd_y_3 <= 3.5", "中", "您对机遇因素的看法较为中立。", "none"),
            result_rule("hx_wd_y_3 > 3.5", "高", "您倾向于认为运气和机遇在生活中起重要作用。", "none"),
        ]),
    ]

def build():
    return build_scale(
        title="控制源量表(LOC)",
        description="本问卷帮助了解您对生活中事件归因方式的倾向，是内控还是外控。共30题，大约需要6分钟完成。",
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
