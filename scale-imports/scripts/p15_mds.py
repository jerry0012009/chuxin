"""P1-15: MDS - Moral Disengagement Scale (Bandura, 1996)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "mds-moral-disengagement"
IMPORT_CODE = "huaxinyun-mds-moral-disengagement"

# MDS: 32 items, 3-point (1=disagree, 2=neutral, 3=agree)
# Single dimension: total mean score (range 1-3)
# Thresholds: <1.5 low, 1.5-2.0 moderate, >2.0 high

QUESTIONS = [
    (1, "为了保护你关心的人，做一些不太好的事情是可以接受的。"),
    (2, "有时候为了保护自己，伤害别人是必要的。"),
    (3, "如果一个团队一致决定做某件事，那么就不应该责怪其中的个别成员。"),
    (4, "如果孩子在学校受到不好的对待，那么他们在家里的不良行为是可以理解的。"),
    (5, "如果人们不关心自己，那么他们的不良行为是他们自己的错。"),
    (6, "有些人做了坏事是因为他们受到了不良影响。"),
    (7, "在某些情况下，为了维护团队的荣誉，违反规则是可以接受的。"),
    (8, "有时候打人或推搡他人是可以接受的。"),
    (9, "如果一个人做了违法的事情但没有被抓住，那就不算真正的犯错。"),
    (10, "有些人天生就比较暴力。"),
    (11, "如果老师没有管理好课堂，学生不遵守纪律就不能全怪学生。"),
    (12, "偷窃富人的东西比偷窃穷人的东西危害更小。"),
    (13, "为了保护朋友而撒谎是可以接受的。"),
    (14, "在某些情况下，使用暴力是维护尊严的唯一方式。"),
    (15, "如果一个人所做的只是跟随命令，那他不应该为后果负责。"),
    (16, "有时候，为了达到重要的目标，不得不做一些不好的事情。"),
    (17, "如果团队中的每个人都做了违规的事情，那就不算真正违规。"),
    (18, "对待犯了错的人，可以不那么讲礼貌。"),
    (19, "如果受害者自己也有过错，那么加害者的行为就更可以理解。"),
    (20, "有些人的行为恶劣是因为他们生长在不好的环境中。"),
    (21, "如果一个人是被迫做坏事的，那他就不能被完全责怪。"),
    (22, "有时候为了完成任务，不得不忽略某些规则。"),
    (23, "在工作中，如果不违规就无法完成任务，那么违规是可以接受的。"),
    (24, "如果一个群体做出了决定，那么其中的个人就不需要为后果承担全部责任。"),
    (25, "有些人做了坏事是因为他们不知道这样做的后果。"),
    (26, "对待那些与我们不同的人，可以不太在意他们的感受。"),
    (27, "如果一个人没有直接参与做坏事，只是旁观，那他就不需要负责。"),
    (28, "有时候，为了让别人服从，使用威胁手段是可以接受的。"),
    (29, "如果大家都在做某件事，那它就不算错。"),
    (30, "为了帮助家人而做错事，是可以被原谅的。"),
    (31, "如果一个人没有意识到自己在做坏事，那么他的道德责任就应该减轻。"),
    (32, "对某些人来说，一些小的错误行为不算什么大事。"),
]

MDS_3_OPTIONS = [
    ("不同意", 1), ("中立", 2), ("同意", 3)
]

def make_questions():
    return [radio_q(order, text, MDS_3_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    # Total score: mean of all 32 items
    all_items = " + ".join(f"hx_t_{i}" for i in range(1, 33))
    total_formula = f"({all_items}) / 32"

    return [
        dimension("道德推脱", "moral_disengagement", 1, total_formula, "", [
            result_rule("hx_wd_y_1 < 1.5", "道德推脱水平较低", "您的道德推脱水平较低，表明您具有较强的道德自律能力，较少为不道德行为寻找借口。", "none"),
            result_rule("hx_wd_y_1 >= 1.5 && hx_wd_y_1 <= 2.0", "道德推脱水平中等", "您的道德推脱水平处于中等范围，在某些情境下可能会出现道德推理上的偏差，建议加强道德意识。", "low"),
            result_rule("hx_wd_y_1 > 2.0", "道德推脱水平较高", "您的道德推脱水平较高，表明您倾向于为不道德行为寻找合理化理由，建议反思自身的道德判断标准。", "middle"),
        ]),
    ]

def build():
    return build_scale(
        title="道德推脱量表(MDS)",
        description="本问卷帮助了解您在面对道德选择时的思维方式和倾向。共32题，大约需要6分钟完成。",
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
