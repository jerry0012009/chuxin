"""P2-27: WebEXEC - Web-based Executive Function Test (Buchanan et al., 2010)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "webexec-executive"
IMPORT_CODE = "huaxinyun-webexec-executive"

# WebEXEC: 25 items, 4-point (1=strongly disagree to 4=strongly agree)
# All items negative (about cognitive/executive failures in daily life)
# No reverse items. Sum 25-100. Higher = more executive dysfunction.

QUESTIONS = [
    (1, "我很难同时处理多项任务。"),
    (2, "我在组织日常活动时经常遇到困难。"),
    (3, "我在需要集中注意力时很容易分心。"),
    (4, "我经常忘记别人刚刚告诉我的事情。"),
    (5, "我在做计划时经常遗漏重要细节。"),
    (6, "我在切换不同任务时感到困难。"),
    (7, "我在控制冲动行为方面有困难。"),
    (8, "我在解决问题时很难保持思路清晰。"),
    (9, "我在需要灵活应变时感到吃力。"),
    (10, "我在完成需要多步骤的工作时经常出错。"),
    (11, "我在管理时间方面存在困难。"),
    (12, "我经常丢失或放错物品。"),
    (13, "我在需要抑制不当反应时有困难。"),
    (14, "我在执行复杂指令时经常犯错。"),
    (15, "我很难在嘈杂或干扰的环境中工作。"),
    (16, "我在需要持续关注的任务上表现不佳。"),
    (17, "我经常忘记预约或承诺。"),
    (18, "我在估算时间方面存在困难。"),
    (19, "我在做出决定前很难全面考虑各种选项。"),
    (20, "我在需要自我监控时经常出现问题。"),
    (21, "我在开始新任务时经常拖延。"),
    (22, "我在理解复杂说明时存在困难。"),
    (23, "我很难在工作记忆中保持信息。"),
    (24, "我在需要同时关注多条信息时感到困难。"),
    (25, "我在完成任务的过程中很难保持动力。"),
]

WEBEXEC_OPTIONS = [
    ("非常不同意", 1), ("不同意", 2), ("同意", 3), ("非常同意", 4)
]

def make_questions():
    return [radio_q(order, text, WEBEXEC_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    total_items = q_range(1, 25)
    return [
        dimension("执行功能障碍", "webexec_total", 1, total_items, "", [
            result_rule("hx_wd_y_1 <= 40", "执行功能良好", "您的WebEXEC总分较低，表明您在日常生活中执行功能表现良好，组织、计划和多任务处理能力较强。", "none"),
            result_rule("hx_wd_y_1 > 40 && hx_wd_y_1 <= 55", "执行功能轻度困难", "您的WebEXEC总分处于中等范围，表明您在日常执行功能方面存在一些轻度困难，但不影响正常生活。", "none"),
            result_rule("hx_wd_y_1 > 55 && hx_wd_y_1 <= 75", "执行功能中度困难", "您的WebEXEC总分偏高，表明您在组织、计划、任务切换等执行功能方面存在中度困难，建议关注并采取相应策略。", "low"),
            result_rule("hx_wd_y_1 > 75", "执行功能显著困难", "您的WebEXEC总分明显偏高，表明您在日常执行功能方面存在显著困难，建议寻求专业评估和帮助。", "middle"),
        ]),
    ]

def build():
    return build_scale(
        title="网络执行功能量表(WebEXEC)",
        description="本问卷帮助了解您在日常生活中注意力、计划和决策等方面的功能状态。共25题，大约需要5分钟完成。",
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
