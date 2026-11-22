"""P2-28: CFQ - Cognitive Failures Questionnaire (Broadbent et al., 1982)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from import_helpers import *

SCALE_CODE = "cfq-cognition"
IMPORT_CODE = "huaxinyun-cfq-cognition"

# CFQ: 25 items, 5-point (0=never to 4=very often)
# Single dimension. Sum 0-100. Higher = more cognitive failures.
# Norms: mean ~43 in general population.

QUESTIONS = [
    (1, "你是否曾经忘记自己打算去做的事情？"),
    (2, "你是否曾经在阅读时发现自己注意力不集中？"),
    (3, "你是否曾经一时想不起某人的名字？"),
    (4, "你是否曾经碰倒或撞到东西？"),
    (5, "你是否曾经忘记把东西放在了哪里？"),
    (6, "你是否曾经在别人说话时走神？"),
    (7, "你是否曾经想说某个词却说了另一个词？"),
    (8, "你是否曾经在出门后不确定门是否锁好？"),
    (9, "你是否曾经发现自己手边没有笔或其他小工具？"),
    (10, "你是否曾经在走路时撞到别人？"),
    (11, "你是否曾经在打电话时忘记想说的话？"),
    (12, "你是否曾经忘记安排好的约会？"),
    (13, "你是否曾经在不适当的时候想起某件事？"),
    (14, "你是否曾经忘记别人告诉你的事情？"),
    (15, "你是否曾经发现自己做事时丢三落四？"),
    (16, "你是否曾经在需要集中精力时发现自己在做白日梦？"),
    (17, "你是否曾经把一件东西放在不寻常的地方然后找不到？"),
    (18, "你是否曾经在做事之前忘记自己打算做什么？"),
    (19, "你是否曾经在朋友家或别人家忘记带走东西？"),
    (20, "你是否曾经发现自己说的话词不达意？"),
    (21, "你是否曾经在被人介绍之后很快忘记对方的名字？"),
    (22, "你是否曾经在出门时忘记带重要的东西？"),
    (23, "你是否曾经在别人问你问题时走神？"),
    (24, "你是否曾经在做某件事情时忘记另一件需要做的事？"),
    (25, "你是否曾经因为注意力不集中而错过了公交车或地铁？"),
]

CFQ_OPTIONS = [
    ("从不", 0), ("很少", 1), ("有时", 2), ("经常", 3), ("非常频繁", 4)
]

def make_questions():
    return [radio_q(order, text, CFQ_OPTIONS) for order, text in QUESTIONS]

def make_dimensions():
    total_items = q_range(1, 25)
    return [
        dimension("认知失误", "cfq_total", 1, total_items, "", [
            result_rule("hx_wd_y_1 <= 25", "认知失误水平较低", "您的认知失误问卷总分较低，表明您在日常生活中很少出现注意力不集中、记忆力下降等认知失误。", "none"),
            result_rule("hx_wd_y_1 > 25 && hx_wd_y_1 <= 43", "认知失误水平中等", "您的认知失误问卷总分处于中等范围，偶尔会出现一些认知失误，这在日常生活中属于正常现象。", "none"),
            result_rule("hx_wd_y_1 > 43 && hx_wd_y_1 <= 65", "认知失误水平偏高", "您的认知失误问卷总分高于一般人群常模（约43分），表明您在注意力和记忆方面可能存在一定困难。建议关注睡眠质量和压力管理。", "low"),
            result_rule("hx_wd_y_1 > 65", "认知失误水平显著偏高", "您的认知失误问卷总分明显偏高，表明您在日常生活中频繁出现认知失误。建议寻求专业评估，排查注意力或记忆方面的问题。", "middle"),
        ]),
    ]

def build():
    return build_scale(
        title="认知失误问卷(CFQ)",
        description="本问卷帮助了解您在日常生活中是否容易出现注意力不集中、记忆力下降等情况。共25题，大约需要5分钟完成。",
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
